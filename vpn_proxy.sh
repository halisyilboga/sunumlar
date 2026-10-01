#!/usr/bin/env bash
# =============================================================================
# vpn_proxy.sh — TEK SCRIPT: VPN + uyku önleme + SSH proxy tüneli yönetimi
#
#   VPN (Tunnelblick / Tailscale / FortiClient / BlancVPN) AÇIK olduğunda
#   seçili proxy'leri otomatik kurar, VPN kapanınca beklemeye alır.
#
# Kullanım:
#   ./vpn_proxy.sh            -> ilk kurulum sihirbazı / bağlan (interaktif)
#   ./vpn_proxy.sh start      -> seçili proxy'leri başlat + arka plan daemon
#   ./vpn_proxy.sh stop       -> daemon + tüm tünelleri kapat
#   ./vpn_proxy.sh status     -> VPN + proxy durumu
#   ./vpn_proxy.sh setup      -> proxy seçimi / retry ayarı (yeniden yapılandır)
#   ./vpn_proxy.sh watch      -> canlı log
#
# POP-UP YOK: daemon asla parola sormaz, asla diyalog göstermez.
# Parola ~/.config/sunumlar/secrets.env içinde bir kez sorulup saklanır (600).
# =============================================================================
set -uo pipefail

# -----------------------------------------------
# Ayarlar
# -----------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_JS="$SCRIPT_DIR/sync_proxy_models.js"

CONFIG_DIR="$HOME/.config/sunumlar"
SECRETS_FILE="$CONFIG_DIR/secrets.env"
STATE_DIR="$CONFIG_DIR/proxy"
CONF_FILE="$CONFIG_DIR/vpn_proxy.conf"
HOSTS_FILE="$CONFIG_DIR/hosts.env"
LOG_FILE="$STATE_DIR/manager.log"
PID_FILE="$STATE_DIR/manager.pid"

# -----------------------------------------------
# HEDEF MAKİNE (IP) LİSTESİ
#
# VPN DHCP kiraları sık değiştiği için IP'yi koda gömüyoruz. Listeyi
# ~/.config/sunumlar/hosts.env dosyasında tutuyoruz; dosyaya yeni IP
# eklemek için sonuna bir satır more:
#
#   1  10.1.37.223  ubuntu-ana (varsayılan)
#   2  10.1.37.224  ubuntu-yedek
#
# Numarayla seçmek için:  ./vpn_proxy.sh 2
# Tek seferlik geçersiz kılmak için:  PROXY_HOST=10.1.37.224 ./vpn_proxy.sh start
#
# ÖNCELİK (yüksekten düşüğe):
#   1. PROXY_HOST ortam değişkeni      (tek seferlik)
#   2. ./vpn_proxy.sh <numara>         (seçimi kalıcı kaydeder)
#   3. hosts.env'deki kayıtlı seçim
#   4. hosts.env'deki 1. satır
#   5. DEFAULT_PROXY_HOST (aşağıdaki sabit)
# Hiçbiri yoksa mevcut değer kullanılır.
# -----------------------------------------------
DEFAULT_PROXY_HOST="10.1.37.223"
PROXY_USER="${PROXY_USER:-halis}"
PROXY_SSH_PORT="${PROXY_SSH_PORT:-22}"

# Ortam değişkeniyle gelen PROXY_HOST'u AŞAĞIDA ezilmeden önce yakala.
# Boşsa hiç kimse geçersiz kılmamış demektir.
PROXY_HOST_OVERRIDE="${PROXY_HOST:-}"
PROXY_HOST="$DEFAULT_PROXY_HOST"

# Yeniden deneme aralığı: 10s ile başlar, katlanarak büyür, 240s (4 dk) tavan.
WARM_INTERVAL="${WARM_INTERVAL:-10}"
MAX_INTERVAL="${MAX_INTERVAL:-240}"
API_TIMEOUT="${API_TIMEOUT:-8}"

# isim:port:uzak-port
ALL_PROXIES=(
  "opencode:6446:6446"
  "cline:6447:6447"
  "kilo:5380:5380"
  "antigravity:4000:4000"
)

mkdir -p "$STATE_DIR" 2>/dev/null && chmod 700 "$STATE_DIR" 2>/dev/null
: > /dev/null

ts() { date '+%F %T'; }
log() { printf '[%s] %s\n' "$(ts)" "$1" >>"$LOG_FILE" 2>/dev/null; }
say() { printf '%s\n' "$1"; }

# macOS'ta `timeout` yok — yerine kendi deadline'ımız.
deadline() {
  local secs="${1:-30}"; shift
  "$@" & local pid=$! i=0
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$i" -ge $((secs * 4)) ]; then
      { kill -TERM "$pid" 2>/dev/null; } 2>/dev/null
      sleep 1; kill -9 "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
      return 124
    fi
    sleep 0.25; i=$((i + 1))
  done
  wait "$pid"
}

# -----------------------------------------------
# Sırlar (parola)
# -----------------------------------------------
load_secrets() { [ -f "$SECRETS_FILE" ] && . "$SECRETS_FILE"; }

# Parolayı TEK noktadan yükle. open_tunnel her çağrıldığında güncel
# olmalı; yoksa BatchMode'ya düşüp "Permission denied" verir.
ensure_password_loaded() { ssh_password >/dev/null 2>&1 || load_secrets; }

ssh_password() {
  [ -n "${SSH_PASSWORD:-}" ] && { printf '%s' "$SSH_PASSWORD"; return 0; }
  [ -n "${UBUNTU_SSH_PASSWORD:-}" ] && { printf '%s' "$UBUNTU_SSH_PASSWORD"; return 0; }
  return 1
}

