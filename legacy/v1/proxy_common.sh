#!/usr/bin/env bash
# =============================================================================
# proxy_common.sh — TUM connect_*.sh ve keepalive'ın ortak kütüphanesi.
# Çalıştırılmaz, `source` edilir.
#
# Çözdüğü 3 sorun:
#   1) Şifre: ~/.config/sunumlar/secrets.env içinde tek yerde saklanır,
#      tüm scriptler oradan okur (UX'ta tekrar sorulmaz).
#   2) VPN kapısı: 10.1.37.223:22 TCP'si açılmadan tunnel açılmaz.
#      VPN gelince supervisor bağlantıyı kendisi kurar.
#   3) ASILI PORT: ssh ölür ama portu bırakmaz / ya da port dinler ama
#      cevap vermez. `proxy_free_port` bunu teşhis edip temizler.
#      Asıl önlem: ServerAlive* + ExitOnForwardFailure (aşağıda).
# =============================================================================

PROXY_HOST="${PROXY_HOST:-10.1.37.223}"
PROXY_USER="${PROXY_USER:-halis}"
PROXY_SSH_PORT="${PROXY_SSH_PORT:-22}"

SECRETS_FILE="${SECRETS_FILE:-$HOME/.config/sunumlar/secrets.env}"
STATE_DIR="${STATE_DIR:-$HOME/.config/sunumlar/proxy}"

PROXY_API_TIMEOUT="${PROXY_API_TIMEOUT:-8}"       # sağlık probu (kısa)
PROXY_API_RETRIES="${PROXY_API_RETRIES:-4}"       # ilk bağlantı denemesi
PROXY_KEEPALIVE_INTERVAL="${PROXY_KEEPALIVE_INTERVAL:-30}"
PROXY_VPN_WAIT="${PROXY_VPN_WAIT:-3600}"          # VPN gelene kadar bekleme sn

# Asılı portun kök nedeni bu iki seçenek:
#   ServerAliveInterval/CountMax : VPN düşünce ssh canlı kalmaz, kendi kapanır
#                                 ve portu SERBEST BIRAKIR (bugün 6447'de olan)
#   ExitOnForwardFailure         : port bağlanamazsa ssh sessizce ölü modda
#                                 kalmaz, hata verip çıkar
PROXY_SSH_OPTS=(
  -o StrictHostKeyChecking=accept-new
  -o ConnectTimeout=10
  -o ServerAliveInterval=15
  -o ServerAliveCountMax=3
  -o ExitOnForwardFailure=yes
  -o TCPKeepAlive=yes
  -p "$PROXY_SSH_PORT"
)

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$1"; }

notify() {
  [ -n "${PROXY_NOTIFY:-1}" ] || return 0
  osascript -e "display notification \"$1\" with title \"${2:-Proxy}\"" >/dev/null 2>&1 || true
}

# -----------------------------------------------
# Sırlar
# -----------------------------------------------
load_secrets() {
  [ -f "$SECRETS_FILE" ] || return 0
  # shellcheck source=/dev/null
  . "$SECRETS_FILE"
}

# SSH parolası: env > secrets.env. `SSH_PASSWORD` geriye uyumlu takma ad.
ssh_password() {
  [ -n "${SSH_PASSWORD:-}" ] && { printf '%s' "$SSH_PASSWORD"; return 0; }
  [ -n "${UBUNTU_SSH_PASSWORD:-}" ] && { printf '%s' "$UBUNTU_SSH_PASSWORD"; return 0; }
  return 1
}

save_ssh_password() {
  local pw="$1"
  [ -n "$pw" ] || return 1
  mkdir -p "$(dirname "$SECRETS_FILE")"
  chmod 700 "$(dirname "$SECRETS_FILE")"
  touch "$SECRETS_FILE"; chmod 600 "$SECRETS_FILE"
  # shellcheck disable=SC1090
  . "$SECRETS_FILE" 2>/dev/null || true
  if grep -q '^UBUNTU_SSH_PASSWORD=' "$SECRETS_FILE" 2>/dev/null; then
    # değer içinde özel karakter varsa güvenli tırnakla
    local q
    q=$(printf '%s' "$pw" | sed "s/'/'\\\\''/g")
    /usr/bin/sed -i '' "s|^UBUNTU_SSH_PASSWORD=.*|UBUNTU_SSH_PASSWORD='$q'|" "$SECRETS_FILE"
  else
    printf 'UBUNTU_SSH_PASSWORD=%s\n' "$(printf '%s' "$pw" | sed "s/'/'\\\\''/g; s/^/'/; s/$/'/")" >> "$SECRETS_FILE"
  fi
  chmod 600 "$SECRETS_FILE"
}

