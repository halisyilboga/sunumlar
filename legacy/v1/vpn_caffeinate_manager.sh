#!/bin/bash
# vpn_caffeinate_manager.sh
#   1) Herhangi bir VPN bağlıyken makinenin uykuya girmesini engeller (caffeinate)
#   2) Kullanıcı yokken ajan süreçlerini dondurur (SIGSTOP), dönünce açar (SIGCONT)
#      VARSAYILAN KAPALI (FREEZE_ENABLED=0). Herdr panelindeki ajanı SIGSTOP etmek
#      zsh'in terminali geri almasına yol açar; SIGCONT sonrası ajan arka planda
#      kalır, ilk tty erişiminde SIGTTIN/SIGTTOU ile tekrar T'ye düşer. Herdr panel
#      boş kabuk sanır, resurrect ikinci kopya açar -> RAM/swap katlanır.
#      (29 Eylül 2026 teşhisi; 57 ajan bu şekilde sıkışmıştı.)

POLL_INTERVAL=10
HEARTBEAT_INTERVAL=300
FREEZE_ENABLED="${FREEZE_ENABLED:-0}"
IDLE_FREEZE_AFTER=600
AGENT_PATTERN='opencode|claude|kilocode/cli-darwin-arm64/bin/kilo'

# VPN geldiğinde SSH proxy'lerini (opencode/cline/kilo/antigravity) otomatik
# kur. Tek giriş noktası proxy_login.sh; parola ~/.config/sunumlar/secrets.env
# içinde saklanır, VPN yoksa daemon bekler.
AUTO_PROXY="${AUTO_PROXY:-1}"
PROXY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROXY_LOGIN="$PROXY_DIR/proxy_login.sh"

LAST_STATE="unknown"
FREEZE_STATE="active"
LAST_HEARTBEAT=0
CAFFEINATE_PID=""

log() {
  printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

# Periyodik durum satırı: konsol hiçbir zaman sessiz kalmaz
heartbeat() {
  local idle=$1 agents caf stuck
  agents=$(agent_pids | grep -c .)
  stuck=""
  [ -n "$STUCK_PIDS" ] && stuck=" !!SIKISAN:$STUCK_PIDS"
  if [ "$FREEZE_STATE" = "frozen" ]; then
    caf="DONDURULDU"
  else
    caf="aktif"
    [ -n "$CAFFEINATE_PID" ] || caf="kapalı"
  fi
  log "DURUM vpn=[$CURRENT_STATE] ajan=$agents dondurma=$FREEZE_STATE($FREEZE_COUNT) caffeinate=$caf klavye_sessiz=${idle}s$stuck"
}

# Tek ifconfig çağrısı ile utun arayüzlerinin IPv4 adresleri
SNAPSHOT=""
refresh_snapshot() {
  SNAPSHOT=$(ifconfig -a 2>/dev/null | awk '
    /^[a-z0-9]+:/ { iface=$1; sub(/:$/,"",iface) }
    /^[[:space:]]*inet / && iface ~ /^utun/ { print iface, $2 }
  ')
}

# "tailscale" -> 100.64.0.0/10 beklenir
# "openvpn"   -> 100.x HARİC adres beklenir
vpn_tunnel_ip() {
  local mode="$1" iface ip
  while read -r iface ip; do
    [ -z "$ip" ] && continue
    if [ "$mode" = "tailscale" ]; then
      case "$ip" in 100.*) echo "$iface $ip"; return 0 ;; esac
    else
      case "$ip" in 100.*) ;; *) echo "$iface $ip"; return 0 ;; esac
    fi
  done <<< "$SNAPSHOT"
  return 1
}

is_tunnelblick_connected() {
  pgrep -x "openvpn" >/dev/null 2>&1 || return 1
  vpn_tunnel_ip "openvpn" >/dev/null 2>&1
}

is_tailscale_connected() {
  scutil --nc status "Tailscale" 2>/dev/null | grep -qx "Connected" || return 1
  vpn_tunnel_ip "tailscale" >/dev/null 2>&1
}

# FortiClient ("VPN") / BlancVPN ("BlancVPN"): servis Connected + tünel IP'si.
# Arayüz sahipliği ayrılamadığı için "openvpn" kuralı (100.x hariç) kullanılır.
is_service_vpn_up() {
  scutil --nc status "$1" 2>/dev/null | grep -qx "Connected" || return 1
  vpn_tunnel_ip "openvpn" >/dev/null 2>&1
}