save_password() {
  local pw="${1:-}" q
  [ -n "$pw" ] || return 1
  mkdir -p "$CONFIG_DIR"; chmod 700 "$CONFIG_DIR"
  touch "$SECRETS_FILE"; chmod 600 "$SECRETS_FILE"
  q=$(printf '%s' "$pw" | sed "s/'/'\\\\''/g")
  if grep -q '^UBUNTU_SSH_PASSWORD=' "$SECRETS_FILE" 2>/dev/null; then
    /usr/bin/sed -i '' "s|^UBUNTU_SSH_PASSWORD=.*|UBUNTU_SSH_PASSWORD='$q'|" "$SECRETS_FILE"
  else
    printf "UBUNTU_SSH_PASSWORD='%s'\n" "$q" >> "$SECRETS_FILE"
  fi
  chmod 600 "$SECRETS_FILE"
}

# -----------------------------------------------
# VPN algılama (vpn_caffeinate_manager.sh mantığı)
# -----------------------------------------------
SNAP=""
refresh_snapshot() {
  SNAP=$(ifconfig -a 2>/dev/null | awk '
    /^[a-z0-9]+:/ { i=$1; sub(/:$/,"",i) }
    /inet / && i ~ /^utun/ { print i, $2 }
  ')
}
# tailscale: 100.64.0.0/10 beklenir; openvpn: 100.x HARİÇ adres
vpn_tunnel_ip() {
  local mode="${1:-openvpn}" iface ip
  while read -r iface ip; do
    [ -z "$ip" ] && continue
    if [ "$mode" = "tailscale" ]; then
      case "$ip" in 100.*) echo "$iface $ip"; return 0 ;; esac
    else
      case "$ip" in 100.*) ;; *) echo "$iface $ip"; return 0 ;; esac
    fi
  done <<< "$SNAP"
  return 1
}
is_tunnelblick() {
  pgrep -x openvpn >/dev/null 2>&1 || return 1
  vpn_tunnel_ip openvpn >/dev/null 2>&1
}
is_tailscale() {
  scutil --nc status Tailscale 2>/dev/null | grep -qx Connected || return 1
  vpn_tunnel_ip tailscale >/dev/null 2>&1
}
is_forti() {
  scutil --nc status VPN 2>/dev/null | grep -qx Connected || return 1
  vpn_tunnel_ip openvpn >/dev/null 2>&1
}
is_blanc() {
  scutil --nc status BlancVPN 2>/dev/null | grep -qx Connected || return 1
  vpn_tunnel_ip openvpn >/dev/null 2>&1
}

vpn_state() {
  local s="kapalı"
  is_tunnelblick && s="Tunnelblick"
  is_tailscale  && s="$s+Tailscale"
  is_forti      && s="$s+FortiClient"
  is_blanc      && s="$s+BlancVPN"
  printf '%s' "$s"
}
vpn_up() {
  # SNAP bayatlamış olabilir (script uzun süre açık kalmışsa); tazele.
  [ -n "$SNAP" ] || refresh_snapshot
  [ "$(vpn_state)" != "kapalı" ]
}
# VPN arayüzü açık OLMAK ZORUNDA; hedef makineye erişim de ayrıca doğrulanır.
host_reachable() { nc -z -G 3 "$PROXY_HOST" "$PROXY_SSH_PORT" >/dev/null 2>&1; }
can_connect() { vpn_up && host_reachable; }

# -----------------------------------------------
# Caffeinate — VPN bağlıyken uykuya girmeyi engeller
# -----------------------------------------------
CAFF_PID=""
start_caffeinate() {
  [ -n "$CAFF_PID" ] && kill -0 "$CAFF_PID" 2>/dev/null && return 0
  caffeinate -i -t 3600 >/dev/null 2>&1 &
  CAFF_PID=$!
  log "☕ caffeinate başlatıldı (pid $CAFF_PID)"
}
stop_caffeinate() {
  if [ -n "$CAFF_PID" ] && kill -0 "$CAFF_PID" 2>/dev/null; then
    kill "$CAFF_PID" 2>/dev/null
    log "☕ caffeinate durduruldu"
  fi
  CAFF_PID=""
}

# -----------------------------------------------
# Port / API
# -----------------------------------------------
api_ok() {
  local out
  out=$(curl -s --max-time "$API_TIMEOUT" "http://localhost:$1/v1/models" 2>/dev/null)
  case "$out" in *'"data"'*) return 0 ;; *) return 1 ;; esac
}
port_busy() { [ -n "$(lsof -ti ":$1" -sTCP:LISTEN 2>/dev/null || true)" ]; }

# Port dinliyor ama API cevap vermiyorsa = ASILI TUNNEL. Sadece ssh'i öldür.
free_port() {
  local port="${1:-}" out line pid="" cmd stuck
  out=$(lsof -nP -i ":$port" -sTCP:LISTEN -Fpc 2>/dev/null || true)
  [ -z "$out" ] && return 0
  while IFS= read -r line; do
    case "$line" in
      p*) pid="${line#p}" ;;
      c*) cmd="${line#c}"
          if [ "$cmd" = "ssh" ]; then kill "$pid" 2>/dev/null
          else log "⚠️  Port $port '${cmd}' (pid $pid) ssh değil — dokunulmuyor."; return 1; fi ;;
    esac
  done <<< "$out"
  sleep 1
  stuck=$(lsof -ti ":$port" -sTCP:LISTEN 2>/dev/null || true)
  [ -n "$stuck" ] && kill -9 $stuck 2>/dev/null
  sleep 0.5
}

