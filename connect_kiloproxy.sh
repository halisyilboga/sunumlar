#!/usr/bin/env bash

# ==============================================================================
# KiloProxy Tunnel & Model Selector
# Run this script on your local machine using: source connect_kiloproxy.sh
# ==============================================================================

# 1. CONFIGURATION
UBUNTU_IP="10.1.37.223"  # Ubuntu machine IP
UBUNTU_USER="halis"      # SSH username
LOCAL_PORT=5380          # Local port to map
REMOTE_PORT=5380         # Remote port of KiloProxy

echo "========================================="
echo "🔌 KiloProxy Remote Connection"
echo "========================================="

# 2. TUNNEL CONNECTION
# Check if local port is already in use
if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "ℹ️  Port $LOCAL_PORT is already in use locally. Assuming tunnel is active."
else
    echo "🔄 Establishing background SSH tunnel ($LOCAL_PORT -> localhost:$REMOTE_PORT)..."
    ssh -N -f -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${UBUNTU_USER}@${UBUNTU_IP}
    if [ $? -eq 0 ]; then
        echo "✅ Tunnel established successfully."
        sleep 1.5 # Wait for tunnel to stabilize
    else
        echo "❌ Failed to open SSH tunnel."
        return 1 2>/dev/null || exit 1
    fi
fi

# 3. DYNAMIC MODEL SELECTION
echo "🔍 Fetching active models from KiloProxy API..."
MODELS_JSON=$(curl -s --max-time 5 http://localhost:${LOCAL_PORT}/v1/models)

if [ -z "$MODELS_JSON" ]; then
    echo "⚠️  Failed to reach KiloProxy API. Endpoint might be offline or starting."
    echo "Falling back to default model."
    SELECTED_MODEL="openrouter/free"
else
    # Parse models dynamically using Python to avoid jq dependency
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
        SELECTED_MODEL="openrouter/free"
    else
        echo "-----------------------------------------"
        echo "Select an active model to use:"
        echo "-----------------------------------------"
        # Simple selection menu
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

# 4. EXPORT ENVIRONMENT VARIABLES
export OPENAI_API_BASE="http://localhost:${LOCAL_PORT}/v1"
export OPENAI_API_KEY="anonymous" # KiloProxy default auth token
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
