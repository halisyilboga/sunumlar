#!/usr/bin/env bash
# =============================================================================
# proxy_login.sh — TEK giriş noktası. Tüm proxy'leri (claude/opencode/kilo/
# antigravity) tek komutla açar, VPN gelince kendiliğinden kurar.
#
#   ./proxy_login.sh              # bağlan (parola sorarsa bir kez sorar)
#   ./proxy_login.sh status       # tüm proxy durumu
#   ./proxy_login.sh stop         # tüm keepalive + tunnel'ları kapat
#   ./proxy_login.sh restart      # durdur + başlat
#   ./proxy_login.sh watch        # log'u canlı izle
#
# Parola ~/.config/sunumlar/secrets.env içine bir kez yazılır (chmod 600).
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
# shellcheck source=proxy_common.sh
. "./proxy_common.sh"

# isim:port:uzak-port
PROXIES=(
  "opencode:6446:6446"
  "cline:6447:6447"
  "kilo:5380:5380"
  "antigravity:4000:4000"
)

KEEPALIVE_PID_FILE="$STATE_DIR/keepalive.pid"
KEEPALIVE_LOG="$STATE_DIR/keepalive.log"
# Tek bir proxy'nin bağlanma denemesi en fazla bu kadar sürebilir
PROXY_TRY_TIMEOUT="${PROXY_TRY_TIMEOUT:-45}"

keepalive_running() {
  [ -f "$KEEPALIVE_PID_FILE" ] && kill -0 "$(cat "$KEEPALIVE_PID_FILE" 2>/dev/null)" 2>/dev/null
}

# Bir portun adı (log/mesaj için)
name_of() {
  local p="$1" e
  for e in "${PROXIES[@]}"; do
    IFS=':' read -r n lp _ <<< "$e"
    [ "$lp" = "$p" ] && { echo "$n"; return 0; }
  done
  echo "port$p"
}

status_all() {
  load_secrets
  printf '%-14s %-8s %-8s %s\n' PROXY PORT API NOT
  # vpn_ready her proxy için yeniden sorgulanırsa status saniyelerce sürer;
  # bir kez ölçüp sonucu paylaşıyoruz.
  vpn_ready && vpn_up=1 || vpn_up=0
  local e n lp rp a p
  for e in "${PROXIES[@]}"; do
    IFS=':' read -r n lp rp <<< "$e"
    if api_ok "$lp" 5; then
      a="✅ canlı"
      p="$(port_busy "$lp" && echo "tunnel açık" || echo "tunnel yok")"
    else
      a="❌ yok"
      if port_busy "$lp"; then
        p="⚠️ ASILI port"
      elif [ "$vpn_up" = "1" ]; then
        p="bağlanmamış"
      else
        p="vpn-yok"
      fi
    fi
    printf '%-14s %-8s %-8s %s\n' "$n" "$lp" "$a" "$p"
  done
  echo
  if [ "$vpn_up" = "1" ]; then
    echo "🟢 VPN: $PROXY_HOST erişilebilir"
  else
    echo "🔴 VPN: $PROXY_HOST:22 ERİŞİLEMEZ — bağlantılar kurulamıyor"
  fi
  if keepalive_running; then
    echo "🟢 Keepalive çalışıyor (pid $(cat "$KEEPALIVE_PID_FILE"))  log: $KEEPALIVE_LOG"
  else
    echo "⚪ Keepalive duruyor"
  fi
}

connect_all() {
  ensure_password
  mkdir -p "$STATE_DIR"; chmod 700 "$STATE_DIR"

  if ! wait_for_vpn 20; then
    echo "⚠️  VPN henüz yok ($PROXY_HOST:22 kapalı)."
    echo "    Keepalive arka planda bekleyecek; VPN gelince hepsi kendiliğinden bağlanacak."
    echo "    Şimdiden bağlanmayı denemek için: ./proxy_login.sh   (tekrar çalıştır)"
    start_keepalive
    return 0
  fi

  local e n lp rp ok=0 fail=0
  for e in "${PROXIES[@]}"; do
    IFS=':' read -r n lp rp <<< "$e"
    echo
    echo "── $n (port $lp) ──"
    if ensure_tunnel "$lp" "$rp"; then
      ok=$((ok + 1))
    else
      fail=$((fail + 1))
    fi
  done

  echo
  echo "========================================="
  echo "  Bağlanan: $ok   Bağlanamayan: $fail"
  echo "========================================="
  start_keepalive
  status_all
}