# SSH seçenekleri — asılı portun KÖK NEDENİ çözümü:
#   ServerAlive*: VPN düşünce ssh canlı kalmaz, portu serbest bırakır
#   ExitOnForwardFailure: port bağlanamazsa ssh ölü modda kalmaz
SSH_OPTS=(
  -o StrictHostKeyChecking=accept-new
  -o ConnectTimeout=10
  -o ServerAliveInterval=15
  -o ServerAliveCountMax=3
  -o ExitOnForwardFailure=yes
  -o TCPKeepAlive=yes
  -p "$PROXY_SSH_PORT"
)

open_tunnel() {
  local port="${1:-}" remote="${2:-}" lg="$STATE_DIR/ssh-$port.log"
  ensure_password_loaded
  local pw; pw=$(ssh_password) || pw=""
  if [ -n "$pw" ]; then
    local pf="$STATE_DIR/.pw" af="$STATE_DIR/askpass.sh"
    printf '%s' "$pw" > "$pf"; chmod 600 "$pf"
    printf '#!/bin/sh\nexec cat %s\n' "$pf" > "$af"; chmod 700 "$af"
    SSH_ASKPASS="$af" SSH_ASKPASS_REQUIRE=force \
      ssh "${SSH_OPTS[@]}" -N -L "$port:localhost:$remote" "$PROXY_USER@$PROXY_HOST" >>"$lg" 2>&1 &
  else
    # Parola yoksa: yalnızca anahtar denenir. Daemon'da TTY yok, soru sorulmaz.
    rm -f "$STATE_DIR/.pw" "$STATE_DIR/askpass.sh"
    ssh "${SSH_OPTS[@]}" -o BatchMode=yes -N -L "$port:localhost:$remote" "$PROXY_USER@$PROXY_HOST" >>"$lg" 2>&1 &
  fi
  local pid=$!
  sleep 1
  kill -0 "$pid" 2>/dev/null || return 1
  printf '%s' "$pid"
}

wait_api() {
  local port="${1:-}" i
  for i in 1 2 3 4; do api_ok "$port" && return 0; sleep 1.5; done
  return 1
}

# ensure_tunnel <port> <remote>
ensure_tunnel() {
  local port="${1:-}" remote="${2:-}" pid
  api_ok "$port" && return 0
  port_busy "$port" && { log "port $port asılı, temizleniyor"; free_port "$port"; }
  can_connect || { log "VPN/host hazır değil, atlanıyor"; return 1; }
  pid=$(open_tunnel "$port" "$remote") || { log "tunnel açılamadı (port $port)"; return 1; }
  if wait_api "$port"; then log "✅ port $port bağlandı (pid $pid)"; return 0; fi
  log "port $port cevap vermedi, kapatılıyor"; kill "$pid" 2>/dev/null; free_port "$port"
  return 1
}

# -----------------------------------------------
# Yapılandırma (hangi proxy'ler, retry)
# -----------------------------------------------
load_conf() {
  SELECTED=""; RETRY="true"; HOST=""
  [ -f "$CONF_FILE" ] && . "$CONF_FILE"
  return 0
}
# Source edildiğinde de ayarlar hazır olsun.
load_conf 2>/dev/null || true
save_conf() {
  mkdir -p "$CONFIG_DIR"; chmod 700 "$CONFIG_DIR"
  { printf '# vpn_proxy.sh ayarları\n'
    printf 'SELECTED="%s"\n' "$SELECTED"
    printf 'RETRY="%s"\n' "$RETRY"
    printf 'HOST="%s"\n' "${HOST:-}"
  } > "$CONF_FILE"
  chmod 600 "$CONF_FILE"
}

# -----------------------------------------------
# HEDEF MAKİNE LİSTESİ
# -----------------------------------------------

# hosts.env yoksa varsayılanı YAZ (kullanıcı sonradan üstüne ekleyebilsin).
ensure_hosts_file() {
  [ -f "$HOSTS_FILE" ] && return 0
  mkdir -p "$CONFIG_DIR"; chmod 700 "$CONFIG_DIR"
  {
    printf '# vpn_proxy.sh — VPN hedef makine listesi\n'
    printf '#\n'
    printf '# Biçim:   <no>  <ip>  <açıklama>\n'
    printf '# Yeni IP eklemek için: bu dosyayı aç, EN SONA yeni satır yaz.\n'
    printf '# Silmek için: satırı sil. Düzenlemek için: açıklamayı değiştir.\n'
    printf '#\n'
    printf '# Kullanım:\n'
    printf '#   ./vpn_proxy.sh 2              → 2. satırdaki makineyi seç ve BAĞLAN\n'
    printf '#   ./vpn_proxy.sh hosts         → listeyi göster\n'
    printf '#   PROXY_HOST=10.1.37.224 ./vpn_proxy.sh start   → tek seferlik geçersiz kıl\n'
    printf '#\n'
    printf '# VPN DHCP kiraları sık değiştiği için birden fazla IP tutuyoruz.\n'
    printf '# 1 numaralı satır DEĞİŞTİRİLMEZ; sıralama numaraya göre.\n'
    printf '\n'
    printf '1  %s  ubuntu-ana (varsayılan)\n' "$DEFAULT_PROXY_HOST"
  } > "$HOSTS_FILE"
  chmod 600 "$HOSTS_FILE"
}

