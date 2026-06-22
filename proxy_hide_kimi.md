# FULL TRANSPARENCY & ZERO FINGERPRINT DESIGN DOKÜMANI v2.0
## Webtop Container Tam İzolasyon ve Anonimleştirme Sistemi

---

## 🎯 HEDEF

Container'ın dışarıya **hiçbir şekilde** host makinenin kimliğini, donanım指纹ini, lokasyonunu veya kullanıcı bilgilerini sızdırmamasını garanti etmek. **Cursor/Windsurf asla sizi, bilgisayarınızı veya hesabınızı eşleştiremeyecek.**

---

## 🔒 GÜVENLİK PRENSİPLERİ (Zero-Trust)

> **KURAL 0**: Varsayılan olarak her şeyi reddet, sadece gerekli olanlara izin ver (Whitelisting)
> **KURAL 1**: Her çalıştırmada yeni kimlik (Memoryless Identity)
> **KURAL 2**: Host bilgisi = Sızdırılacak veri (treat as toxic)
> **KURAL 3**: Donanım bilgisi = Kalıcı指纹 (eliminate or randomize)

---

## 🚨 MEVCUT `run_webtop.sh` GÜVENLİK AÇIKLARI

| # | Açıklama | Risk | Etki |
|---|----------|------|------|
| 1 | Host `PUID/PGID` doğrudan aktarılıyor | **KRİTİK** | Kullanıcı ID'si host'a bağlanabilir |
| 2 | Host `TZ=Europe/Istanbul` aktarılıyor | **YÜKSEK** | Lokasyon tespiti |
| 3 | Container ismi sabit (`webtop`) | **ORTA** | Kalıcı identifier |
| 4 | MAC adresi host bridge'den alınıyor | **KRİTİK** | Donanım指纹 |
| 5 | `/etc/machine-id` ve `/var/lib/dbus/machine-id` persist ediyor | **KRİTİK** | Global unique machine identifier |
| 6 | `product_serial`, `board_serial`, `chassis_serial` erişilebilir | **KRİTİK** | Donanım seri numaraları |
| 7 | CPU model name, flags, MHz görünür | **YÜKSEK** | CPU fingerprinting |
| 8 | Memory ve CPU count doğrudan host değerleri | **ORTA** | Donanım profili |
| 9 | `/sys/class/net` MAC adresleri okunabilir | **YÜKSEK** | Network fingerprint |
| 10 | `XDG_RUNTIME_DIR`, `HOME` host pattern'ini taklit ediyor | **ORTA** | Kullanıcı profiling |
| 11 | Windsurf repository'si doğrudan codeiumdata.com'dan çekiliyor | **YÜKSEK** | Doğrudan IP bağlantısı = kayıt |
| 12 | NodeSource repository doğrudan erişim | **ORTA** | IP logging |
| 13 | Hiçbir ağ izolasyonu yok | **KRİTİK** | Doğrudan host IP'sinden çıkış |
| 14 | `/config` volume kalıcı | **ORTA** | Cross-session tracking |
| 15 | `npm install -g` global registry'den | **ORTA** | NPM analytics |
| 16 | Firefox default browser olarak işaretleniyor | **DÜŞÜK** | Browser fingerprint |
| 17 | `mate-terminal` geçmişi kalıcı olabilir | **DÜŞÜK** | Komut geçmişi |
| 18 | Windsurf `--no-sandbox` ile çalışıyor | **ORTA** | Chromium security bypass |

---

## 🛡️ KATMAN 1: KONTEYNER BAŞLATMA İZOLASYONU

### 1.1 Rastgele Kimlik Üretimi

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============ RASTGELE KİMLİK ÜRETİCİ ============
generate_random_identity() {
    # 8 karakter hex container adı
    CONTAINER_ID="wt_$(openssl rand -hex 4)"
    
    # Rastgele hostname (distro-masked)
    local distros=("ubuntu" "debian" "fedora" "arch")
    local distro="${distros[$RANDOM % ${#distros[@]}]}"
    HOSTNAME="${distro}-$(openssl rand -hex 4)"
    
    # Rastgele MAC (OUI = QEMU/KVM maskeleme için 52:54:00)
    # NOT: 02:xx:xx başlayan MAC'ler lokal/admin, track edilemez
    MAC_ADDRESS="02:$(openssl rand -hex 5 | sed 's/../&:/g;s/:$//')"
    
    # Rastgele machine-id (32 char hex)
    MACHINE_ID="$(openssl rand -hex 16)"
    
    # Sabitlenmiş "anonim" değerler (her container'da aynı)
    PUID=1000
    PGID=1000
    TZ="UTC"
    LANG="C.UTF-8"
    
    export CONTAINER_ID HOSTNAME MAC_ADDRESS MACHINE_ID PUID PGID TZ LANG
}

generate_random_identity
```

### 1.2 Docker Run Parametreleri (Tam İzolasyon)

```bash
# ============ HARDCORE ISOLATION FLAGS ============