# Parolayı bir kez sor, secrets.env'e yaz. Zaten varsa hiç sormaz.
ensure_password() {
  load_secrets
  if ssh_password >/dev/null 2>&1; then
    return 0
  fi
  echo "-----------------------------------------"
  echo "SSH ($PROXY_USER@$PROXY_HOST) parolası bir kez sorulacak ve"
  echo "  $SECRETS_FILE içine yazılacak (chmod 600)."
  echo "  Artık tüm proxy'ler kendiliğinden bağlanacak."
  echo "-----------------------------------------"
  local pw
  read -rsp "SSH parolası: " pw; echo
  [ -n "$pw" ] || { echo "❌ Parola boş - anahtar (ssh key) ile deneniyor."; return 0; }
  save_ssh_password "$pw"
  unset pw
  SSH_PASSWORD="$(ssh_password)"
  log "✅ Parola kaydedildi ($SECRETS_FILE)"
}

# -----------------------------------------------
# VPN kapısı
# -----------------------------------------------
vpn_ready() {
  nc -z -G 3 "$PROXY_HOST" "$PROXY_SSH_PORT" >/dev/null 2>&1
}

# VPN gelene kadar bekler. 0 = bağlandı, 1 = zaman aşımı.
wait_for_vpn() {
  local limit="${1:-$PROXY_VPN_WAIT}" waited=0
  while ! vpn_ready; do
    if [ "$waited" -ge "$limit" ]; then
      return 1
    fi
    if [ $((waited % 300)) -eq 0 ]; then
      log "⏳ VPN bekleniyor ($PROXY_HOST:22 erişilemiyor, ${waited}s)"
    fi
    sleep 5
    waited=$((waited + 5))
  done
  return 0
}

# -----------------------------------------------
# Port / API teşhisi
# -----------------------------------------------
api_ok() {
  local port="$1" timeout="${2:-$PROXY_API_TIMEOUT}" out
  out=$(curl -s --max-time "$timeout" "http://localhost:${port}/v1/models" 2>/dev/null)
  case "$out" in
    *'"data"'*) return 0 ;;
    *) return 1 ;;
  esac
}

port_listeners() {
  lsof -nP -i ":$1" -sTCP:LISTEN -Fpc 2>/dev/null || true
}

port_busy() {
  [ -n "$(lsof -ti ":$1" -sTCP:LISTEN 2>/dev/null || true)" ]
}

# Port dinliyor ama API cevap vermiyorsa = ÖLÜ/ASILI TUNNEL.
# Sadece ssh süreçlerini öldürür; başka bir program varsa dokunmaz.
free_port() {
  local port="$1" out line pid="" cmd killed=0 stuck
  out=$(port_listeners "$port")
  [ -z "$out" ] && { wait_port_free "$port" 5 && return 0 || return 1; }

  log "🧹 Port $port asılı/normal dinleniyor, ssh süreçleri temizleniyor..."
  while IFS= read -r line; do
    case "$line" in
      p*) pid="${line#p}" ;;
      c*) cmd="${line#c}"
          if [ "$cmd" = "ssh" ]; then
            kill "$pid" 2>/dev/null && killed=$((killed+1))
          else
            echo "❌ Port $port '${cmd}' (pid $pid) tarafından kullanılıyor - bu bir ssh değil, elle kapatın." >&2
            return 1
          fi
          ;;
    esac
  done <<< "$out"

  sleep 1
  stuck=$(lsof -ti ":$port" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$stuck" ]; then
    log "🧹 Port $port direndi, zorla kapatılıyor: $stuck"
    kill -9 $stuck 2>/dev/null || true
  fi
  wait_port_free "$port" 6
}

# Portun gerçekten boşalmasını bekler (TIME_WAIT / yavaş çıkış).
wait_port_free() {
  local port="$1" limit="${2:-5}" i=0
  while port_busy "$port"; do
    [ "$i" -ge "$((limit * 2))" ] && return 1
    sleep 0.5
    i=$((i + 1))
  done
  return 0
}

# -----------------------------------------------
# Tunnel açma
# -----------------------------------------------
# Parola varsa askpass ile sessiz açar (arka plan/daemon uyumlu).
# Dönüş: açılan ssh PID'i (stdout), başarısızsa 1.
open_tunnel() {
  local port="$1" remote="$2" logfile
  logfile="$STATE_DIR/ssh-${port}.log"
  mkdir -p "$STATE_DIR" && chmod 700 "$STATE_DIR"

  local pw
  pw=$(ssh_password) || pw=""

  if [ -n "$pw" ]; then
    local pf="$STATE_DIR/.password" af="$STATE_DIR/askpass.sh"
    printf '%s' "$pw" > "$pf"; chmod 600 "$pf"
    printf '#!/bin/sh\nexec cat %s\n' "$pf" > "$af"; chmod 700 "$af"
    SSH_ASKPASS="$af" SSH_ASKPASS_REQUIRE=force \
      ssh "${PROXY_SSH_OPTS[@]}" -N -L "${port}:localhost:${remote}" \
      "${PROXY_USER}@${PROXY_HOST}" >>"$logfile" 2>&1 &
  else
    rm -f "$STATE_DIR/.password" "$STATE_DIR/askpass.sh"
    ssh "${PROXY_SSH_OPTS[@]}" -N -L "${port}:localhost:${remote}" \
      "${PROXY_USER}@${PROXY_HOST}" >>"$logfile" 2>&1 &
  fi
  local pid=$!
  sleep 1
  # 1 saniyede öldüyse (şifre reddi, port dolu, VPN yok) hata say
  if ! kill -0 "$pid" 2>/dev/null; then
    tail -2 "$logfile" 2>/dev/null | sed 's/^/    /'
    return 1
  fi
  echo "$pid"
}