# Listeyi oku: HOST_IPS[] ve HOST_NOTES[] dizilerine doldurur.
# Yorum satırlarını (#) ve boş satırları atlar.
load_hosts() {
  HOST_IPS=(); HOST_NOTES=()
  ensure_hosts_file
  [ -f "$HOSTS_FILE" ] || return 1
  local n ip note
  while read -r n ip note _rest; do
    case "$n" in ''|\#*) continue ;; esac
    case "$ip" in ''|*[!0-9.]*) continue ;; esac   # geçerli IPv4 gibi görünmeyenleri atla
    HOST_IPS+=("$ip")
    HOST_NOTES+=("$note")
  done < "$HOSTS_FILE"
  [ "${#HOST_IPS[@]}" -gt 0 ]
}

# Listeyi ekrana bas; aktif olanı işaretle.
show_hosts() {
  load_hosts || { say "❌ $HOSTS_FILE okunamadı."; return 1; }
  say ""
  say "── Hedef makineler ──"
  say "  $HOSTS_FILE"
  say "  ─────────────────────────────────────────"
  local i
  for i in "${!HOST_IPS[@]}"; do
    local n=$((i + 1)) mark="  " st
    [ "$n" = "${HOST_INDEX:-0}" ] && mark="→ "
    st=$(probe_host "${HOST_IPS[$i]}")
    printf '%s %d) %-15s %-28s %s\n' "$mark" "$n" "${HOST_IPS[$i]}" "${HOST_NOTES[$i]}" "$st"
  done
  say ""
  say "  Seçmek için:  ./vpn_proxy.sh <no>      örn. ./vpn_proxy.sh 2"
  say "  Yeni IP eklemek için: $HOSTS_FILE dosyasının SONUNA satır ekle"
  say ""
}

# Aktif hedefin listedeki açıklamasını döndür (yoksa "özel ayar").
host_note() {
  load_hosts 2>/dev/null || { printf 'özel ayar'; return; }
  local i
  for i in "${!HOST_IPS[@]}"; do
    if [ "${HOST_IPS[$i]}" = "$PROXY_HOST" ]; then
      printf '%s' "${HOST_NOTES[$i]}"; return
    fi
  done
  # Listede yok. Ama varsayılan IP ise "özel ayar" demek yanıltıcı olur.
  [ "$PROXY_HOST" = "$DEFAULT_PROXY_HOST" ] && printf 'varsayılan (liste dışı)' || printf 'özel ayar'
}

# Bir IP'nin erişilebilirliğini tek satırda özetle.
probe_host() {
  local ip="${1:-}" t0 t1
  t0=$(date +%s)
  if nc -z -G 2 "$ip" "$PROXY_SSH_PORT" >/dev/null 2>&1; then
    t1=$(date +%s)
    printf '🟢 erişilebilir (%ss)' "$((t1 - t0))"
  else
    printf '🔴 erişilemiyor'
  fi
}

# Numarayla makine seç; seçimi kalıcı kaydet. ./vpn_proxy.sh 2
select_host_by_index() {
  local idx="${1:-}" i
  case "$idx" in ''|*[!0-9]*) say "❌ Geçersiz numara: '$idx'"; return 1 ;; esac
  load_hosts || { say "❌ Hedef listesi okunamadı: $HOSTS_FILE"; return 1; }
  if [ "$idx" -lt 1 ] || [ "$idx" -gt "${#HOST_IPS[@]}" ]; then
    say "❌ '$idx' yok. 1-${#HOST_IPS[@]} arası bir numara ver, ya da '$HOSTS_FILE' dosyasına ekle."
    return 1
  fi
  i=$((idx - 1))
  # ÖNCE ayarları oku, SONRA seçimi yaz — load_conf HOST'u sıfırlar.
  load_conf
  HOST_INDEX="$idx"
  HOST="${HOST_IPS[$i]}"
  PROXY_HOST="$HOST"
  # Kalıcı kaydet: sonraki çalıştırmalarda da bu makine kullanılsın.
  save_conf
  say "✅ Hedef seçildi: ${HOST_IPS[$i]}  (${HOST_NOTES[$i]})"
  [ "$idx" = "1" ] || say "   Kalıcı kaydedildi — sonraki çalıştırmalarda da bu kullanılacak."
  return 0
}

# PROXY_HOST'u tüm öncelik kurallarına göre belirler.
resolve_host() {
  # 1) Ortam değişkeni açıkça verilmişse odur (tek seferlik geçersiz kılma).
  if [ -n "${PROXY_HOST_OVERRIDE:-}" ]; then
    PROXY_HOST="$PROXY_HOST_OVERRIDE"; return 0
  fi
  # 2) Ayarlarda kayıtlı seçim.
  if [ -n "${HOST:-}" ]; then PROXY_HOST="$HOST"; return 0; fi
  # 3) hosts.env'deki 1. satır, 4) yoksa sabit.
  if load_hosts 2>/dev/null; then PROXY_HOST="${HOST_IPS[0]}"; return 0; fi
  PROXY_HOST="$DEFAULT_PROXY_HOST"
  return 0
}

# Hedef makineyi belirle. Tanımdan sonra çağrılır.
resolve_host || PROXY_HOST="$DEFAULT_PROXY_HOST"

