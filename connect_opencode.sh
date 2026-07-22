#!/usr/bin/env bash

UBUNTU_IP="${UBUNTU_IP:-10.1.37.223}"
UBUNTU_USER="${UBUNTU_USER:-halis}"
LOCAL_PORT="${LOCAL_PORT:-6446}"
REMOTE_PORT="${REMOTE_PORT:-6446}"
MODEL_TIMEOUT="${MODEL_TIMEOUT:-10}"
MODEL_RETRIES="${MODEL_RETRIES:-3}"

echo "========================================="
echo "🔌 OpenCode Remote Proxy Connection"
echo "========================================="

check_tunnel() {
  lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1
}

establish_tunnel() {
  echo "🔄 Establishing background SSH tunnel ($LOCAL_PORT -> localhost:$REMOTE_PORT)..."
  ssh -N -f -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${UBUNTU_USER}@${UBUNTU_IP}
}

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

if check_tunnel; then
  echo "ℹ️  Port $LOCAL_PORT is already in use locally. Tunnel is active."
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

echo "🔍 Fetching active models from OpenCode API..."
if ! fetch_models; then
  echo "⚠️  Failed to reach OpenCode API after $MODEL_RETRIES attempts."
  echo "Falling back to default model."
  SELECTED_MODEL="deepseek-v4-flash-free"
else
  MODELS_LIST=$(echo "$MODELS_JSON" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    models = [m["id"] for m in data.get("data", [])]
    if models:
        print(" ".join(models))
except Exception:
    sys.exit(1)
' 2>/dev/null)

  if [ -z "$MODELS_LIST" ]; then
    echo "⚠️  Could not parse models from API. Using default."
    SELECTED_MODEL="deepseek-v4-flash-free"
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

export OPENAI_API_BASE="http://localhost:${LOCAL_PORT}/v1"
export OPENAI_API_KEY="oc-89707dcf6c84c410ee7fa8c49daeeafaad3d22f7"
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