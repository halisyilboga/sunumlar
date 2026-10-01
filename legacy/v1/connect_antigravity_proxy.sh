#!/usr/bin/env bash
# ==============================================================================
# Usage: source ./connect_antigravity_proxy.sh
# 
# NOTE: Must be run with 'source' (or '. ./connect_antigravity_proxy.sh') so that
# the selected model & API environment variables persist in your active terminal session!
# ==============================================================================

UBUNTU_IP="${UBUNTU_IP:-10.1.37.223}"
UBUNTU_USER="${UBUNTU_USER:-halis}"
LOCAL_PORT="${LOCAL_PORT:-4000}"
REMOTE_PORT="${REMOTE_PORT:-4000}"
MODEL_TIMEOUT="${MODEL_TIMEOUT:-10}"
MODEL_RETRIES="${MODEL_RETRIES:-3}"

echo "========================================="
echo "🔌 Antigravity Claude Proxy Connection"
echo "========================================="

check_tunnel() {
  curl -s --max-time 2 http://localhost:${LOCAL_PORT}/v1/models >/dev/null 2>&1
}

establish_tunnel() {
  echo "🔄 Establishing background SSH tunnel ($LOCAL_PORT -> localhost:$REMOTE_PORT on $UBUNTU_IP)..."
  ssh -N -f -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${UBUNTU_USER}@${UBUNTU_IP}
}

if check_tunnel; then
  echo "ℹ️  Port $LOCAL_PORT is already accessible."
else
  establish_tunnel
  if [ $? -eq 0 ]; then
    echo "✅ Tunnel established successfully."
    sleep 1.5
  else
    echo "❌ Failed to open SSH tunnel."
    return 1 2>/dev/null || exit 1
  fi
fi

fetch_models() {
  local attempt=0
  while [ $attempt -lt $MODEL_RETRIES ]; do
    MODELS_JSON=$(curl -s --max-time $MODEL_TIMEOUT http://localhost:${LOCAL_PORT}/v1/models 2>/dev/null)
    if [ -n "$MODELS_JSON" ]; then
      return 0
    fi
    attempt=$((attempt + 1))
    if [ $attempt -lt $MODEL_RETRIES ]; then
      echo "⚠️  Retrying model fetch (attempt $((attempt + 1))/$MODEL_RETRIES)..."
      sleep 1
    fi
  done
  return 1
}

echo "🔍 Fetching active models from Antigravity Proxy API..."
if ! fetch_models; then
  echo "⚠️  Failed to reach Proxy API after $MODEL_RETRIES attempts."
  echo "Falling back to default model."
  SELECTED_MODEL="gemini-3.5-flash-low"
else
  MODELS_LIST=$(echo "$MODELS_JSON" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    # Filter out non-LLM internal tools like web-search
    models = [m["id"] for m in data.get("data", []) if m["id"] not in ("web-search", "search")]
    if models:
        print("\n".join(models))
except Exception:
    sys.exit(1)
' 2>/dev/null)

  if [ -z "$MODELS_LIST" ]; then
    echo "⚠️  Could not parse models from API. Using default."
    SELECTED_MODEL="gemini-3.5-flash-low"
  else
    echo "-----------------------------------------"
    echo "Select an active model to use:"
    echo "-----------------------------------------"
    idx=1
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      printf "%2d) %s\n" "$idx" "$line"
      idx=$((idx + 1))
    done <<< "$MODELS_LIST"
    total_models=$((idx - 1))
    echo "-----------------------------------------"

    while true; do
      printf "Enter selection number (1-%d): " "$total_models"
      read choice
      if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$total_models" ]; then
        SELECTED_MODEL=$(echo "$MODELS_LIST" | sed -n "${choice}p")
        break
      else
        echo "❌ Invalid selection. Please enter a valid number between 1 and $total_models."
      fi
    done
  fi
fi

export ANTHROPIC_BASE_URL="http://localhost:${LOCAL_PORT}"
export ANTHROPIC_AUTH_TOKEN="test"
export ANTHROPIC_MODEL="$SELECTED_MODEL"

echo "-----------------------------------------"
echo "🚀 Environment configured successfully!"
echo "-----------------------------------------"
echo "  • Base URL:   $ANTHROPIC_BASE_URL"
echo "  • API Key:    $ANTHROPIC_AUTH_TOKEN"
echo "  • Model Name: $ANTHROPIC_MODEL"
echo ""
echo "💡 Usage in Claude Code / CLI:"
echo "   export ANTHROPIC_BASE_URL=\"$ANTHROPIC_BASE_URL\""
echo "   export ANTHROPIC_AUTH_TOKEN=\"$ANTHROPIC_AUTH_TOKEN\""
echo "   export ANTHROPIC_MODEL=\"$ANTHROPIC_MODEL\""
echo "========================================="
