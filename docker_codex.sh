docker rm -f webtop 2>/dev/null; \
  docker run -d --name webtop \
    --platform=linux/amd64 \
    -p 3333:3000 \
    -e PUID=$(id -u) -e PGID=$(id -g) -e TZ=Europe/Istanbul \
    -e SELKIES_MANUAL_WIDTH=1920 \
    -e SELKIES_MANUAL_HEIGHT=1080 \
    -e SELKIES_IS_MANUAL_RESOLUTION_MODE=true \
    -e SELKIES_USE_CSS_SCALING=true \
    -e SELKIES_FRAMERATE=30 \
    --shm-size=2gb --memory=6g \
    lscr.io/linuxserver/webtop:ubuntu-mate && \
  echo "Waiting 20s for Webtop Ubuntu amd64 boot (1920x1080)..." && sleep 20 && \
  docker exec -u root webtop bash -lc 'curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && npm install -g @openai/codex' && \
  echo "STABLE 1080p Webtop Ubuntu VM Ready at http://localhost:3333"




  # https://tmailor.com/ 
  # https://temp-mail.org/
  # Asdfg1234**.

  cp -r ~/.codex ~/codexler/.codex.backup1 2>/dev/null || true

  docker cp webtop:/config/.codex ~/codexler/.codex.backup2
----- 
# sonrasi icin:
  rm -rf ~/.codex
  cp -r ~/codexler/.codex.backup2 ~/.codex


   docker cp webtop:/config/.windsurf ~/windsurf/.windsurf.backup2