usage() {
  say "Kullanım: $0 <komut>"
  say ""
  say "  menu              menüyü aç (varsayılan)"
  say "  start             seçili proxy'leri aç + daemon başlat"
  say "  stop              daemon + tüm tüneller + portları kapat"
  say "  restart           kapat + aç"
  say "  status            VPN + proxy durumu"
  say "  setup             hangi proxy'ler / retry ayarı"
  say "  watch             canlı log akışı"
  say "  hosts             hedef makine listesini göster"
  say ""
  say "  $0 <no>           listedeki <no>. makineyi seç ve BAĞLAN"
  say "                   örn. $0 2"
  say ""
  say "  Hedef listesi: $HOSTS_FILE"
  say "  Tek seferlik geçersiz kılma:"
  say "    PROXY_HOST=<ip> $0 start"
}

# -----------------------------------------------
# Interaktif kurulum
# -----------------------------------------------
interactive_setup() {
  load_conf
  say ""
  say "════════════════════════════════════════════════════════"
  say "  VPN + Proxy Yöneticisi — Kurulum"
  say "════════════════════════════════════════════════════════"
  say ""
  say "  Hangi proxy'ler açılsın? (virgülle ayır, örnek: 1,2,3)"
  say ""
  local i=1 e name port
  for e in "${ALL_PROXIES[@]}"; do
    IFS=':' read -r name port _ <<< "$e"
    say "     $i) $name  (port $port)"
    i=$((i + 1))
  done
  say ""
  local cur; cur=$(printf '%s' "$SELECTED" | tr ',' ' ')
  [ -n "$cur" ] && say "  Şu an: $cur"
  say ""
  local ans
  read -rp "  Seçim (örn. 1,2,3 — hepsi için 'hepsi'): " ans
  case "${ans:-}" in
    hepsi|Hepsi|HEPSI|all) ans="hepsi" ;;
  esac
  if [ "$ans" = "hepsi" ]; then
    SELECTED="1,2,3,4"
  else
    # girdi numaraları geçerli mi, tekilleştir
    local clean="" n
    for n in $(printf '%s' "$ans" | tr ',' ' '); do
      case "$n" in
        ''|*[!0-9]*) continue ;;
        1|2|3|4) case ",$SELECTED,$clean," in *",$n,"*) ;; *) clean="$clean,$n" ;; esac ;;
      esac
    done
    SELECTED="${clean#,}"
  fi
  if [ -z "$SELECTED" ]; then
    say "  Geçerli seçim yok — çıkılıyor."
    return 1
  fi
  say ""
  say "  Seçilen: $SELECTED"
  say ""
  say "  Bağlantı koptuğunda otomatik yeniden bağlansın mı?"
  say "    (10s → 4dk arası kademeli aralıklarla)"
  say ""
  local r
  if [ "$RETRY" = "true" ]; then say "  Şu an: EVET"; else say "  Şu an: HAYIR"; fi
  read -rp "  Retry (true/false) [Enter=mevcut]: " r
  [ -n "$r" ] && RETRY="$r"
  case "$RETRY" in true|false) ;; *) RETRY="true" ;; esac

  # Parola bir kez sorulur (sadece burada, sadece interaktif)
  load_secrets
  if ! ssh_password >/dev/null 2>&1; then
    say ""
    say "  SSH parolası bir kez sorulacak ($SECRETS_FILE içine yazılacak)."
    say "  Bundan sonra sorulmayacak — VPN açılınca hepsi otomatik bağlanır."
    local pw
    read -rsp "  Parola: " pw; echo
    [ -n "$pw" ] && { save_password "$pw"; say "  ✅ Kaydedildi (chmod 600)."; }
  else
    say ""
    say "  Kayıtlı parola bulundu — tekrar sorulmayacak."
  fi
  save_conf
  say ""
  say "  Ayarlar kaydedildi: $CONF_FILE"
  say ""
  return 0
}

# Seçili proxy'lerin "ad:port:uzak" listesi.
# want "1,3" -> opencode + kilo. Sıra numarası listedeki sabit sırayla eşleşir.
selected_proxies() {
  local want="${1:-}" e name port remote i=1
  for e in "${ALL_PROXIES[@]}"; do
    IFS=':' read -r name port remote <<< "$e"
    case ",$want," in
      *",$i,"*) printf '%s:%s:%s\n' "$name" "$port" "$remote" ;;
    esac
    i=$((i + 1))
  done
  return 0
}

# -----------------------------------------------
# Proxy bağlama (tek seferlik)
# -----------------------------------------------
connect_selected() {
  local want="${1:-}" quiet="${2:-}" ok=0 fail=0 e name port remote
  for e in $(selected_proxies "$want"); do
    IFS=':' read -r name port remote <<< "$e"
    if api_ok "$port"; then
      [ "$quiet" = "1" ] || say "  ✅ $name (port $port) zaten canlı"
      ok=$((ok + 1))
    elif deadline 90 ensure_tunnel "$port" "$remote"; then
      [ "$quiet" = "1" ] || say "  ✅ $name (port $port) bağlandı"
      ok=$((ok + 1))
    else
      [ "$quiet" = "1" ] || say "  ❌ $name (port $port) bağlanamadı"
      fail=$((fail + 1))
    fi
  done
  [ "$quiet" = "1" ] || say "  → bağlanan: $ok, başarısız: $fail"
  return 0
}

