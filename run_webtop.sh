#!/usr/bin/env bash

set -euo pipefail

CONTAINER_NAME="webtop"
IMAGE="lscr.io/linuxserver/webtop:ubuntu-mate"
PORT="3333"

docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

docker run -d --name "$CONTAINER_NAME" \
  --platform=linux/amd64 \
  -p "${PORT}:3000" \
  -e PUID="$(id -u)" \
  -e PGID="$(id -g)" \
  -e TZ="Europe/Istanbul" \
  -e SELKIES_MANUAL_WIDTH="1920" \
  -e SELKIES_MANUAL_HEIGHT="1080" \
  -e SELKIES_IS_MANUAL_RESOLUTION_MODE="true" \
  -e SELKIES_USE_CSS_SCALING="true" \
  -e SELKIES_FRAMERATE="30" \
  --shm-size="2gb" \
  --memory="6g" \
  "$IMAGE" >/dev/null

echo "Waiting for container boot..."
until docker exec "$CONTAINER_NAME" pgrep -x Xvfb >/dev/null 2>&1 || \
  docker exec "$CONTAINER_NAME" pgrep -x Xorg >/dev/null 2>&1; do
  sleep 1
done

docker exec -i -u root "$CONTAINER_NAME" bash <<'EOF'
set -euo pipefail

SESSION_USER="abc"
SESSION_GROUP="dialout"
LAYOUT_NAME="webtop-clean"
LAYOUT_FILE="/usr/share/mate-panel/layouts/${LAYOUT_NAME}.layout"
APT_UPDATED=0

apt_install() {
  if [ "$#" -eq 0 ]; then
    return
  fi

  if [ "$APT_UPDATED" -eq 0 ]; then
    apt-get update
    APT_UPDATED=1
  fi

  DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
}

ensure_nodesource_repo() {
  if command -v node >/dev/null 2>&1; then
    return
  fi

  apt_install ca-certificates curl gnupg
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  APT_UPDATED=0
}

ensure_windsurf_repo() {
  if dpkg -s windsurf >/dev/null 2>&1; then
    return
  fi

  apt_install ca-certificates curl gnupg
  install -d -m 0755 /etc/apt/keyrings

  if [ ! -f /etc/apt/keyrings/windsurf-stable.gpg ]; then
    curl -fsSL "https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/windsurf.gpg" \
      | gpg --dearmor -o /etc/apt/keyrings/windsurf-stable.gpg
  fi

  cat >/etc/apt/sources.list.d/windsurf.list <<'REPO'
deb [arch=amd64 signed-by=/etc/apt/keyrings/windsurf-stable.gpg] https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/apt stable main
REPO

  APT_UPDATED=0
}

session_env_value() {
  local key="$1"
  local session_pid
  local session_line

  session_pid="$(pgrep -u "$SESSION_USER" -x mate-session | head -n 1 || true)"
  if [ -z "$session_pid" ]; then
    echo "Could not find mate-session for ${SESSION_USER}" >&2
    exit 1
  fi

  session_line="$(su -l "$SESSION_USER" -c "ps eww -p '$session_pid' | tail -n 1")"
  local value
  value="$(printf '%s\n' "$session_line" | grep -o "${key}=[^ ]*" | head -n 1 || true)"
  if [ -z "$value" ]; then
    echo "Could not find ${key} in mate-session environment" >&2
    exit 1
  fi

  printf '%s\n' "$value"
}

run_in_session() {
  local command_text="$1"
  local home_var
  local runtime_var
  local display_var
  local dbus_var
  local escaped_command

  home_var="$(session_env_value HOME)"
  runtime_var="$(session_env_value XDG_RUNTIME_DIR)"
  display_var="$(session_env_value DISPLAY)"
  dbus_var="$(session_env_value DBUS_SESSION_BUS_ADDRESS)"
  printf -v escaped_command '%q' "$command_text"

  su -l "$SESSION_USER" -c "$home_var $runtime_var $display_var $dbus_var bash -lc $escaped_command"
}

echo "Preparing clean MATE panel layout..."
awk '
  /^\[Object indicatorappletcomplete\]$/ { skip = 1; next }
  skip && /^$/ { skip = 0; next }
  !skip { print }
' /usr/share/mate-panel/layouts/familiar.layout >"$LAYOUT_FILE"

echo "Fixing config permissions..."
install -d -o "$SESSION_USER" -g "$SESSION_GROUP" /config/.cache /config/.cache/dconf /config/.XDG
chown -R "$SESSION_USER:$SESSION_GROUP" /config/.cache /config/.XDG

echo "1. Installing Node.js..."
ensure_nodesource_repo
apt_install nodejs

echo "2. Installing Firefox..."
if ! dpkg -s firefox >/dev/null 2>&1; then
  apt_install firefox
fi

echo "Setting Firefox as default browser..."
update-alternatives --set x-www-browser /usr/bin/firefox || true
update-alternatives --set gnome-www-browser /usr/bin/firefox || true
run_in_session "xdg-settings set default-web-browser firefox.desktop"

echo "Resetting panel and starting Firefox + Terminal..."
run_in_session "gsettings set org.mate.panel default-layout '${LAYOUT_NAME}'"
run_in_session "mate-panel --reset --layout '${LAYOUT_NAME}' --replace >/tmp/mate-panel-reset.log 2>&1 &"
run_in_session "firefox >/tmp/firefox.log 2>&1 &"
run_in_session "mate-terminal >/tmp/mate-terminal.log 2>&1 &"

echo "3. Installing Codex..."
if ! command -v codex >/dev/null 2>&1; then
  npm install -g @openai/codex
fi

echo "4. Installing Windsurf..."
if ! dpkg -s windsurf >/dev/null 2>&1; then
  ensure_windsurf_repo
  apt_install windsurf
fi

echo "Launching Windsurf..."
run_in_session "windsurf --no-sandbox >/tmp/windsurf.log 2>&1 &"

if run_in_session "gsettings get org.mate.panel object-id-list" | grep -q "indicatorappletcomplete"; then
  echo "Indicator applet is still present after panel reset" >&2
fi
EOF

echo "Webtop Ubuntu MATE ready at http://localhost:${PORT}"