get_vpn_state() {
  local tb="down" ts="down" other="down"
  is_tunnelblick_connected && tb="up"
  is_tailscale_connected && ts="up"
  { is_service_vpn_up "VPN" || is_service_vpn_up "BlancVPN"; } && other="up"
  echo "$tb|$ts|$other"
}

get_vpn_detail() {
  local tb_if ts_if
  tb_if=$(vpn_tunnel_ip "openvpn") || tb_if="-"
  ts_if=$(vpn_tunnel_ip "tailscale") || ts_if="-"
  pgrep -x "openvpn" >/dev/null 2>&1 || tb_if="openvpn süreci yok"
  echo "tunnelblick=[${tb_if}] tailscale=[${ts_if}]"
}

# Klavye/fare en son ne zaman kullanıldı (saniye)
hid_idle_seconds() {
  local ns
  ns=$(ioreg -c IOHIDSystem 2>/dev/null | grep "HIDIdleTime" | head -1 | tr -cd '0-9')
  [ -z "$ns" ] && { echo 0; return 0; }
  echo $((ns / 1000000000))
}

# Dondurulan PID'ler dosyada tutulur: subshell'de kaybolmaz,
# script yeniden başlasa bile kaldığı yerden çözülebilir.
FROZEN_FILE="/tmp/vpn_frozen_pids"
FREEZE_COUNT=0

