#!/usr/bin/env bash
# =========================================
# 🔌 OpenCode Remote Proxy Connection (keepalive destekli)
# Kullanım:
#   ./connect_opencode.sh          - tunnel + model seçimi
#   ./connect_opencode.sh status   - durum kontrolü
#   ./connect_opencode.sh stop     - keepalive + tunnel kapat
#   KEEPALIVE=yes ./connect_opencode.sh   - soru sormadan keepalive aç
# =========================================

UBUNTU_IP="${UBUNTU_IP:-10.1.37.223}"
UBUNTU_USER="halis"
LOCAL_PORT="${LOCAL_PORT:-6446}"
REMOTE_PORT="${REMOTE_PORT:-6446}"
MODEL_TIMEOUT="${MODEL_TIMEOUT:-10}"
MODEL_RETRIES="${MODEL_RETRIES:-3}"
KEEPALIVE="${KEEPALIVE:-ask}"                 # yes | no | ask
KEEPALIVE_INTERVAL="${KEEPALIVE_INTERVAL:-30}"

PROVIDER_TITLE="OpenCode Remote Proxy"
DEFAULT_MODEL="deepseek-v4-flash-free"
# API key repoda tutulmaz: ~/.config/sunumlar/secrets.env (chmod 600) veya ortam değişkeni.
SECRETS_FILE="${SECRETS_FILE:-$HOME/.config/sunumlar/secrets.env}"
# shellcheck source=/dev/null
[ -f "$SECRETS_FILE" ] && . "$SECRETS_FILE"
API_KEY="${OPENCODE_PROXY_API_KEY:-}"
[ -z "$API_KEY" ] && echo "⚠️  OPENCODE_PROXY_API_KEY yok ($SECRETS_FILE içine ekleyin)" >&2

RUN_DIR="${TMPDIR:-/tmp}/opencode-tunnel-${LOCAL_PORT}"
PID_FILE="$RUN_DIR/keepalive.pid"
LOG_FILE="$RUN_DIR/keepalive.log"
PASS_FILE="$RUN_DIR/.password"
ASKPASS="$RUN_DIR/askpass.sh"

SOURCED=0
[ "${BASH_SOURCE[0]}" != "$0" ] && SOURCED=1

_top_fail() {
  echo "$1"
  return 1 2>/dev/null || exit 1
}

# -----------------------------------------------
# Tunnel / API testleri
# -----------------------------------------------
api_ok() {
  local out
  out=$(curl -s --max-time "$MODEL_TIMEOUT" "http://localhost:${LOCAL_PORT}/v1/models" 2>/dev/null)
  case "$out" in
    *'"data"'*) return 0 ;;
    *) return 1 ;;
  esac
}

listeners_exist() {
  [ -n "$(lsof -ti :"$LOCAL_PORT" -sTCP:LISTEN 2>/dev/null)" ]
}

# Port dinliyor ama API cevap vermiyorsa = ölü tunnel.
# Sadece ssh süreçlerini öldürür; farklı bir süreç varsa hata döner.
kill_stale() {
  local out line pid="" cmd
  out=$(lsof -nP -i :"$LOCAL_PORT" -sTCP:LISTEN -Fpc 2>/dev/null) || true
  [ -z "$out" ] && return 0
  while IFS= read -r line; do
    case "$line" in
      p*) pid="${line#p}" ;;
      c*)
        cmd="${line#c}"
        if [ "$cmd" = "ssh" ]; then
          echo "🧹 Ölü tunnel temizleniyor (pid $pid, port $LOCAL_PORT)..."
          kill "$pid" 2>/dev/null || true
        else
          echo "❌ Port $LOCAL_PORT '${cmd}' (pid $pid) tarafından kullanılıyor - elle kapatın."
          return 1
        fi
        ;;
    esac
  done <<< "$out"
  sleep 1
  local stuck
  stuck=$(lsof -ti :"$LOCAL_PORT" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$stuck" ]; then
    kill -9 $stuck 2>/dev/null || true
    sleep 0.5
  fi
  return 0
}