# -----------------------------------------------
# Durum
# -----------------------------------------------
show_status() {
  load_conf; load_secrets; refresh_snapshot
  say ""
  local vs; vs=$(vpn_state)
  if [ "$vs" = "kapalı" ]; then
    say "  🔴 VPN: KAPALI — proxy'ler kurulamaz"
  else
    say "  🟢 VPN: $vs"
    if host_reachable; then say "     hedef $PROXY_HOST erişilebilir"
    else say "     ⚠️  hedef $PROXY_HOST ERİŞİLEMEZ"; fi
  fi
  say ""
  say "  PROXY            PORT     DURUM"
  say "  ─────────────────────────────────────"
  local e name port remote line p
  for e in $(selected_proxies "$SELECTED"); do
    IFS=':' read -r name port remote <<< "$e"
    if api_ok "$port" 5; then
      p="✅ canlı"
    elif port_busy "$port"; then
      p="⚠️  asılı port"
    else
      p="❌ kapalı"
    fi
    printf '  %-15s %-8s %s\n' "$name" "$port" "$p"
  done
  say ""
  say "  Seçili: $SELECTED   Retry: $RETRY"
  say "  Hedef:   $PROXY_HOST  ($(host_note))"
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; then
    say "  🟢 Yönetici daemon çalışıyor (pid $(cat "$PID_FILE"))"
  else
    say "  ⚪ Yönetici daemon duruyor"
  fi
  # OpenCode bu localhost portlarını KULLANIR; tünel yoksa model listesini
  # göremez. Kullanıcı bunu "altyapi çalışmıyor" sanabilir.
  local missing=0
  for e in $(selected_proxies "$SELECTED"); do
    IFS=':' read -r name port remote <<< "$e"
    api_ok "$port" 4 || missing=$((missing + 1))
  done
  if [ "$missing" -gt 0 ] && [ "$vs" != "kapalı" ]; then
    say "  ⚠️  $missing proxy canlı değil → OpenCode bu modelleri GÖREMEZ."
    say "     (VPN + tünel gerekli; altyapı sorunu değil)"
  fi
  say ""
  say ""
}

# -----------------------------------------------
# DAEMON: VPN izler, proxy'leri otomatik yönetir
#   - VPN gelince ısınma (warm) aralıklarıyla bağlanır
#   - VPN gidince bekle
#   - retry=false ise kopan proxy'ler bir daha denenmez
#   - ASLA parola sormaz, ASLA pop-up göstermez
# -----------------------------------------------
run_daemon() {
  echo $$ > "$PID_FILE"
  trap 'rm -f "$PID_FILE"; exit 0' INT TERM
  load_conf; load_secrets
  log "═══ Yönetici başladı (seçili=$SELECTED retry=$RETRY) ═══"

  local prev_vpn="bilinmiyor" interval="$WARM_INTERVAL"
  local connected="" e name port remote need

  while true; do
    refresh_snapshot
    local vs; vs=$(vpn_state)
    local vpnup=0; [ "$vs" != "kapalı" ] && vpnup=1

    if [ "$vpnup" = "1" ]; then
      start_caffeinate
      if [ "$prev_vpn" != "1" ]; then
        log "▼ VPN AÇILDI: $vs — proxy'ler ısıtılıyor (ilk deneme ${interval}s)"
        [ -n "$connected" ] && { log "  (önceki oturumdan bağlı: $connected)"; connected=""; }
      fi
      # Bağlanılması gerekenler: seçili olan ve canlı olmayanlar
      need=""
      for e in $(selected_proxies "$SELECTED"); do
        IFS=':' read -r name port remote <<< "$e"
        api_ok "$port" 4 || need="$need $name:$port:$remote"
      done
      if [ -n "$need" ]; then
        for e in $need; do
          IFS=':' read -r name port remote <<< "$e"
          if deadline 90 ensure_tunnel "$port" "$remote"; then
            connected="$connected $name"
            log "  ✅ $name bağlandı (port $port)"
          else
            log "  ❌ $name bağlanamadı (port $port)"
          fi
        done
        # Bağlantı kurulduğu için ısınma sıfırlanır
        interval="$WARM_INTERVAL"
      else
        # Hepsi canlı: aralık en yüksek değere (4 dk) kadar açılır
        [ "$interval" -lt "$MAX_INTERVAL" ] && interval=$((interval * 2))
        [ "$interval" -gt "$MAX_INTERVAL" ] && interval="$MAX_INTERVAL"
        log "  · tüm proxy'ler canlı — sonraki kontrol ${interval}s"
      fi
    else
      if [ "$prev_vpn" != "0" ]; then
        log "▲ VPN KAPANDI — tüneller kapatılıyor, portlar bırakılıyor"
        close_all_ports
        connected=""
        stop_caffeinate
      fi
      interval="$WARM_INTERVAL"
    fi
    prev_vpn="$vpnup"

    # retry=false: VPN açıldıktan sonra kurulamayan proxy sürekli denenmez,
    # tüm bağlantılar kurulana kadar uzun aralıkta beklenir.
    if [ "$RETRY" = "false" ] && [ -n "$need" ]; then
      [ "$interval" -lt "$MAX_INTERVAL" ] && interval=$MAX_INTERVAL
    fi
    sleep "$interval"
  done
}

