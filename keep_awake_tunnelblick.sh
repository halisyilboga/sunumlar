#!/bin/bash

CAFFEINATE_PID=""

is_vpn_connected() {
  scutil --nc list 2>/dev/null | grep -q "Connected"
}

while true; do
  if is_vpn_connected; then
    if [ -z "$CAFFEINATE_PID" ]; then
      caffeinate -i &
      CAFFEINATE_PID=$!
    fi
  else
    if [ -n "$CAFFEINATE_PID" ]; then
      kill $CAFFEINATE_PID 2>/dev/null
      CAFFEINATE_PID=""
    fi
  fi
  
  sleep 5
done