prompt_credentials() {
  UBUNTU_USER="halis"
  echo "-----------------------------------------"
  echo "SSH kullanıcısı: halis (sabit)"
  read -rsp "SSH şifresi (boş = ssh anahtarı/etkileşim): " SSH_PASSWORD
  echo
  echo "-----------------------------------------"
}

# SSH_PASSWORD varsa askpass ile sessiz (arka plan uyumlu) bağlanır,
# yoksa ssh'ın kendi etkileşimli şifre sorusunu kullanır.
open_tunnel() {
  mkdir -p "$RUN_DIR"
  chmod 700 "$RUN_DIR" 2>/dev/null || true
  if [ -n "${SSH_PASSWORD:-}" ]; then
    printf '%s' "$SSH_PASSWORD" > "$PASS_FILE"
    chmod 600 "$PASS_FILE"
    printf '#!/bin/sh\ncat %s\n' "$PASS_FILE" > "$ASKPASS"
    chmod 700 "$ASKPASS"
    SSH_ASKPASS="$ASKPASS" SSH_ASKPASS_REQUIRE=force \
      ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
          -N -L "${LOCAL_PORT}:localhost:${REMOTE_PORT}" \
          "${UBUNTU_USER}@${UBUNTU_IP}" >>"$LOG_FILE" 2>&1 &
  else
    rm -f "$PASS_FILE" "$ASKPASS"
    ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
        -N -f -L "${LOCAL_PORT}:localhost:${REMOTE_PORT}" \
        "${UBUNTU_USER}@${UBUNTU_IP}"
  fi
  return 0
}

wait_for_api() {
  local i=1
  while [ "$i" -le "$MODEL_RETRIES" ]; do
    api_ok && return 0
    sleep 1.5
    i=$((i + 1))
  done
  return 1
}

ensure_tunnel() {
  if api_ok; then
    echo "ℹ️  Port $LOCAL_PORT zaten aktif - tunnel açık."
    return 0
  fi
  if listeners_exist; then
    kill_stale || return 1
  fi
  prompt_credentials
  echo "🔄 SSH tunnel başlatılıyor ($LOCAL_PORT -> localhost:$REMOTE_PORT)..."
  open_tunnel
  if [ -n "${SSH_PASSWORD:-}" ]; then
    unset SSH_PASSWORD
  fi
  if wait_for_api; then
    echo "✅ Tunnel kuruldu."
    return 0
  fi
  echo "❌ Tunnel kurulamadı (şifre hatalı olabilir - tekrar deneyin)."
  return 1
}

fetch_models() {
  local attempt=0 MODELS_JSON=""
  while [ "$attempt" -lt "$MODEL_RETRIES" ]; do
    MODELS_JSON=$(curl -s --max-time "$MODEL_TIMEOUT" "http://localhost:${LOCAL_PORT}/v1/models" 2>/dev/null)
    if [ -n "$MODELS_JSON" ]; then
      FETCHED_MODELS_JSON="$MODELS_JSON"
      return 0
    fi
    attempt=$((attempt + 1))
    [ "$attempt" -lt "$MODEL_RETRIES" ] && sleep 1
  done
  return 1
}

parse_models() {
  if command -v node >/dev/null 2>&1; then
    echo "$1" | node -e '
let d="";process.stdin.on("data",c=>d+=c).on("end",()=>{
  try{const j=JSON.parse(d);const ids=(j.data||[]).map(m=>m.id).filter(Boolean);
  if(ids.length)process.stdout.write(ids.join("\n"));}catch(e){process.exit(1);}})'
  else
    echo "$1" | grep -o '"id":"[^"]*"' | sed 's/^"id":"//;s/"$//'
  fi
}

# -----------------------------------------------
# Keepalive
# -----------------------------------------------
stop_keepalive() {
  local pid
  if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "🛑 Keepalive durduruluyor (pid $pid)..."
      kill "$pid" 2>/dev/null || true
      sleep 0.5
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
  fi
}