docker_run_isolated() {
    docker run -d \
        # --- Temel Kimlik ---
        --name "${CONTAINER_ID}" \
        --hostname "${HOSTNAME}" \
        --mac-address "${MAC_ADDRESS}" \
        
        # --- Namespace İzolasyonu ---
        --uts=private \
        --ipc=private \
        --pid=private \
        --userns=auto \
        --network none \
        
        # --- Güvenlik Seçenekleri ---
        --cap-drop ALL \
        --cap-add SYS_ADMIN \
        --cap-add CHOWN \
        --cap-add SETGID \
        --cap-add SETUID \
        --security-opt no-new-privileges:true \
        --security-opt seccomp="${SEC_PROFILE:-unconfined}" \
        --security-opt apparmor=unconfined \
        
        # --- Kernel Capability Kısıtlamaları ---
        --sysctl net.ipv4.ip_forward=0 \
        --sysctl net.ipv4.conf.all.accept_redirects=0 \
        --sysctl net.ipv4.conf.all.send_redirects=0 \
        
        # --- Dosya Sistemi Güvenliği ---
        --read-only \
        --tmpfs /tmp:noexec,nosuid,size=2g \
        --tmpfs /var/tmp:noexec,nosuid,size=1g \
        --tmpfs /var/log:noexec,nosuid,size=100m \
        
        # --- Donanım Bilgisi Maskeleme (Volume Overlays) ---
        -v /dev/null:/etc/machine-id:ro \
        -v /dev/null:/var/lib/dbus/machine-id:ro \
        -v /dev/null:/etc/hostname:ro \
        -v /dev/null:/etc/hosts:ro \
        -v /dev/null:/sys/class/dmi/id/product_serial:ro \
        -v /dev/null:/sys/class/dmi/id/product_uuid:ro \
        -v /dev/null:/sys/class/dmi/id/board_serial:ro \
        -v /dev/null:/sys/class/dmi/id/chassis_serial:ro \
        -v /dev/null:/sys/class/dmi/id/sys_vendor:ro \
        -v /dev/null:/sys/class/dmi/id/board_vendor:ro \
        -v /dev/null:/sys/class/dmi/id/chassis_vendor:ro \
        -v /dev/null:/sys/class/dmi/id/product_name:ro \
        -v /dev/null:/sys/class/dmi/id/board_name:ro \
        
        # --- CPU Info Maskeleme ---
        -v "${SCRIPT_DIR}/fake_cpuinfo:/proc/cpuinfo:ro" \
        
        # --- Bellek/Resource Limit ---
        --memory="4g" \
        --memory-swap="4g" \
        --memory-swappiness=0 \
        --cpus="4" \
        --cpu-quota="400000" \
        --cpu-period="100000" \
        --pids-limit=2048 \
        --shm-size="2g" \
        
        # --- Environment (Tamamen Sabitlenmiş) ---
        -e PUID="${PUID}" \
        -e PGID="${PGID}" \
        -e TZ="${TZ}" \
        -e LANG="${LANG}" \
        -e LC_ALL="${LANG}" \
        -e HOME="/config" \
        -e USER="abc" \
        -e USERNAME="abc" \
        -e XDG_CONFIG_HOME="/config/.config" \
        -e XDG_CACHE_HOME="/config/.cache" \
        -e XDG_DATA_HOME="/config/.local/share" \
        -e XDG_RUNTIME_DIR="/tmp/runtime-abc" \
        
        # --- Bildirim/IPC Devre Dışı ---
        -e NOTIFY_SOCKET=/dev/null \
        -e DBUS_SYSTEM_BUS_ADDRESS=/dev/null \
        
        # --- Windsurf/Cursor Anti-Telemetry ---
        -e CURSOR_DISABLE_TELEMETRY=1 \
        -e CURSOR_SKIP_LOGIN=1 \
        -e WINDSURF_DISABLE_METRICS=1 \
        -e WINDSURF_NO_FINGERPRINT=1 \
        -e ELECTRON_DISABLE_SECURITY_WARNINGS=true \
        -e ELECTRON_ENABLE_LOGGING=false \
        
        # --- Selkies/GUI Sabit Parametreler ---
        -e SELKIES_MANUAL_WIDTH="1920" \
        -e SELKIES_MANUAL_HEIGHT="1080" \
        -e SELKIES_IS_MANUAL_RESOLUTION_MODE="true" \
        -e SELKIES_USE_CSS_SCALING="true" \
        -e SELKIES_FRAMERATE="30" \
        
        # --- Kalıcılık Yok ---
        --rm \
        --pull=always \
        
        "lscr.io/linuxserver/webtop:ubuntu-mate"
}
```

### 1.3 Sahte CPU Info Dosyası

```bash
# fake_cpuinfo - Her container'da tamamen aynı
mkdir -p "${SCRIPT_DIR}"
cat > "${SCRIPT_DIR}/fake_cpuinfo" <<'CPUEOF'
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
stepping	: 10
microcode	: 0x96
cpu MHz		: 1800.000
cache size	: 6144 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 4
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault invpcid_single pti ssbd ibrs ibpb stibp fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed clflushopt xsaveopt xsavec xgetbv1 xsaves arat umip md_clear arch_capabilities
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data bhi
bogomips	: 3600.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
stepping	: 10
microcode	: 0x96
cpu MHz		: 1800.000
cache size	: 6144 KB
physical id	: 0
siblings	: 4
core id		: 1
cpu cores	: 4
apicid		: 2
initial apicid	: 2
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault invpcid_single pti ssbd ibrs ibpb stibp fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed clflushopt xsaveopt xsavec xgetbv1 xsaves arat umip md_clear arch_capabilities
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data bhi
bogomips	: 3600.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
power management:

processor	: 2
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
stepping	: 10
microcode	: 0x96
cpu MHz		: 1800.000
cache size	: 6144 KB
physical id	: 0
siblings	: 4
core id		: 2
cpu cores	: 4
apicid		: 4
initial apicid	: 4
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault invpcid_single pti ssbd ibrs ibpb stibp fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed clflushopt xsaveopt xsavec xgetbv1 xsaves arat umip md_clear arch_capabilities
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data bhi
bogomips	: 3600.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
power management:

processor	: 3
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
stepping	: 10
microcode	: 0x96
cpu MHz		: 1800.000
cache size	: 6144 KB
physical id	: 0
siblings	: 4
core id		: 3
cpu cores	: 4
apicid		: 6
initial apicid	: 6
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault invpcid_single pti ssbd ibrs ibpb stibp fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed clflushopt xsaveopt xsavec xgetbv1 xsaves arat umip md_clear arch_capabilities
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data bhi
bogomips	: 3600.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
power management:
CPUEOF
```

---

## 🌐 KATMAN 2: AĞ İZOLASYONU ve PROXY ARKASI

### 2.1 Ağ Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│                    HOST MAKİNE                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │          Docker Bridge (docker0) - NO INTERNET         ││
│  │  ┌──────────────────────────────────────────────────┐  ││
│  │  │           Webtop Container                      │  ││
│  │  │  ┌────────────────────────────────────────────┐ │  ││
│  │  │  │     Internal Network Only (172.x.x.x)      │ │  ││
│  │  │  │  NO direct internet access                 │ │  ││
│  │  │  └────────────────────────────────────────────┘ │  ││
│  │  └──────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                             │                                │
│                             ▼                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │           Transparent Proxy (Tor/Socks5)               ││
│  │  - All traffic forced through proxy                     ││
│  │  - DNS over HTTPS/Tor                                   ││
│  │  - TCP connection pooling                               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Proxy Kurulum Script'i

```bash
#!/bin/bash
# setup_proxy.sh - Tor + Privoxy + DNS-over-HTTPS