# SIGSTOP edilecek ajan PID'leri (kendimiz, shell'ler, herdr ve .app paketleri hariç)
agent_pids() {
  local pid comm cmdline
  pgrep -f "$AGENT_PATTERN" 2>/dev/null | while read -r pid; do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    comm=$(ps -o comm= -p "$pid" 2>/dev/null)
    case "$comm" in *bash|zsh|-zsh) continue ;; esac
    case "$comm" in *herdr*) continue ;; esac
    # Masaüstü uygulamaları (örn. Claude.app) dondurulmez — sadece CLI ajanlar
    cmdline=$(ps -o command= -p "$pid" 2>/dev/null)
    case "$cmdline" in *.app/*) continue ;; esac
    echo "$pid"
  done
}

is_stopped() {
  local state
  state=$(ps -o stat= -p "$1" 2>/dev/null)
  [ -z "$state" ] && return 1
  case "$state" in *T*) return 0 ;; esac
  return 1
}

freeze_agents() {
  local pid n=0
  : > "$FROZEN_FILE"
  while read -r pid; do
    [ -z "$pid" ] && continue
    is_stopped "$pid" && continue
    if kill -STOP "$pid" 2>/dev/null; then
      echo "$pid" >> "$FROZEN_FILE"
      n=$((n+1))
    fi
  done <<< "$(agent_pids)"
  FREEZE_COUNT=$n
}

thaw_agents() {
  local pid n=0
  STUCK_PIDS=""
  [ -f "$FROZEN_FILE" ] || { FREEZE_COUNT=0; return 0; }
  while read -r pid; do
    [ -z "$pid" ] && continue
    # Hâlâ STOP durumda olanı aç; bitmişse dokunma
    is_stopped "$pid" && kill -CONT "$pid" 2>/dev/null
  done < "$FROZEN_FILE"
  # SIGCONT teslim edildi diye süreç gerçekten uyanmış olmayabilir.
  # Sahipsiz kalmış bir süreç grubunda kernel SIGCONT'yi sessizce düşürür;
  # o durumda süreç T'de kalır ve yalnızca kill -9 ile kurtulur.
  sleep 1
  while read -r pid; do
    [ -z "$pid" ] && continue
    if is_stopped "$pid"; then
      STUCK_PIDS="$STUCK_PIDS $pid"
    else
      n=$((n+1))
    fi
  done < "$FROZEN_FILE"
  rm -f "$FROZEN_FILE"
  FREEZE_COUNT=$n
}

cleanup() {
  log "Script sonlandırılıyor. Dondurulmuş ajanlar açılıyor, caffeinate temizleniyor..."
  thaw_agents
  [ -n "$CAFFEINATE_PID" ] && kill "$CAFFEINATE_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM EXIT

# Önceki çalışmadan donmuş kalmış ajan varsa (kill -9 / reboot arası)
# açılışta kurtar — SIGCONT çalışan sürece zarar vermez.
thaw_agents
if [ "$FREEZE_COUNT" -gt 0 ]; then
  log "Başlangıç kurtarma: $FREEZE_COUNT donmuş ajan süreci açıldı"
fi

log "Script başlatıldı. VPN (Tunnelblick+Tailscale+FortiClient+BlancVPN) + ajan dondurma (polling ${POLL_INTERVAL}s, dondurma eşiği ${IDLE_FREEZE_AFTER}s)."
log "Durum satırı her ${HEARTBEAT_INTERVAL}s tekrarlanır. Durdurmak için Ctrl-C."
[ "$IDLE_FREEZE_AFTER" -le 60 ] && log "UYARI: IDLE_FREEZE_AFTER <= 60 ise dondurma/açma salınımı yapar (60'dan büyük olmalı)."

while true; do
  refresh_snapshot

  CURRENT_STATE=$(get_vpn_state)
  IFS='|' read -r TB_STATE TS_STATE OTHER_STATE <<< "$CURRENT_STATE"

  if [ "$TB_STATE" != "down" ] || [ "$TS_STATE" != "down" ] || [ "$OTHER_STATE" != "down" ]; then
    VPN_UP=1
    [ "$CURRENT_STATE" != "$LAST_STATE" ] && log "VPN BAĞLANDI [$CURRENT_STATE] ($(get_vpn_detail)) - caffeinate başlatılıyor"
    if [ -z "$CAFFEINATE_PID" ] || ! kill -0 "$CAFFEINATE_PID" 2>/dev/null; then
      caffeinate -i -t 3600 &
      CAFFEINATE_PID=$!
      log "Caffeinate başlatıldı (PID: $CAFFEINATE_PID)"
    fi
    # VPN YENİDEN bağlandığında proxy'leri kur. Sadece durum değişiminde
    # tetiklenir (her poll'da değil) — VPN'sız geçen sürelerde de toparlanır.
    if [ "$AUTO_PROXY" = "1" ] && [ -x "$PROXY_LOGIN" ] \
       && { [ "$LAST_STATE" = "down|down|down" ] || [ -z "$LAST_STATE" ]; }; then
      log "VPN geldi - SSH proxy'leri kuruluyor (proxy_login.sh)"
      bash "$PROXY_LOGIN" connect >>"$PROXY_DIR/vpn_caffeinate_manager.log" 2>&1 \
        && log "Proxy'ler kuruldu" || log "Proxy kurulumu sıkıntılı - vpn_caffeinate_manager.log'a bakın"
    fi
  else
    [ "$CURRENT_STATE" != "$LAST_STATE" ] && log "VPN KESİLDİ [$CURRENT_STATE] ($(get_vpn_detail)) - caffeinate durduruluyor"
    if [ -n "$CAFFEINATE_PID" ]; then
      kill "$CAFFEINATE_PID" 2>/dev/null
      CAFFEINATE_PID=""
    fi
  fi
  LAST_STATE="$CURRENT_STATE"

  IDLE=$(hid_idle_seconds)
  if [ "$FREEZE_ENABLED" = "1" ] && [ "$FREEZE_STATE" != "frozen" ] && [ "$IDLE" -ge "$IDLE_FREEZE_AFTER" ]; then
    freeze_agents
    if [ "$FREEZE_COUNT" -gt 0 ]; then
      FREEZE_STATE="frozen"
      log "Kullanıcı ${IDLE}s sessiz - $FREEZE_COUNT ajan süreci donduruldu (SIGSTOP, bağlam korunuyor)"
    fi
  elif [ "$FREEZE_STATE" = "frozen" ] && [ "$IDLE" -lt 30 ]; then
    thaw_agents
    FREEZE_STATE="active"
    log "Girdi tespit edildi (idle ${IDLE}s) - $FREEZE_COUNT ajan süreci açıldı (SIGCONT)"
    if [ -n "$STUCK_PIDS" ]; then
      log "KRİTİK: $STUCK_PIDS açılamadı, T durumunda sıkıştı (süreç grubu sahipsiz kalmış)."
      log "KRİTİK: Elle kurtarma -> kill -9$STUCK_PIDS"
    fi
  fi

  NOW=$(date +%s)
  if [ $((NOW - LAST_HEARTBEAT)) -ge "$HEARTBEAT_INTERVAL" ]; then
    heartbeat "$IDLE"
    LAST_HEARTBEAT=$NOW
  fi

  sleep "$POLL_INTERVAL"
done
