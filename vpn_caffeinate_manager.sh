#!/bin/bash

LOG_FILE="/tmp/vpn_caffeinate_manager.log"
CAFFEINATE_PID=""
LAST_STATE="unknown"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

is_vpn_connected() {
  # 1. Tunnelblick uygulamasının açık olup olmadığını kontrol et
  if pgrep -x "Tunnelblick" >/dev/null 2>&1 || pgrep -f "Tunnelblick.app" >/dev/null 2>&1; then
    # Tunnelblick konfigürasyon durumlarını AppleScript ile sorgula
    local tb_states
    tb_states=$(osascript -e 'tell application "Tunnelblick" to get state of configurations' 2>/dev/null)
    # Konfigürasyonlardan herhangi biri tam olarak CONNECTED durumunda mı?
    if echo "$tb_states" | grep -qw "CONNECTED"; then
      return 0
    fi
  fi

  # 2. Yedek kontrol: Aktif openvpn prosesi VE atanmış IPv4 adresi olan utun tünel arayüzü var mı?
  if pgrep -x "openvpn" >/dev/null 2>&1; then
    if ifconfig | grep -E '^utun[0-9]+:' -A 4 | grep -q 'inet '; then
      return 0
    fi
  fi

  return 1
}

cleanup() {
  log "Script sonlandırılıyor. Caffeinate temizleniyor..."
  if [ -n "$CAFFEINATE_PID" ]; then
    kill "$CAFFEINATE_PID" 2>/dev/null
  fi
  exit 0
}

trap cleanup INT TERM EXIT

log "Script başlatıldı. Tunnelblick VPN bağlantısı izleniyor..."
log "Log dosyası: $LOG_FILE"

while true; do
  if is_vpn_connected; then
    CURRENT_STATE="connected"
    if [ "$CURRENT_STATE" != "$LAST_STATE" ]; then
      log "VPN BAĞLANDI - Uykuya geçmeyi önlemek için caffeinate başlatılıyor"
    fi
    # Caffeinate çalışmıyorsa veya kapandıysa yeniden başlat
    if [ -z "$CAFFEINATE_PID" ] || ! kill -0 "$CAFFEINATE_PID" 2>/dev/null; then
      caffeinate -i &
      CAFFEINATE_PID=$!
      log "Caffeinate başlatıldı (PID: $CAFFEINATE_PID)"
    fi
  else
    CURRENT_STATE="disconnected"
    if [ "$CURRENT_STATE" != "$LAST_STATE" ]; then
      log "VPN KESİLDİ/KAPATILDI - Caffeinate durduruluyor, bilgisayar uykuya geçebilir"
    fi
    if [ -n "$CAFFEINATE_PID" ]; then
      kill "$CAFFEINATE_PID" 2>/dev/null
      log "Caffeinate durduruldu (PID: $CAFFEINATE_PID)"
      CAFFEINATE_PID=""
    fi
  fi

  LAST_STATE="$CURRENT_STATE"
  sleep 5
done