# macOS dialog ile şifre sor (kullanıcı adı sabit: halis, keepalive arka plan süreci terminalde soramaz)
daemon_ask_password() {
  local pw
  UBUNTU_USER="halis"
  pw=$(osascript -e 'display dialog "Yeniden bağlanmak için SSH şifresini girin ('"$UBUNTU_IP"', halis)" default answer "" with hidden answer buttons {"Vazgeç","Bağlan"} default button "Bağlan"' -e 'text returned of result' 2>/dev/null) || return 1
  [ -n "$pw" ] || return 1
  printf '%s' "$pw" > "$PASS_FILE"
  chmod 600 "$PASS_FILE"
  SSH_PASSWORD="$pw"
  return 0
}

notify() {
  osascript -e "display notification \"$1\" with title \"$PROVIDER_TITLE\"" >/dev/null 2>&1 || true
}

run_daemon() {
  echo $$ > "$PID_FILE"
  trap 'rm -f "$PID_FILE"; exit 0' INT TERM
  echo "[$(date '+%F %T')] keepalive başladı (interval=${KEEPALIVE_INTERVAL}s)"
  UBUNTU_USER="halis"
  rm -f "$RUN_DIR/.user" 2>/dev/null || true
  if [ -f "$PASS_FILE" ]; then
    SSH_PASSWORD=$(cat "$PASS_FILE")
  fi
  while true; do
    date '+%F %T' > "$RUN_DIR/lastcheck"
    if ! api_ok; then
      echo "[$(date '+%F %T')] bağlantı kopuk - test ediliyor ve yeniden bağlanılıyor..."
      kill_stale
      if [ -z "${SSH_PASSWORD:-}" ]; then
        echo "[$(date '+%F %T')] şifre yok - kullanıcıya soruluyor..."
        daemon_ask_password || {
          echo "[$(date '+%F %T')] şifre girilmedi, 30 sn sonra tekrar denenecek."
          sleep "$KEEPALIVE_INTERVAL"
          continue
        }
      fi
      open_tunnel
      if wait_for_api; then
        echo "[$(date '+%F %T')] yeniden bağlandı ✅"
        notify "Tunnel yeniden bağlandı (port $LOCAL_PORT)"
      else
        echo "[$(date '+%F %T')] şifre reddedildi - yeniden soruluyor..."
        rm -f "$PASS_FILE"
        unset SSH_PASSWORD
        if daemon_ask_password && open_tunnel && wait_for_api; then
          echo "[$(date '+%F %T')] yeniden bağlandı ✅"
          notify "Tunnel yeniden bağlandı (port $LOCAL_PORT)"
        else
          echo "[$(date '+%F %T')] bağlanılamadı - bir sonraki turda tekrar denenecek."
          notify "Tunnel bağlanamadı! port $LOCAL_PORT"
        fi
      fi
    fi
    sleep "$KEEPALIVE_INTERVAL"
  done
}

start_keepalive() {
  stop_keepalive
  mkdir -p "$RUN_DIR"
  if [ ! -f "$PASS_FILE" ]; then
    local pw
    echo "ℹ️  Keepalive sessiz yeniden bağlanmak için şifre kaydedilecek."
    read -rsp "SSH şifresi (boş = anahtar ile dene): " pw
    echo
    if [ -n "$pw" ]; then
      printf '%s' "$pw" > "$PASS_FILE"
      chmod 600 "$PASS_FILE"
    fi
  fi
  env KEEPALIVE_DAEMON=1 \
      UBUNTU_IP="$UBUNTU_IP" UBUNTU_USER="$UBUNTU_USER" \
      LOCAL_PORT="$LOCAL_PORT" REMOTE_PORT="$REMOTE_PORT" \
      MODEL_TIMEOUT="$MODEL_TIMEOUT" MODEL_RETRIES="$MODEL_RETRIES" \
      KEEPALIVE_INTERVAL="$KEEPALIVE_INTERVAL" \
      bash "${BASH_SOURCE[0]}" >>"$LOG_FILE" 2>&1 &
  disown 2>/dev/null || true
  sleep 1
  if keepalive_running; then
    echo "✅ Keepalive aktif (pid $(cat "$PID_FILE")), log: $LOG_FILE"
  else
    echo "❌ Keepalive başlatılamadı! log: $LOG_FILE"
    tail -5 "$LOG_FILE" 2>/dev/null
    return 1
  fi
}

keepalive_running() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null
}