start_keepalive() {
  mkdir -p "$STATE_DIR"; chmod 700 "$STATE_DIR"
  if keepalive_running; then
    echo "🟢 Keepalive zaten aktif (pid $(cat "$KEEPALIVE_PID_FILE"))."
    return 0
  fi
  env KEEPALIVE_DAEMON=1 STATE_DIR="$STATE_DIR" \
      SECRETS_FILE="$SECRETS_FILE" \
      KEEPALIVE_INTERVAL="$PROXY_KEEPALIVE_INTERVAL" \
      PROXY_HOST="$PROXY_HOST" PROXY_USER="$PROXY_USER" \
      PROXY_SSH_PORT="$PROXY_SSH_PORT" \
      bash "${BASH_SOURCE[0]}" >>"$KEEPALIVE_LOG" 2>&1 &
  disown 2>/dev/null || true
  sleep 1
  if keepalive_running; then
    echo "✅ Keepalive başlatıldı (pid $(cat "$KEEPALIVE_PID_FILE")), log: $KEEPALIVE_LOG"
  else
    echo "❌ Keepalive başlatılamadı. log: $KEEPALIVE_LOG"
    tail -5 "$KEEPALIVE_LOG" 2>/dev/null | sed 's/^/    /'
    return 1
  fi
}

stop_keepalive() {
  local pid
  [ -f "$KEEPALIVE_PID_FILE" ] || return 0
  pid=$(cat "$KEEPALIVE_PID_FILE" 2>/dev/null)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    log "🛑 Keepalive durduruluyor (pid $pid)"
    kill "$pid" 2>/dev/null || true
    sleep 0.5
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$KEEPALIVE_PID_FILE"
}

stop_all() {
  stop_keepalive
  local e n lp rp
  for e in "${PROXIES[@]}"; do
    IFS=':' read -r n lp rp <<< "$e"
    if port_busy "$lp"; then
      log "🛑 $n tunnel kapatılıyor (port $lp)"
      free_port "$lp" 2>/dev/null || true
    fi
  done
  rm -rf "$STATE_DIR"
  echo "✅ Tüm proxy'ler kapatıldı."
}

# -----------------------------------------------
# Daemon: VPN'i izler, portları sağlıklı tutar
# -----------------------------------------------
run_daemon() {
  mkdir -p "$STATE_DIR"; chmod 700 "$STATE_DIR"
  echo $$ > "$KEEPALIVE_PID_FILE"
  trap 'rm -f "$KEEPALIVE_PID_FILE"; exit 0' INT TERM
  load_secrets
  # Parola kayıtlı değilse, soramayız — kullanıcı login scriptini çalıştırsın.
  if ! ssh_password >/dev/null 2>&1; then
    log "⚠️  Kayıtlı SSH parolası yok. ./proxy_login.sh çalıştırın."
  fi
  log "🟢 Keepalive başladı (interval=${PROXY_KEEPALIVE_INTERVAL}s)"

  local vpn_prev="unknown" failed_prev="" e n lp rp failed=""
  while true; do
    date '+%F %T' > "$STATE_DIR/lastcheck"

    # VPN kapısı — VPN yoksa hiçbir şeye dokunma, sadece bekle
    if ! vpn_ready; then
      if [ "$vpn_prev" = "up" ]; then
        log "🔴 VPN kesildi — bağlantılar beklemeye alınıyor."
        notify "VPN kesildi, proxy'ler bekliyor" "Proxy"
      fi
      vpn_prev="down"
      sleep "$PROXY_KEEPALIVE_INTERVAL"
      continue
    fi
    if [ "$vpn_prev" != "up" ]; then
      log "🟢 VPN geldi ($PROXY_HOST) — proxy'ler kuruluyor."
      notify "VPN bağlandı, proxy'ler kuruluyor" "Proxy"
    fi
    vpn_prev="up"

    failed=""
    for e in "${PROXIES[@]}"; do
      IFS=':' read -r n lp rp <<< "$e"
      if api_ok "$lp"; then
        continue
      fi
      log "🔁 $n (port $lp) cevap vermiyor — yeniden bağlanılıyor."
      # Tek bir takılı proxy tüm döngüyü kilitlemesin diye süre sınırı.
      if PROXY_NOTIFY=0 with_deadline "$PROXY_TRY_TIMEOUT" \
           ensure_tunnel "$lp" "$rp" >/dev/null 2>&1; then
        :
      else
        failed="$failed $n"
      fi
    done

    if [ -n "$failed" ]; then
      log "⚠️  Bağlanamadı:$failed"
    else
      # önceden kopmuşsa bildir
      if [ -n "$failed_prev" ] && [ -z "$failed" ]; then
        notify "Tüm proxy'ler tekrar bağlı" "Proxy"
      fi
    fi
    failed_prev="$failed"

    sleep "$PROXY_KEEPALIVE_INTERVAL"
  done
}

if [ "${KEEPALIVE_DAEMON:-0}" = "1" ]; then
  run_daemon
  exit 0
fi

case "${1:-connect}" in
  connect|"")
    connect_all
    ;;
  status)
    status_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    echo
    connect_all
    ;;
  watch)
    tail -f "$KEEPALIVE_LOG"
    ;;
  *)
    echo "Kullanım: $0 [connect|status|stop|restart|watch]"
    exit 1
    ;;
esac