daemon_running() { [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; }

start_daemon() {
  daemon_running && { say "🟢 Yönetici zaten çalışıyor (pid $(cat "$PID_FILE"))."; return 0; }
  load_conf; load_secrets
  if [ -z "$SELECTED" ]; then
    say "⚠️  Hangi proxy'lerin açılacağı seçilmemiş. Kurulum sihirbazı çalışıyor..."
    interactive_setup || return 1
  fi
  env DAEMON=1 CONFIG_DIR="$CONFIG_DIR" STATE_DIR="$STATE_DIR" \
      SECRETS_FILE="$SECRETS_FILE" CONF_FILE="$CONF_FILE" \
      PROXY_HOST="$PROXY_HOST" PROXY_USER="$PROXY_USER" PROXY_SSH_PORT="$PROXY_SSH_PORT" \
      WARM_INTERVAL="$WARM_INTERVAL" MAX_INTERVAL="$MAX_INTERVAL" \
      bash "${BASH_SOURCE[0]}" >>"$LOG_FILE" 2>&1 &
  disown 2>/dev/null || true
  sleep 1
  if daemon_running; then say "✅ Yönetici başlatıldı (pid $(cat "$PID_FILE"))."; else say "❌ Başlatılamadı — $LOG_FILE"; return 1; fi
}

stop_daemon() {
  [ -f "$PID_FILE" ] || return 0
  local pid; pid=$(cat "$PID_FILE" 2>/dev/null)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    say "🛑 Yönetici durduruluyor (pid $pid)..."
    kill "$pid" 2>/dev/null; sleep 0.5; kill -9 "$pid" 2>/dev/null
  fi
  rm -f "$PID_FILE"
}

# Seçili (ya da verilen) proxy'lerin portlarını kapatır.
# free_port yalnızca portu tutan ssh sürecini öldürür; başka program varsa dokunmaz.
# close_all_ports [secim]  — arg verilmezse SELECTED kullanılır
close_all_ports() {
  local want="${1:-$SELECTED}" e name port remote closed=0
  [ -n "$want" ] || want="1,2,3,4"
  for e in $(selected_proxies "$want"); do
    IFS=':' read -r name port remote <<< "$e"
    if port_busy "$port"; then
      say "  🛑 $name kapatılıyor (port $port)"
      if free_port "$port"; then closed=$((closed+1)); else say "     ⚠️  kapatılamadı"; fi
    fi
  done
  [ "$closed" -gt 0 ] && say "  → $closed port kapatıldı."
  return 0
}

stop_all() {
  stop_daemon
  say "Tüm proxy portları kapatılıyor..."
  close_all_ports "1,2,3,4"
  stop_caffeinate
  say "✅ Hepsi kapatıldı (daemon + tüneller + portlar)."
}

# -----------------------------------------------
# Canlı log akışı (renkli, bağlantı durumu satırlarıyla)
# -----------------------------------------------
stream_log() {
  [ -f "$LOG_FILE" ] || { say "Log yok: $LOG_FILE"; return 1; }
  say "── canlı log ──"
  say "   Menüye dönmek için: 'q' + Enter"
  say "────────────────────────────────────────────────────────"
  # Önceki satırları bir kez bas
  tail -n 30 "$LOG_FILE" 2>/dev/null | while IFS= read -r line; do colorize_log "$line"; done
  # Canlı takip: 'q' girilene kadar log satırlarını bas.
  # tail -f'in stdin'i var; onu kullanıcı kanalı yapıp 'q'yu yakalarız.
  tail -f -n 0 "$LOG_FILE" 2>/dev/null | while IFS= read -r line; do
    colorize_log "$line"
    # 'q' basıldıysa menüye dön
    if read -t 0.3 -r k 2>/dev/null; then
      case "$k" in q|Q) break ;; esac
    fi
  done &
  local logpid=$!
  # Kullanıcıdan 'q' bekle (read bu satırı bekler)
  while true; do
    read -r -n 1 -t 1 key 2>/dev/null || continue
    case "$key" in
      q|Q) break ;;
    esac
  done
  kill "$logpid" 2>/dev/null
  pkill -P "$logpid" 2>/dev/null
  say ""
  say "── menüye dönüldü ──"
}

# Log satırını renklendir
colorize_log() {
  case "$1" in
    *"bağlandı"*|*"AÇILDI"*|*"başlatıldı"*|*"başladı"*)
      printf '\033[32m%s\033[0m\n' "$1" ;;
    *"❌"*|*"KAPANDI"*|*"HATA"*|*"kapatılamadı"*|*"asılı"*|*"dokunulmuyor"*)
      printf '\033[31m%s\033[0m\n' "$1" ;;
    *"▼"*|*"▲"*|*"tüm proxy"*)
      printf '\033[36m%s\033[0m\n' "$1" ;;
    *"☕"*) printf '\033[33m%s\033[0m\n' "$1" ;;
    *) printf '\033[90m%s\033[0m\n' "$1" ;;
  esac
}

# -----------------------------------------------
# OpenCode model senkronizasyonu (sync_proxy_models.js)
# -----------------------------------------------
sync_models() {
  if [ ! -f "$SYNC_JS" ]; then
    say "❌ $SYNC_JS bulunamadı."
    return 1
  fi
  say ""
  say "── OpenCode model senkronizasyonu ──"
  local n=0 e name port remote
  for e in $(selected_proxies "$SELECTED"); do
    IFS=':' read -r name port remote <<< "$e"
    if api_ok "$port" 5; then n=$((n + 1)); else say "  ⚠️  $name canlı değil, atlanacak"; fi
  done
  if [ "$n" -eq 0 ]; then
    say "❌ Hiçbir seçili proxy canlı değil. Önce proxy'leri aç (menü 1)."
    return 1
  fi
  say "  $n proxy canlı — modeller okunuyor..."
  say ""
  local args=""
  read -rp "  Ölü modelleri de sil? (--prune) [e/h]: " p
  case "${p:-h}" in e|E|evet) args="--prune" ;; esac
  say ""
  if command -v node >/dev/null 2>&1; then
    node "$SYNC_JS" $args
  else
    say "❌ node bulunamadı."
    return 1
  fi
  say ""
  say "ℹ️  Değişiklik varsa opencode'u yeniden başlat."
  say ""
}

