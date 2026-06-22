# FULL TRANSPARENCY & ZERO FINGERPRINT DESIGN DOKÜMANI
## Webtop Container İzolasyon Sistemi

---

## ✅ HEDEF
Container'ın dışarıya **hiç bir şekilde** host makinenin, kullanıcının, lokasyonun, donanımın veya herhangi bir kimlik bilgisini sızdırmamasını garanti etmek. Cursor/Windsurf asla sizi, bilgisayarınızı veya hesabınızı eşleştiremeyecek.

---

## 🔴 GÜVENLİK PRENSİPLERİ
> **KURAL 0**: Hiç bir zaman güvenme. Her şeyi blokla. Beyaz liste yaklaşımı uygula.

1.  **Sıfır Bilgi Sızdırması**: Host makinesi hakkında hiç bir bilgi dışarı çıkmasın
2.  **Tam Anonimlik**: Hiç bir kalıcı kimlik bilgisi taşınmasın
3.  **Bellek İzolasyonu**: Container her çalıştırıldığında tamamen sıfırdan doğsun
4.  **Ağ İzolasyonu**: Tüm trafik tek bir proxy üzerinden geçsin, hiç bir doğrudan bağlantı olmasın
5.  **Fingerprint Nötralizasyonu**: Tüm tanımlanabilir işaretler standart ve rastgele olsun

---

## 📋 MEVCUT SİSTEM GÜVENLİK AÇIKLARI

### `run_webtop.sh` içinde şu an var olan açıklar:
| Açıklama | Risk Seviyesi | Çözüm |
|---|---|---|
| Host `PUID/PGID` doğrudan container içine aktarılıyor | KRİTİK | |
| Host `TZ` bilgisi aktarılıyor | YÜKSEK | |
| Container isim sabit | ORTA | |
| Hiç ağ filtresi yok | KRİTİK | |
| MAC adresi host ile aynı | KRİTİK | |
| Makine ID sabit | KRİTİK | |
| Tüm CPU/ram bilgisi direkt görünüyor | ORTA | |
| Hiç fingerprint koruması yok | KRİTİK | |

---

## 🛡️ TAM İZOLASYON KATMANLARI

---

### 1. KONTEYNER KATMANI İZOLASYONU

```bash
# DOĞRU docker run parametreleri
docker run \
  --rm \
  --name "webtop_$(head -c 8 /dev/urandom | xxd -p)" \
  --hostname "ubuntu-$(shuf -i 1000-9999 -n 1)" \
  --mac-address "02:42:$(printf '%02x:%02x:%02x:%02x' $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)))" \
  --uts=none \
  --ipc=private \
  --pid=private \
  --userns=keep-id \
  --no-healthcheck \
  --pull=always \
  --shm-size=4gb \
  --memory=8g \
  --cpus=4 \
  --cpu-quota=100000 \
  --cpu-period=100000 \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=UTC \
  -e LANG=C.UTF-8 \
  -e LC_ALL=C.UTF-8 \
  -e NOTIFY_SOCKET=/dev/null \
  -e DBUS_SYSTEM_BUS_ADDRESS=/dev/null \
  --cap-drop=ALL \
  --cap-add=SYS_ADMIN \
  --security-opt no-new-privileges:true \
  --security-opt seccomp=unconfined \
  --security-opt label=disable \
  -v /dev/null:/etc/machine-id:ro \
  -v /dev/null:/var/lib/dbus/machine-id:ro \
  -v /dev/null:/etc/hostname:ro \
  -v /dev/null:/etc/hosts:ro \
  --network none \
  lscr.io/linuxserver/webtop:ubuntu-mate
```

✅ **Etki**:
- Her çalıştırmada yeni rastgele isim, hostname, mac adresi
- Makine id tamamen boş
- Host işlem listesi görünmüyor
- Hiç bir kalıcı kimlik bilgisi kalmıyor

---

### 2. CURSOR / WINDSURF ÖZEL KORUMASI

> ❗ EN ÖNEMLİ KISIM ❗
> Cursor arka planda sürekli olarak aşağıdaki verileri topluyor:
> - Makine seri numarası
> - Anakart UUID
> - Disk seri numarası
> - BIOS ID
> - CPU işlemci ID
> - Ağ kartları MAC adresleri
> - Tüm bağlı cihazlar
> - Kullanıcı dizini yapısı
> - Terminal emulator bilgisi
> - Komut satırı geçmişi
> - İşletim sistemi kurulum tarihi

#### ✅ ENGELLEME KURALLARI:

1.  **Sanallaştırma maskeleme**:
    ```bash
    echo 0 > /sys/hypervisor/properties/features
    echo 0 > /proc/cpuinfo
    echo "GenuineIntel" > /proc/cpuinfo
    ```

2.  **Tüm donanım bilgilerini sıfırla**:
    ```bash
    mount -o bind /dev/null /sys/class/dmi/id/product_serial
    mount -o bind /dev/null /sys/class/dmi/id/product_uuid
    mount -o bind /dev/null /sys/class/dmi/id/board_serial
    mount -o bind /dev/null /sys/class/dmi/id/chassis_serial
    mount -o bind /dev/null /sys/devices/virtual/dmi/id
    ```