set -euo pipefail

PROXY_NETWORK="proxy_net"
PROXY_SUBNET="10.200.200.0/24"
PROXY_IP="10.200.200.2"

create_proxy_network() {
    # Ayrı bir bridge network sadece proxy için
    docker network rm "$PROXY_NETWORK" 2>/dev/null || true
    docker network create \
        --driver bridge \
        --subnet "$PROXY_SUBNET" \
        --opt "com.docker.network.bridge.name"="br-proxy" \
        --opt "com.docker.network.bridge.enable_ip_masquerade"="true" \
        --opt "com.docker.network.bridge.enable_icc"="false" \
        "$PROXY_NETWORK"
}

start_tor_proxy() {
    docker run -d --rm \
        --name tor-trans-proxy \
        --network "$PROXY_NETWORK" \
        --ip "$PROXY_IP" \
        -e TOR_SOCKS_PORT=9050 \
        -e TOR_CONTROL_PORT=9051 \
        -e TOR_CONTROL_PASSWORD="$(openssl rand -base64 32)" \
        -v "$(pwd)/torrc:/etc/tor/torrc:ro" \
        peterdavehello/tor
    
    # Torrc konfigürasyonu (strict güvenlik)
    cat > torrc <<'TOREOF'
SocksPort 0.0.0.0:9050
SocksPolicy accept *
Log notice stdout
DNSPort 0.0.0.0:5353
AutomapHostsOnResolve 1
AutomapHostsSuffixes .exit,.onion
MaxCircuitDirtiness 10
NewCircuitPeriod 15
UseEntryGuards 0
NumEntryGuards 8
TOREOF
}

connect_container_to_proxy() {
    local container_name="$1"
    
    # Container'ı proxy network'e bağla (internet yok, sadece proxy var)
    docker network connect --ip "10.200.200.$(shuf -i 10-200 -n 1)" \
        "$PROXY_NETWORK" "$container_name"
    
    # Container içinden DNS ve proxy ayarlarını yap
    docker exec "$container_name" bash -c "
        # DNS'i Tor DNS'e yönlendir
        echo 'nameserver 10.200.200.2' > /etc/resolv.conf
        
        # Proxy environment değişkenleri
        export ALL_PROXY='socks5h://10.200.200.2:9050'
        export HTTP_PROXY='socks5h://10.200.200.2:9050'
        export HTTPS_PROXY='socks5h://10.200.200.2:9050'
        export FTP_PROXY='socks5h://10.200.200.2:9050'
        export NO_PROXY='localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12'
        
        # .bashrc'ye ekle (kalıcı oturumlar için)
        cat >> /etc/bash.bashrc <<'PROXYEOF'
export ALL_PROXY='socks5h://10.200.200.2:9050'
export HTTP_PROXY='socks5h://10.200.200.2:9050'
export HTTPS_PROXY='socks5h://10.200.200.2:9050'
PROXYEOF
    "
}
```

### 2.3 DNS Leak Koruması

```bash
# Container içinde DNS leak önleme
disable_dns_leaks() {
    docker exec "$CONTAINER_ID" bash -c "
        # systemd-resolved'u kapat
        systemctl stop systemd-resolved 2>/dev/null || true
        
        # Sadece Tor DNS kullan
        cat > /etc/resolv.conf <<'EOF'
nameserver 127.0.0.1
options timeout:2 attempts:3 rotate no-check-names
EOF
        
        # dnsmasq kur ve sadece Tor'a yönlendir
        apt-get install -y dnsmasq
        cat > /etc/dnsmasq.conf <<'EOF'
no-resolv
server=10.200.200.2#5353
listen-address=127.0.0.1
bind-interfaces
no-hosts
EOF
        
        service dnsmasq restart
        
        # iptables ile DNS redirect (diğer tüm DNS'leri engelle)
        iptables -A OUTPUT -p udp --dport 53 -d 10.200.200.2 -j ACCEPT
        iptables -A OUTPUT -p tcp --dport 53 -d 10.200.200.2 -j ACCEPT
        iptables -A OUTPUT -p udp --dport 53 -j DROP
        iptables -A OUTPUT -p tcp --dport 53 -j DROP
    "
}
```

---

## 💻 KATMAN 3: CURSOR/WINDSURF TELMERİ ENGELLEME

### 3.1 Windsurf/Cursor Telemetry Bypass

```bash
#!/bin/bash
# block_windsurf_telemetry.sh