# -----------------------------------------------
# Menü
# -----------------------------------------------
menu() {
  load_conf; load_secrets
  while true; do
    refresh_snapshot
    local vs; vs=$(vpn_state)
    say ""
    say "════════════════════════════════════════════════════════"
    if [ "$vs" = "kapalı" ]; then
      say "  🔴 VPN KAPALI"
    else
      say "  🟢 VPN: $vs"
      host_reachable && say "     $PROXY_HOST erişilebilir" || say "     ⚠️  $PROXY_HOST erişilemiyor"
    fi
    say "────────────────────────────────────────────────────────"
    local e name port remote line
    for e in $(selected_proxies "$SELECTED"); do
      IFS=':' read -r name port remote <<< "$e"
      if api_ok "$port" 4; then line="✅ canlı"
      elif port_busy "$port"; then line="⚠️  asılı port"
      else line="❌ kapalı"; fi
      printf '  %-14s %-6s %s\n' "$name" "$port" "$line"
    done
    say "────────────────────────────────────────────────────────"
    say "  Seçili: $SELECTED   Retry: $RETRY"
  say "  Hedef:   $PROXY_HOST  ($(host_note))"
    if daemon_running; then say "  Daemon: 🟢 pid $(cat "$PID_FILE")"
    else say "  Daemon: ⚪ duruyor"; fi
    say ""
    say "  1) Proxy'leri aç (bağlan + daemon başlat)"
    say "  2) Proxy'leri kapat (portları da kapat)"
    say "  3) Durumu göster"
    say "  4) Canlı log akışı ('q' ile menüye dön)"
    say "  5) Ayarlar (hangi proxy'ler / retry)"
    say "  6) OpenCode modellerini güncelle"
    say "  7) Çıkış"
    say ""
    local c
    read -rp "  Seçim [1-7]: " c
    case "${c:-}" in
      1) do_start ;;
      2) stop_all ;;
      3) show_status ;;
      4) stream_log; say "" ;;
      5) interactive_setup ;;
      6) sync_models ;;
      7|"") say "Çıkılıyor."; return 0 ;;
      *) say "  Geçersiz seçim." ;;
    esac
  done
}

do_start() {
  load_conf
  ensure_password_loaded
  if [ -z "$SELECTED" ]; then
    say "⚠️  Önce hangi proxy'lerin açılacağını seçmelisiniz."
    interactive_setup || return 1
  fi
  # VPN/host durumunu TAZELE — yoksa bayat SNAP ile yanlış karar verir.
  refresh_snapshot
  if can_connect; then
    connect_selected "$SELECTED"
    start_daemon
  else
    say ""
    say "🔴 VPN kapalı / hedef erişilemiyor ($PROXY_HOST)."
    say "   Yine de daemon başlatılsın mı? VPN açılınca otomatik kurar."
    local a
    read -rp "   [e/h] " a
    case "${a:-e}" in
      h|H|hayir|Hayır) say "   Başlatılmadı."; return 0 ;;
      *) start_daemon; say "   VPN açılınca otomatik bağlanacak. (Durdurmak: $0 stop)" ;;
    esac
  fi
}

# -----------------------------------------------
# Giriş noktası
# -----------------------------------------------
# `source` edilirse menü ÇALIŞMAZ (fonksiyonlar kullanılabilir).
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
if [ "${DAEMON:-0}" = "1" ]; then
  run_daemon
  exit 0
fi

# İLK ÇALIŞMA: ayar yoksa kurulum sihirbazını MUTLAKA çalıştır.
# Kullanıcı "hangi proxy'leri istiyorum?" sorusunu cevaplamadan
# hiçbir şey açılmaz — istemeden bağlanma olmaz.
if [ "${1:-}" != "setup" ] && [ "${1:-}" != "status" ] && [ "${1:-}" != "help" ]; then
  load_conf
  if [ -z "$SELECTED" ]; then
    say ""
    say "🆕 İlk kurulum — hangi proxy'lerin açılmasını istiyorsunuz?"
    say ""
    interactive_setup || {
      say ""
      say "Kurulum tamamlanmadı. '$0 setup' ile tekrar deneyebilirsiniz."
      exit 1
    }
    say ""
    say "Şimdi: '$0 start' ile bağlanabilirsiniz."
  fi
fi

case "${1:-menu}" in
  menu) menu ;;
  start) do_start ;;
  stop) stop_all ;;
  status) show_status ;;
  setup) interactive_setup && say "Yeniden başlatmak için: $0 stop && $0 start" ;;
  restart)
    stop_all
    # VPN/host kısa süreli erişilemez olabilir (tünel kapanınca).
    # 15s bekle: bu sırada VPN/host toparlanır, sonra bağlan.
    say "Yeniden bağlanılıyor..."
    _w=0
    while [ "$_w" -lt 15 ]; do
      can_connect && break
      sleep 1; _w=$((_w + 1))
    done
    load_conf; do_start
    ;;
  watch|log) stream_log ;;
  hosts|ip|ips) show_hosts ;;
  # ./vpn_proxy.sh 2  →  listedeki 2. makineyi seç ve BAĞLAN.
  # VPN DHCP kiraları sık değiştiği için hızlı geçiş için.
  ''|*[!0-9]*) usage ;;
  *)
    if select_host_by_index "$1"; then
      do_start
    else
      say ""
      show_hosts
    fi
    ;;
esac
fi