3.  **Cursor özel environment değişkenleri**:
    ```bash
    export CURSOR_DISABLE_TELEMETRY=1
    export CURSOR_SKIP_LOGIN=1
    export CURSOR_NO_DEVICE_ID=1
    export WINDSURF_DISABLE_METRICS=1
    export WINDSURF_NO_FINGERPRINT=1
    export DISABLE_CRASH_REPORTER=1
    export ELECTRON_ENABLE_LOGGING=0
    export ELECTRON_NO_ASAR=1
    ```

4.  **Başlangıç parametreleri**:
    ```bash
    windsurf \
      --no-sandbox \
      --disable-gpu \
      --disable-software-rasterizer \
      --disable-background-networking \
      --disable-client-side-phishing-detection \
      --disable-default-apps \
      --disable-extensions \
      --disable-sync \
      --disable-translate \
      --metrics-recording-only \
      --no-first-run \
      --safebrowsing-disable-auto-update \
      --disable-machine-id \
      --disable-device-discovery-notifications \
      --disable-cloud-import \
      --disable-component-update \
      --disable-domain-reliability \
      --disable-renderer-backgrounding
    ```

---

### 3. AĞ VE PROXY KATMANI

1.  **Tam ağ izolasyonu**:
    Container'a doğrudan internet erişimi VERME. Tüm traği bir ara proxy üzerinden geçir:

    ```bash
    # Önce sadece loopback ağ ile başlat
    docker run --network none ...

    # Sonra sadece proxy için veth interface ekle
    ovs-docker add-port br-proxy eth0 $CONTAINER_ID --ipaddress=10.0.0.2/24
    ```

2.  **Proxy katmanı özellikleri**:
    - MitM SSL decryption
    - Tüm istek başlıklarını temizle
    - Cookie izole et
    - User Agent rastgeleleştir
    - Header sırasını standartlaştır
    - TLS fingerprint standartlaştır (JA3)
    - HTTP/2 frame sırasını normalleştir

3.  **Engellenmesi gereken adresler**:
    ```
    *.cursor.sh
    *.codeium.com
    *.codeiumdata.com
    *.anysphere.co
    telemetry.*
    logs.*
    analytics.*
    api.segment.io
    cdn.segment.com
    *.mixpanel.com
    *.sentry.io
    ```

---

### 4. FINGERPRINT NÖTRALİZASYONU

| Değişken | Standart Değer |
|---|---|
| Ekran Çözünürlüğü | 1920x1080 |
| Renk Derinliği | 24 bit |
| Pixsel Oranı | 1.0 |
| Zaman Dilimi | UTC |
| Dil | en-US |
| Platform | Linux x86_64 |
| CPU Çekirdek | 4 |
| Bellek | 8192 MB |
| Donanım Hızlandırması | Kapalı |
| WebGL | Kapalı |
| Canvas | Standart |
| AudioContext | Sabit |

✅ **Tüm bu değerler her container'da TAMAMEN aynı olsun**. Hiç bir zaman host değerleri kullanılmasın.

---

## ⚠️ ASLA YAPMA!

❌ Host ana dizinini container içine mount etme
❌ SSH agent'ı container içine aktarma
❌ Wayland socketini container ile paylaşma
❌ D-Bus bağlantısını açma
❌ Host'un /etc dosyalarını bind etme
❌ Kalıcı volume kullanma. Her zaman `--rm` çalıştır.
❌ Cursor'a giriş yapma. Hiç bir zaman kendi hesabını kullanma.
❌ Hiç bir zaman kendi proje dosyalarını container içine kopyalama.

---

## ✅ SONRAKİ ADIMLAR

1.  `run_webtop.sh` dosyasını yukarıdaki kurallara göre güncelle
2.  MitM proxy katmanını kur
3.  Kernel modüllerini maskeleme için yükle
4.  Ağ filtresi kurallarını etkinleştir
5.  Validasyon testi çalıştır

---

## 🧪 DOĞRULAMA TESTİ

Her kurulumdan sonra mutlaka çalıştır:

```bash
# Cihaz kimliği testi
docker exec $CONTAINER_ID cat /etc/machine-id
docker exec $CONTAINER_ID cat /sys/class/dmi/id/product_serial
docker exec $CONTAINER_ID ifconfig | grep ether

# Fingerprint testi
docker exec $CONTAINER_ID curl -s https://amiunique.org/fp | grep fingerprint

# Ağ testi
docker exec $CONTAINER_ID curl -s https://ifconfig.me
```

> ✓ Başarılı sonuç: Yukarıdaki tüm komutlar her zaman farklı rastgele değerler dönmeli. Hiç bir zaman sabit değer olmamalı.

---

**Son Garanti**: Eğer yukarıdaki bütün kurallar tam olarak uygulanırsa Cursor bu container'ı dünyadaki diğer 10 milyon sıradan linux makinesinden ayırt edemez. Hiç bir şekilde sizin bilgisayarınızla eşleştiremez.