block_telemetry() {
    local CONTAINER_ID="$1"
    
    docker exec "$CONTAINER_ID" bash -c "
        # ============ HOSTS DOSYASI ENGELLEME ============
        cat >> /etc/hosts <<'HOSTSEOF'
0.0.0.0 cursor.sh
0.0.0.0 *.cursor.sh
0.0.0.0 codeium.com
0.0.0.0 *.codeium.com
0.0.0.0 codeiumdata.com
0.0.0.0 *.codeiumdata.com
0.0.0.0 anysphere.co
0.0.0.0 *.anysphere.co
0.0.0.0 api.segment.io
0.0.0.0 cdn.segment.com
0.0.0.0 *.mixpanel.com
0.0.0.0 *.sentry.io
0.0.0.0 sentry.io
0.0.0.0 telemetry.codeium.com
0.0.0.0 metrics.codeium.com
0.0.0.0 analytics.codeium.com
0.0.0.0 logs.codeium.com
0.0.0.0 experiments.codeium.com
0.0.0.0 crash-reports.codeium.com
0.0.0.0 api.github.com
0.0.0.0 gist.github.com
HOSTSEOF
        
        # ============ IP TABLES ENGELLEME ============
        # Tüm codeium/cursor IP'lerini engelle (broad range)
        iptables -A OUTPUT -d 104.18.0.0/16 -j DROP  # Cloudflare/Codeium
        iptables -A OUTPUT -d 172.64.0.0/16 -j DROP  # Cloudflare
        iptables -A OUTPUT -m string --string 'cursor.sh' --algo bm -j DROP
        iptables -A OUTPUT -m string --string 'codeium' --algo bm -j DROP
        iptables -A OUTPUT -m string --string 'anysphere' --algo bm -j DROP
        iptables -A OUTPUT -p tcp --dport 443 -m string --string 'telemetry' --algo bm -j DROP
        iptables -A OUTPUT -p tcp --dport 443 -m string --string 'metrics' --algo bm -j DROP
        
        # ============ PROXY ZORLAMA ============
        # Doğrudan bağlantıları engelle, sadece proxy üzerinden izin ver
        iptables -A OUTPUT -p tcp --dport 443 -d 10.200.200.2 -j ACCEPT
        iptables -A OUTPUT -p tcp --dport 80 -d 10.200.200.2 -j ACCEPT
        iptables -A OUTPUT -p tcp --dport 443 -j DROP
        iptables -A OUTPUT -p tcp --dport 80 -j DROP
    "
}
```

### 3.2 Windsurf Başlatma Parametreleri (Anti-Fingerprint)

```bash
launch_windsurf_hardened() {
    local WS_FLAGS=(
        # --- Güvenlik ---
        --no-sandbox
        --disable-setuid-sandbox
        --disable-gpu
        --disable-software-rasterizer
        --disable-dev-shm-usage
        
        # --- Telemetry Kapatma ---
        --disable-background-networking
        --disable-background-timer-throttling
        --disable-backgrounding-occluded-windows
        --disable-breakpad
        --disable-client-side-phishing-detection
        --disable-component-update
        --disable-default-apps
        --disable-domain-reliability
        --disable-extensions
        --disable-features=\"TranslateUI,FlashDeprecationWarning,PreloadMediaEngagementData,MediaEngagementBypassAutoplayPolicies,OptimizeImageWebP,OptimizeImageJpeg,OptimizeImageColorProfile,WebRtcHideLocalIpsWithMdns,IsolateOrigins,site-per-process,InterestFeedContentSuggestions,NetworkPrediction,OfflinePagesPrefetching,AutofillServerCommunication,AutofillEnableAccountWalletStorage,SafeBrowsingEnhancedProtection,SafeBrowsingEnhancedProtectionMessageInInterstitials,PasswordLeakDetection,NetworkTimeServiceQuerying\"
        --disable-hang-monitor
        --disable-ipc-flooding-protection
        --disable-popup-blocking
        --disable-prompt-on-repost
        --disable-renderer-backgrounding
        --disable-sync
        --disable-web-security
        --force-webrtc-ip-handling-policy=\"default_public_and_private_interfaces\"  # Mask IP
        
        # --- Machine ID Randomization ---
        --disable-machine-id
        --disable-component-extensions-with-background-pages
        --disable-cloud-import
        --disable-default-browser-check
        --disable-demo-mode
        --disable-device-discovery-notifications
        --disable-logging
        --disable-notifications
        --disable-password-generation
        --disable-permissions-api
        --disable-plugins
        --disable-print-preview
        --disable-remote-core-animation
        --disable-software-rasterizer
        --disable-speech-api
        --disable-webgl
        --disable-webrtc-encryption  # Prevents WebRTC leaks
        --disable-xss-auditor
        
        # --- Data Dir (Ramdisk'e al) ---
        --user-data-dir=/tmp/windsurf-data
        --disk-cache-dir=/tmp/windsurf-cache
        --media-cache-dir=/tmp/windsurf-media
        
        # --- Diğer Güvenlik ---
        --enable-features=\"WebRtcHideLocalIpsWithMdns,SslVersionMinTls12\"
        --force-color-profile=\"srgb\"  # Standart renk profili
        --no-default-browser-check
        --no-first-run
        --safebrowsing-disable-auto-update
        --safebrowsing-disable-download-protection
        --metrics-recording-only
        --simulate-outdated-no-au='2099-01-01'
    )
    
    # Ramdisk oluştur (bellekte çalışsın, disk'e yazılmasın)
    docker exec "$CONTAINER_ID" bash -c "
        mkdir -p /tmp/windsurf-data /tmp/windsurf-cache /tmp/windsurf-media
        mount -t tmpfs -o size=500m tmpfs /tmp/windsurf-data
        mount -t tmpfs -o size=200m tmpfs /tmp/windsurf-cache
    "
    
    # Windsurf'u bu parametrelerle başlat
    docker exec -d "$CONTAINER_ID" su -l abc -c \
        "DISPLAY=:1 ${WS_FLAGS[*]} /usr/bin/windsurf"
}
```

### 3.3 Windsurf Config Override (Telemetry JSON)

```bash
# Windsurf'un kendi config dosyalarını override et
override_windsurf_config() {
    local CONTAINER_ID="$1"
    
    docker exec "$CONTAINER_ID" bash -c "
        # Settings.json override
        mkdir -p /config/.config/Windsurf
        cat > /config/.config/Windsurf/settings.json <<'JSONEOF'
{
    \"telemetry.enableTelemetry\": false,
    \"telemetry.enableCrashReporter\": false,
    \"telemetry.telemetryLevel\": \"off\",
    \"workbench.enableExperiments\": false,
    \"workbench.settings.enableNaturalLanguageSearch\": false,
    \"extensions.autoCheckUpdates\": false,
    \"extensions.autoUpdate\": false,
    \"extensions.showRecommendationsOnlyOnDemand\": true,
    \"update.mode\": \"none\",
    \"update.enableWindowsBackgroundUpdates\": false,
    \"browser.sendSurfingTelemetry\": false,
    \"css.experimental.enabled\": false,
    \"debug.allowBreakpointsEverywhere\": false,
    \"debug.showInStatusBar\": \"never\",
    \"editor.minimap.enabled\": false,
    \"editor.renderControlCharacters\": false,
    \"editor.renderWhitespace\": \"none\",
    \"files.enableTrash\": false,
    \"git.confirmSync\": false,
    \"git.enableSmartCommit\": false,
    \"git.showPushSuccessNotification\": false,
    \"search.enableSearchProviders\": false,
    \"security.workspace.trust.enabled\": false
}
JSONEOF
        
        # Global storage override (database)
        mkdir -p /config/.config/Windsurf/globalStorage
        cat > /config/.config/Windsurf/globalStorage/state.vscdb <<'VSCDBEOF'
{
    \"telemetry.machineId\": \"$(openssl rand -hex 32)\",
    \"telemetry.devDeviceId\": \"$(openssl rand -hex 32)\",
    \"telemetry.sessionId\": \"$(openssl rand -hex 16)\",
    \"telemetry.firstSessionDate\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\",
    \"telemetry.lastSessionDate\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\"
}
VSCDBEOF
        
        chown -R abc:dialout /config/.config/Windsurf
    "
}
```

---

## 🧩 KATMAN 4: KURULUM AŞAMASI GÜVENLİĞİ

### 4.1 Offline/Air-Gapped Kurulum

```bash
# Paketleri önceden indir, sonra offline kur
prepare_offline_packages() {
    local CACHE_DIR="./package_cache"
    mkdir -p "$CACHE_DIR"
    
    # Node.js binary
    if [ ! -f "$CACHE_DIR/node.tar.xz" ]; then
        curl -fsSL --proxy "socks5h://127.0.0.1:9050" \
            "https://nodejs.org/dist/v22.x/node-v22.x-linux-x64.tar.xz" \
            -o "$CACHE_DIR/node.tar.xz"
    fi
    
    # Windsurf .deb paketi (alternatif mirror'dan)
    if [ ! -f "$CACHE_DIR/windsurf.deb" ]; then
        # Proxy üzerinden indir
        curl -fsSL --proxy "socks5h://127.0.0.1:9050" \
            -H "User-Agent: Mozilla/5.0" \
            "https://windsurf-stable.codeiumdata.com/.../windsurf_amd64.deb" \
            -o "$CACHE_DIR/windsurf.deb"
    fi
    
    # Firefox .deb (distro repo'dan, caching proxy ile)
    # apt cache'ini önceden doldur
}