wait_for_api() {
  local port="$1" retries="${2:-$PROXY_API_RETRIES}" i
  for i in $(seq 1 "$retries"); do
    api_ok "$port" && return 0
    sleep 1.5
  done
  return 1
}

# -----------------------------------------------
# Zaman sınırı
# -----------------------------------------------
# macOS'ta `timeout` yok. Bir komutu arka planda çalıştırıp süre dolunca
# öldürür. ensure_tunnel gibi birden çok aşamalı işlemlerde tek bir adımın
# takılıp kalan süreci bekletmesini engeller.
# with_deadline <saniye> <komut> [arg...]
with_deadline() {
  local secs="$1"; shift
  "$@" &
  local pid=$!
  local i=0
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$i" -ge $((secs * 4)) ]; then
      # Alt sürecin "Terminated" mesajını bu shell'e basmasın.
      { kill -TERM "$pid" 2>/dev/null; } 2>/dev/null
      sleep 1
      kill -9 "$pid" 2>/dev/null
      wait "$pid" 2>/dev/null
      return 124
    fi
    sleep 0.25
    i=$((i + 1))
  done
  wait "$pid"
}

# -----------------------------------------------
# Model listesi / seçimi
# -----------------------------------------------
fetch_models() {
  local port="$1" i out
  for i in 1 2 3; do
    out=$(curl -s --max-time "$PROXY_API_TIMEOUT" "http://localhost:${port}/v1/models" 2>/dev/null)
    if [ -n "$out" ]; then
      printf '%s' "$out"
      return 0
    fi
    sleep 1
  done
  return 1
}

parse_models() {
  if command -v node >/dev/null 2>&1; then
    printf '%s' "$1" | node -e '
let d="";process.stdin.on("data",c=>d+=c).on("end",()=>{
  try{const j=JSON.parse(d);const ids=(j.data||[]).map(m=>m.id).filter(Boolean);
  if(ids.length)process.stdout.write(ids.join("\n"));}catch(e){process.exit(1);}})'
  else
    printf '%s' "$1" | grep -o '"id":"[^"]*"' | sed 's/^"id":"//;s/"$//'
  fi
}

# Etkileşimli terminalde menü gösterir, değilse ilk modeli seçer.
# choose_model <port> <varsayılan> [hariç_tutulan_modeller_boşluklu]
choose_model() {
  local port="$1" default="$2" exclude="${3:-}" json list
  if ! json=$(fetch_models "$port"); then
    printf '%s' "$default"
    return 0
  fi
  list=$(parse_models "$json")
  if [ -n "$exclude" ]; then
    # exclude: "web-search search" -> her birini satır bazında ele
    local e
    for e in $exclude; do
      list=$(printf '%s\n' "$list" | grep -vxF "$e" || true)
    done
  fi
  if [ -z "$list" ]; then
    printf '%s' "$default"
    return 0
  fi
  if [ ! -t 0 ]; then
    printf '%s' "$(printf '%s\n' "$list" | head -1)"
    return 0
  fi
  echo "-----------------------------------------"
  echo "Select an active model:"
  echo "-----------------------------------------"
  local sel
  select sel in $list; do
    if [ -n "$sel" ]; then
      printf '%s' "$sel"
      return 0
    fi
    echo "❌ Geçersiz seçim."
  done
  printf '%s' "$default"
}

# Model seçimini stderr'e yazar, sadece model adını stdout'a basar.
# (Menü çıktısı env export'unu bozmasın diye.)
choose_model_clean() {
  local m
  m=$(choose_model "$@")
  printf '%s\n' "$m" >&2
  printf '%s' "$m"
}

# Tam döngü: sağlıklıysa dokunma, değilse temizle + yeniden aç.
# ensure_tunnel <port> [remote]
ensure_tunnel() {
  local port="$1" remote="${2:-$1}"

  if api_ok "$port"; then
    echo "ℹ️  Port $port zaten canlı."
    return 0
  fi

  if port_busy "$port"; then
    echo "⚠️  Port $port dinliyor ama API cevap vermiyor (asılı tunnel)."
    free_port "$port" || { echo "❌ Port $port temizlenemedi."; return 1; }
  fi

  if ! vpn_ready; then
    echo "⏳ VPN yok, bekleniyor..."
    wait_for_vpn || { echo "❌ VPN ($PROXY_HOST) açılmadı."; return 1; }
  fi

  echo "🔄 SSH tunnel: $port -> $PROXY_HOST:localhost:$remote"
  local pid
  pid=$(open_tunnel "$port" "$remote") || { echo "❌ Tunnel açılamadı."; return 1; }

  if wait_for_api "$port"; then
    echo "✅ Tunnel hazır (pid $pid)."
    return 0
  fi

  echo "❌ Tunnel cevap vermiyor, kapatılıyor."
  kill "$pid" 2>/dev/null || true
  free_port "$port" || true
  return 1
}
