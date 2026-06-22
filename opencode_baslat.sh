#!/bin/bash

# ==========================================
# KULLANICI AYARLARI
# ==========================================
#UBUNTU_IP="10.1.37.223"  # Ubuntu makinenin IP adresi
#UBUNTU_USER="ubuntu" # Ubuntu makinesindeki kullanıcı adın

# 1. TÜNELİ AÇ (Arka planda sessizce çalışır)
echo "🔄 Ubuntu makinesine bağlantı tüneli açılıyor..."
#ssh -N -f -L 11434:localhost:11434 $UBUNTU_USER@$UBUNTU_IP

# 2. OLLAMA YERİNE OPENAI UYUMLULUK API'Sİ
# Modelin "tool (araç)" çağrılarında takılıp "devam et" beklemesini engeller.
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_API_KEY="ollama-local" # Burası boş kalmamalı, herhangi bir metin olabilir.

# 3. OPENCODE'U BAŞLAT (Sistem Promptu Müdahalesi İle)
echo "🚀 OpenCode başlatılıyor..."

# Burada modeli 'ollama/...' değil 'openai/...' olarak çağırıyoruz ki uyumluluk katmanı devreye girsin.
# Ayrıca gevezelik yapmaması için katı bir sistem promptu ekliyoruz.
opencode -m openai/gemma4-agent