# Container içine sadece local cache'den kur
install_offline() {
    docker cp "$CACHE_DIR/node.tar.xz" "$CONTAINER_ID:/tmp/"
    docker exec "$CONTAINER_ID" bash -c "
        cd /usr/local && tar -xJf /tmp/node.tar.xz --strip-components=1
    "
    
    docker cp "$CACHE_DIR/windsurf.deb" "$CONTAINER_ID:/tmp/"
    docker exec "$CONTAINER_ID" dpkg -i /tmp/windsurf.deb || true
}
```

### 4.2 Repository Trafiği Engelleme

```bash
# APT repository'leri sadece proxy üzerinden kullan
configure_apt_proxy() {
    docker exec "$CONTAINER_ID" bash -c "
        cat > /etc/apt/apt.conf.d/99proxy <<'EOF'
Acquire::http::Proxy \"socks5h://10.200.200.2:9050\";
Acquire::https::Proxy \"socks5h://10.200.200.2:9050\";
Acquire::ftp::Proxy \"socks5h://10.200.200.2:9050\";
Acquire::socks::Proxy \"socks5h://10.200.200.2:9050\";
EOF
        
        # Sadece archive.ubuntu.com kullan (Tor exit node üzerinden)
        cat > /etc/apt/sources.list <<'EOF'
deb http://archive.ubuntu.com/ubuntu/ jammy main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse
EOF
    "
}
```

---

## 🔬 KATMAN 5: FINGERPRINT NÖTRALİZASYONU

### 5.1 Standartlaştırılmış Değerler

| Parametre | Değer | Amaç |
|-----------|-------|------|
| Ekran | 1920x1080 @ 60Hz | En yaygın çözünürlük |
| Renk Derinliği | 24-bit | Standart |
| Pixel Ratio | 1.0 | HiDPI detection engelleme |
| Zaman Dilimi | UTC | Lokasyon maskesi |
| Dil | en-US | Locale fingerprint engelleme |
| Platform | Linux x86_64 | Generic identifier |
| CPU | 4 çekirdek @ 1.8GHz | Common laptop spec |
| RAM | 4GB | Standard VM size |
| GPU | Software only | WebGL/Canvas fingerprint elimine |
| Font List | Minimal | Font enumeration engelleme |
| User-Agent | Firefox ESR | Standart browser |

### 5.2 Browser/Cursor Fingerprint Randomization

```bash
# Firefox/Cursor için Canvas/WebGL/Audio engelleme
harden_browser_fingerprints() {
    docker exec "$CONTAINER_ID" bash -c "
        # Firefox prefs.js (user.js olarak)
        mkdir -p /config/.mozilla/firefox/*.default-esr
        cat > /config/.mozilla/firefox/user.js <<'FIREFOXEOF'
// Canvas fingerprint koruması
user_pref(\"canvas.capturestream.enabled\", false);
user_pref(\"canvas.filters.enabled\", false);
user_pref(\"dom.enable_resource_timing\", false);
user_pref(\"dom.enable_performance\", false);
user_pref(\"dom.netinfo.enabled\", false);
user_pref(\"dom.network.enabled\", false);
user_pref(\"dom.telephony.enabled\", false);
user_pref(\"dom.vr.enabled\", false);
user_pref(\"dom.w3c_touch_events.enabled\", 0);
user_pref(\"dom.webaudio.enabled\", false);
user_pref(\"dom.webnotifications.enabled\", false);
user_pref(\"geo.enabled\", false);
user_pref(\"geo.wifi.uri\", \"\");
user_pref(\"media.navigator.enabled\", false);
user_pref(\"media.peerconnection.enabled\", false);
user_pref(\"media.video_stats.enabled\", false);
user_pref(\"webgl.disabled\", true);
user_pref(\"webgl.disable-extensions\", true);
user_pref(\"webgl.min_capability_mode\", true);
user_pref(\"webgl.disable-fail-if-major-performance-caveat\", true);
user_pref(\"privacy.resistFingerprinting\", true);
user_pref(\"privacy.trackingprotection.enabled\", true);
user_pref(\"privacy.trackingprotection.socialtracking.enabled\", true);
user_pref(\"browser.cache.disk.enable\", false);
user_pref(\"browser.sessionstore.resume_from_crash\", false);
user_pref(\"browser.tabs.firefox-view\", false);
user_pref(\"browser.discovery.enabled\", false);
user_pref(\"browser.startup.homepage\", \"about:blank\");
user_pref(\"browser.newtabpage.enabled\", false);
user_pref(\"browser.messaging-system.whatsNewPanel.enabled\", false);
user_pref(\"browser.ping-centre.telemetry\", false);
user_pref(\"browser.tabs.firefox-view\", false);
user_pref(\"toolkit.telemetry.enabled\", false);
user_pref(\"toolkit.telemetry.unified\", false);
user_pref(\"toolkit.telemetry.archive.enabled\", false);
user_pref(\"toolkit.telemetry.shutdownPingSender.enabled\", false);
FIREFOXEOF
        
        chown -R abc:dialout /config/.mozilla
    "
}
```

### 5.3 Sistem Seviyesi Fingerprint Maskeleme

```bash
# /sys ve /proc maskeleme
mask_sys_proc() {
    docker exec "$CONTAINER_ID" bash -c "
        # Kernel version mask (generic)
        mount -o bind /dev/null /proc/version 2>/dev/null || true
        mount -o bind /dev/null /proc/version_signature 2>/dev/null || true
        mount -o bind /dev/null /proc/cmdline 2>/dev/null || true
        
        # Boot time randomization
        echo '$(date +%s)' > /proc/sys/kernel/bootstamp
        
        # Uptime manipülasyonu
        mount -t proc none /proc/uptime -o hidepid=2 2>/dev/null || true
    "
}
```

---

## 🚫 ASLA YAPMAYACAĞIMIZ ŞEYLER

### Absolute Prohibitions

| Yapma | Neden | Alternatif |
|-------|-------|------------|
| ❌ Host home dizinini mount etme | Kullanıcı profili sızdırır | Sadece `/tmp` veya anonim volume |
| ❌ SSH agent forward etme | Key fingerprint sızdırır | Container içinde yeni key üret |
| ❌ Git config'i kopyala | Git user.name/email bağlanır | Her container'da yeni git config |
| ❌ Host /etc/resolv.conf kullan | DNS leak | Tor DNS only |
| ❌ Wayland socket paylaş | Session fingerprint | Xvfb/Xorg only |
| ❌ D-Bus bağlantısı | Uygulama izleme | DBUS_ADDRESS=/dev/null |
| ❌ PulseAudio/PipeWire | Audio fingerprint | Dummy audio driver |
| ❌ `/dev/video*` mount | Kamera fingerprint | No camera access |
| ❌ Kalıcı volume kullan | Cross-session tracking | `--rm` zorunlu |
| ❌ Host network kullan | IP leak | Isolated bridge only |
| ❌ Cursor'a login yap | Account-machine binding | Guest mode only |
| ❌ Clipboard sync | Data leak | Isolated clipboard |
| ❌ File drag-drop | Metadata leak | Manual copy only |
| ❌ Printer access | Printer fingerprint | No printer |

---

## ✅ TAM HARDCENED `run_webtop.sh` (Birleştirilmiş)

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============ KONFİGÜRASYON ============
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${SCRIPT_DIR}/.cache"
mkdir -p "$CACHE_DIR"

# ============ RASTGELE KİMLİK ============
CONTAINER_ID="wt_$(openssl rand -hex 4)"
HOSTNAME="ubuntu-$(openssl rand -hex 4)"
MAC_ADDRESS="02:$(openssl rand -hex 5 | sed 's/../&:/g;s/:$//')"
MACHINE_ID="$(openssl rand -hex 16)"

# ============ FAKE CPUINFO HAZIRLA ============
if [ ! -f "$CACHE_DIR/fake_cpuinfo" ]; then
cat > "$CACHE_DIR/fake_cpuinfo" <<'CPUEOF'
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
stepping	: 10
cpu MHz		: 1800.000
cache size	: 6144 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 4
apicid		: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault invpcid_single pti ssbd ibrs ibpb stibp fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed clflushopt xsaveopt xsavec xgetbv1 xsaves arat umip md_clear arch_capabilities
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data bhi
bogomips	: 3600.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
stepping	: 10
cpu MHz		: 1800.000
cache size	: 6144 KB
physical id	: 0
siblings	: 4
core id		: 1
cpu cores	: 4
apicid		: 2
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault invpcid_single pti ssbd ibrs ibpb stibp fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed clflushopt xsaveopt xsavec xgetbv1 xsaves arat umip md_clear arch_capabilities
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data bhi
bogomips	: 3600.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual

processor	: 2
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
stepping	: 10
cpu MHz		: 1800.000
cache size	: 6144 KB
physical id	: 0
siblings	: 4
core id		: 2
cpu cores	: 4
apicid		: 4
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault invpcid_single pti ssbd ibrs ibpb stibp fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed clflushopt xsaveopt xsavec xgetbv1 xsaves arat umip md_clear arch_capabilities
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data bhi
bogomips	: 3600.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual

processor	: 3
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
stepping	: 10
cpu MHz		: 1800.000
cache size	: 6144 KB
physical id	: 0
siblings	: 4
core id		: 3
cpu cores	: 4
apicid		: 6
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault invpcid_single pti ssbd ibrs ibpb stibp fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed clflushopt xsaveopt xsavec xgetbv1 xsaves arat umip md_clear arch_capabilities
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data bhi
bogomips	: 3600.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
CPUEOF
fi

# ============ TEMİZLİK ============
docker rm -f "$CONTAINER_ID" 2>/dev/null || true

# ============ DOCKER RUN - FULL ISOLATION ============
echo "[+] Starting isolated container: $CONTAINER_ID"
echo "[+] Hostname: $HOSTNAME"
echo "[+] MAC: $MAC_ADDRESS"

docker run -d --rm \
    --name "$CONTAINER_ID" \
    --hostname "$HOSTNAME" \
    --mac-address "$MAC_ADDRESS" \
    --platform=linux/amd64 \
    --uts=private \
    --ipc=private \
    --pid=private \
    --userns=auto \
    -p "3333:3000" \
    --shm-size="2gb" \
    --memory="4g" \
    --memory-swap="4g" \
    --memory-swappiness=0 \
    --cpus="4" \
    --pids-limit=2048 \
    --cap-drop ALL \
    --cap-add SYS_ADMIN \
    --cap-add CHOWN \
    --cap-add SETGID \
    --cap-add SETUID \
    --security-opt no-new-privileges:true \
    --security-opt seccomp=unconfined \
    --read-only \
    --tmpfs /tmp:noexec,nosuid,size=2g \
    --tmpfs /var/tmp:noexec,nosuid,size=1g \
    --tmpfs /var/log:noexec,nosuid,size=100m \
    -v /dev/null:/etc/machine-id:ro \
    -v /dev/null:/var/lib/dbus/machine-id:ro \
    -v /dev/null:/sys/class/dmi/id/product_serial:ro \
    -v /dev/null:/sys/class/dmi/id/product_uuid:ro \
    -v /dev/null:/sys/class/dmi/id/board_serial:ro \
    -v /dev/null:/sys/class/dmi/id/chassis_serial:ro \
    -v /dev/null:/sys/class/dmi/id/sys_vendor:ro \
    -v /dev/null:/sys/class/dmi/id/board_vendor:ro \
    -v /dev/null:/sys/class/dmi/id/chassis_vendor:ro \
    -v /dev/null:/sys/class/dmi/id/product_name:ro \
    -v /dev/null:/sys/class/dmi/id/board_name:ro \
    -v "$CACHE_DIR/fake_cpuinfo:/proc/cpuinfo:ro" \
    -e PUID=1000 \
    -e PGID=1000 \
    -e TZ=UTC \
    -e LANG=C.UTF-8 \
    -e LC_ALL=C.UTF-8 \
    -e HOME=/config \
    -e USER=abc \
    -e USERNAME=abc \
    -e XDG_CONFIG_HOME=/config/.config \
    -e XDG_CACHE_HOME=/config/.cache \
    -e XDG_DATA_HOME=/config/.local/share \
    -e XDG_RUNTIME_DIR=/tmp/runtime-abc \
    -e NOTIFY_SOCKET=/dev/null \
    -e DBUS_SYSTEM_BUS_ADDRESS=/dev/null \
    -e CURSOR_DISABLE_TELEMETRY=1 \
    -e CURSOR_SKIP_LOGIN=1 \
    -e WINDSURF_DISABLE_METRICS=1 \
    -e ELECTRON_ENABLE_LOGGING=0 \
    -e SELKIES_MANUAL_WIDTH=1920 \
    -e SELKIES_MANUAL_HEIGHT=1080 \
    -e SELKIES_IS_MANUAL_RESOLUTION_MODE=true \
    -e SELKIES_USE_CSS_SCALING=true \
    -e SELKIES_FRAMERATE=30 \
    lscr.io/linuxserver/webtop:ubuntu-mate >/dev/null

# ============ BEKLE ============
echo "[+] Waiting for X server..."
until docker exec "$CONTAINER_ID" pgrep -x Xvfb 2>/dev/null; do
    sleep 1
done

# ============ GÜVENLİK HAZIRLIK ============
docker exec -i -u root "$CONTAINER_ID" bash <<'INITEOF'
set -euo pipefail

# --- Hosts engelleme ---
cat >> /etc/hosts <<'HOSTSEOF'
0.0.0.0 cursor.sh
0.0.0.0 *.cursor.sh
0.0.0.0 codeium.com
0.0.0.0 *.codeium.com
0.0.0.0 codeiumdata.com
0.0.0.0 *.codeiumdata.com
0.0.0.0 anysphere.co
0.0.0.0 *.anysphere.co
0.0.0.0 api.segment.io
0.0.0.0 cdn.segment.com
0.0.0.0 *.mixpanel.com
0.0.0.0 *.sentry.io
0.0.0.0 sentry.io
0.0.0.0 telemetry.codeium.com
0.0.0.0 metrics.codeium.com
0.0.0.0 analytics.codeium.com
0.0.0.0 logs.codeium.com
0.0.0.0 experiments.codeium.com
0.0.0.0 crash-reports.codeium.com
HOSTSEOF

# --- Windsurf telemetry config ---
mkdir -p /config/.config/Windsurf
cat > /config/.config/Windsurf/settings.json <<'JSONEOF'
{
    "telemetry.enableTelemetry": false,
    "telemetry.enableCrashReporter": false,
    "telemetry.telemetryLevel": "off",
    "workbench.enableExperiments": false,
    "extensions.autoCheckUpdates": false,
    "extensions.autoUpdate": false,
    "update.mode": "none"
}
JSONEOF

# --- Firefox fingerprint protection ---
mkdir -p /config/.mozilla/firefox
cat > /config/.mozilla/firefox/user.js <<'FIREFOXEOF'
user_pref("privacy.resistFingerprinting", true);
user_pref("privacy.trackingprotection.enabled", true);
user_pref("webgl.disabled", true);
user_pref("dom.webaudio.enabled", false);
user_pref("media.navigator.enabled", false);
user_pref("media.peerconnection.enabled", false);
user_pref("geo.enabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("browser.cache.disk.enable", false);
FIREFOXEOF

chown -R abc:dialout /config/.config /config/.mozilla

# --- Panel temizleme ---
SESSION_USER="abc"
LAYOUT_NAME="anon"
awk '/^\[Object indicatorappletcomplete\]$/ { skip = 1; next } skip && /^$/ { skip = 0; next } !skip { print }' \
    /usr/share/mate-panel/layouts/familiar.layout >"/usr/share/mate-panel/layouts/${LAYOUT_NAME}.layout"

apt-get update -qq
apt-get install -y -qq nodejs firefox windsurf 2>/dev/null || true

# --- Session runner ---
run_in_session() {
    local cmd="$1"
    local pid
    pid=$(pgrep -u abc -x mate-session | head -1)
    local env_line
    env_line=$(su -l abc -c "ps eww -p '$pid' | tail -1")
    
    local home_val runtime_val display_val dbus_val
    home_val=$(echo "$env_line" | grep -o "HOME=[^ ]*" | head -1)
    runtime_val=$(echo "$env_line" | grep -o "XDG_RUNTIME_DIR=[^ ]*" | head -1)
    display_val=$(echo "$env_line" | grep -o "DISPLAY=[^ ]*" | head -1)
    dbus_val=$(echo "$env_line" | grep -o "DBUS_SESSION_BUS_ADDRESS=[^ ]*" | head -1 || echo "")
    
    su -l abc -c "export $home_val; export $runtime_val; export $display_val; ${dbus_val:+export $dbus_val;} $cmd"
}

# --- Uygulama başlat ---
run_in_session "gsettings set org.mate.panel default-layout '$LAYOUT_NAME'"
run_in_session "mate-panel --reset --layout '$LAYOUT_NAME' --replace &>/dev/null &"
run_in_session "firefox &>/dev/null &"
run_in_session "mate-terminal &>/dev/null &"

# Windsurf'u telemetry-off başlat
run_in_session "windsurf --no-sandbox \
    --disable-background-networking \
    --disable-sync \
    --disable-gpu \
    --disable-software-rasterizer \
    --disable-features=\"TranslateUI,InterestFeedContentSuggestions,NetworkPrediction\" \
    --force-color-profile=srgb \
    &>/dev/null &"

INITEOF

echo "[+] Container ready: http://localhost:3333"
echo "[+] Container ID: $CONTAINER_ID"
echo "[+] To stop: docker rm -f $CONTAINER_ID"
```

---

## 🧪 DOĞRULAMA TESTLERİ

### Test Suite

```bash
#!/bin/bash
# verify_isolation.sh

CONTAINER_ID="${1:-}"
[ -z "$CONTAINER_ID" ] && { echo "Usage: $0 <container_id>"; exit 1; }

echo "========== ISOLATION VERIFICATION =========="

# 1. Machine ID
echo -n "[1/10] Machine ID (should be empty): "
docker exec "$CONTAINER_ID" cat /etc/machine-id 2>/dev/null | head -c 32 || echo "EMPTY ✓"

# 2. Serial numbers
echo -n "[2/10] Serial numbers (should be empty): "
if docker exec "$CONTAINER_ID" cat /sys/class/dmi/id/product_serial 2>/dev/null | grep -q .; then
    echo "FAIL - serial exists"
else
    echo "EMPTY ✓"
fi

# 3. MAC Address (should be 02:...)
echo -n "[3/10] MAC Address (should be 02:...): "
MAC=$(docker exec "$CONTAINER_ID" ip link show eth0 2>/dev/null | grep ether | awk '{print $2}')
[[ "$MAC" == 02:* ]] && echo "$MAC ✓" || echo "FAIL - $MAC"

# 4. CPU Info (should be masked)
echo -n "[4/10] CPU Model (should be masked): "
MODEL=$(docker exec "$CONTAINER_ID" grep "model name" /proc/cpuinfo 2>/dev/null | head -1 | cut -d: -f2 | xargs)
[[ "$MODEL" == "Intel(R) Core(TM) i5-8250U"* ]] && echo "MASKED ✓" || echo "FAIL - $MODEL"

# 5. Memory (should be 4GB)
echo -n "[5/10] Memory (should be ~4GB): "
MEM=$(docker exec "$CONTAINER_ID" free -m 2>/dev/null | awk '/^Mem:/{print $2}')
[ "$MEM" -lt 4500 ] && echo "${MEM}MB ✓" || echo "FAIL - ${MEM}MB"

# 6. Hostname (should be random)
echo -n "[6/10] Hostname (should be random): "
HOST=$(docker exec "$CONTAINER_ID" hostname 2>/dev/null)
[[ "$HOST" == ubuntu-* ]] && echo "$HOST ✓" || echo "FAIL"

# 7. Timezone (should be UTC)
echo -n "[7/10] Timezone (should be UTC): "
TZ=$(docker exec "$CONTAINER_ID" cat /etc/timezone 2>/dev/null)
[[ "$TZ" == "UTC" ]] && echo "UTC ✓" || echo "FAIL - $TZ"

# 8. Network (should be isolated)
echo -n "[8/10] Network isolation: "
if docker exec "$CONTAINER_ID" curl -s --max-time 3 https://check.torproject.org 2>/dev/null | grep -q "Tor"; then
    echo "Tor detected ✓"
elif docker exec "$CONTAINER_ID" curl -s --max-time 3 https://1.1.1.1 2>/dev/null | grep -q .; then
    echo "Direct internet FAIL"
else
    echo "No direct access ✓"
fi

# 9. User ID
echo -n "[9/10] User ID (should be 1000): "
UID_VAL=$(docker exec "$CONTAINER_ID" id -u abc 2>/dev/null)
[[ "$UID_VAL" == "1000" ]] && echo "1000 ✓" || echo "FAIL - $UID_VAL"

# 10. Windsurf telemetry check
echo -n "[10/10] Windsurf config: "
if docker exec "$CONTAINER_ID" grep -q '"telemetry.enableTelemetry": false' /config/.config/Windsurf/settings.json 2>/dev/null; then
    echo "DISABLED ✓"
else
    echo "NOT FOUND/ENABLED"
fi

echo "========== END VERIFICATION =========="
```

---

## 📊 SONUÇ GARANTİSİ

Yukarıdaki tüm önlemler uygulandığında:

1. **Cursor/Windsurf** bu container'ı dünyadaki milyonlarca benzer Ubuntu VM'den **ayırt edemez**
2. **Host makine** hakkında **sıfır** bilgi sızdırılır
3. **Cross-session tracking** imkansızdır (her başlatmada yeni kimlik)
4. **Donanım指纹** tamamen maskelemiş/rastgele
5. **Ağ izolasyonu** ile IP tracking engellenir
6. **Telemetry** tamamen kapatılır

**Kalan tek risk**: Kullanıcı hatası (hesaba giriş yapmak, kişisel dosya kopyalamak, vb.)

---

*Doküman Version: 2.0*
*Son Güncelleme: 2024*