# -----------------------------------------------
# Daemon girişi (arka plan süreci)
# -----------------------------------------------
if [ "${KEEPALIVE_DAEMON:-0}" = "1" ]; then
  run_daemon
  exit 0
fi

# -----------------------------------------------
# Alt komutlar
# -----------------------------------------------
case "${1:-}" in
  stop)
    stop_keepalive
    if listeners_exist && api_ok; then
      echo "🛑 Tunnel kapatılıyor..."
      kill_stale || true
    fi
    rm -rf "$RUN_DIR"
    echo "✅ Tunnel + keepalive durduruldu."
    return 0 2>/dev/null || exit 0
    ;;
  status)
    if api_ok; then
      echo "✅ Tunnel aktif (localhost:$LOCAL_PORT -> $UBUNTU_IP:$REMOTE_PORT)"
    else
      echo "❌ Tunnel kapalı (localhost:$LOCAL_PORT)"
    fi
    if keepalive_running; then
      echo "🟢 Keepalive çalışıyor (pid $(cat "$PID_FILE"))"
      echo "   log: $LOG_FILE"
      [ -f "$RUN_DIR/lastcheck" ] && echo "   son kontrol: $(cat "$RUN_DIR/lastcheck")"
    else
      echo "⚪ Keepalive duruyor"
    fi
    return 0 2>/dev/null || exit 0
    ;;
esac

# -----------------------------------------------
# Ana akış
# -----------------------------------------------
echo "========================================="
echo "🔌 $PROVIDER_TITLE Connection"
echo "========================================="

ensure_tunnel || _top_fail "❌ Tunnel kurulamadı, çıkılıyor."
sleep 1

# Keepalive kararı — model seçiminden ÖNCE başlatılır
if keepalive_running; then
  echo "🟢 Keepalive zaten aktif (pid $(cat "$PID_FILE")). Durdurmak için: $0 stop"
else
  if [ "$KEEPALIVE" = "ask" ]; then
    echo "-----------------------------------------"
    read -rp "Keepalive açılsın mı? (kopunca otomatik yeniden bağlanır) [Y/n]: " ka
    case "${ka:-Y}" in
      y|Y|yes|YES|e|E|"") KEEPALIVE=yes ;;
      *) KEEPALIVE=no ;;
    esac
  fi
  if [ "$KEEPALIVE" = "yes" ]; then
    start_keepalive
  fi
fi

echo "🔍 Fetching active models from $PROVIDER_TITLE API..."
SELECTED_MODEL=""
if ! fetch_models; then
  echo "⚠️  Failed to reach API after $MODEL_RETRIES attempts."
  SELECTED_MODEL="$DEFAULT_MODEL"
else
  MODELS_LIST=$(parse_models "$FETCHED_MODELS_JSON")
  if [ -z "$MODELS_LIST" ]; then
    SELECTED_MODEL="$DEFAULT_MODEL"
  else
    echo "-----------------------------------------"
    echo "Select an active model to use:"
    echo "-----------------------------------------"
    select opt in $MODELS_LIST; do
      if [ -n "$opt" ]; then
        SELECTED_MODEL=$opt
        break
      else
        echo "❌ Invalid selection. Please enter a valid option number."
      fi
    done
  fi
fi

# Keepalive kararı (yukarıda tunnel kurulur kurulmaz başlatıldı)

export OPENAI_API_BASE="http://localhost:${LOCAL_PORT}/v1"
export OPENAI_API_KEY="$API_KEY"
export OPENAI_MODEL_NAME="$SELECTED_MODEL"

echo "-----------------------------------------"
echo "🚀 Environment configured successfully!"
echo "-----------------------------------------"
echo "  • Base URL:   $OPENAI_API_BASE"
echo "  • API Key:    $OPENAI_API_KEY"
echo "  • Model Name: $OPENAI_MODEL_NAME"
echo ""
echo "💡 Usage in Python / LangGraph / CLI:"
echo "   export OPENAI_API_BASE=\"$OPENAI_API_BASE\""
echo "   export OPENAI_API_KEY=\"$OPENAI_API_KEY\""
echo "   export OPENAI_MODEL_NAME=\"$OPENAI_MODEL_NAME\""
echo "========================================="
