# vpn_proxy.sh — Tek VPN + Proxy Yöneticisi

VPN açıkken SSH proxy tünellerini otomatik kurar, VPN kapanınca kapatır.
`vpn_caffeinate_manager.sh`, `proxy_login.sh`, `proxy_common.sh` ve dört
`connect_*.sh` scriptinin yaptığı işi **tek scriptte** toplar.

> Giriş noktası **depo kökünde**: `./vpn_proxy.sh`
> Ayrıntılar ve güncelleme rehberi: `docs/vpn_proxy.md` (bu dosya)

## ⚠️ GÜNCELLEME REHBERİ — NEREDE NE DEĞİŞTİRİLECEK

Bu bölümü, bu sistemdeki bir şeyi değiştirmeden önce oku.

### Tek doğru dosyalar

| Ne değişecek | GÜNCELLENECEK DOSYA | Asla güncelleme |
|---|---|---|
| VPN algılama, tünel, menü, daemon, port açma/kapama | `vpn_proxy.sh` (depo kökü) | `legacy/v1/*` |
| **Hedef IP listesi** (VPN DHCP kiraları) | `~/.config/sunumlar/hosts.env` | `vpn_proxy.sh` içindeki IP sabiti |
| OpenCode model senkronizasyonu | `sync_proxy_models.js` (depo kökü) | `legacy/v1/sync_proxy_models.js` |
| Bu dokümantasyon | `docs/vpn_proxy.md` | — |

### Değişiklik yaparken zorunlu kurallar

1. **`legacy/v1/`'e dokunma.** 8 eski script orada arşiv duruyor. Değişiklik
   gerekiyorsa **her zaman** `vpn_proxy.sh`'e yap. `legacy/v1/` yalnızca
   "eskiden ne vardı" diye okunur.
2. **Yeni dosya eklerken köke ekle**, `vpn_proxy/bin/` gibi alt klasör açma.
   Giriş noktası kökte tek dosya olarak durmalı; kökteki diğer tunnel
   scriptleriyle (`comfuitunnel.sh`, `tunnel_ollama.sh`, `openclow_tunnel.sh`)
   aynı düzende olsun.
3. **`sync_proxy_models.js` kökte yan yana durur.** `vpn_proxy.sh` onu
   `SCRIPT_DIR` üzerinden bulur; konumunu değiştirirsen `sync_models` menü
   seçeneği kırılır.
4. **Değişiklikten sonra çalıştır:**
   ```bash
   bash -n vpn_proxy.sh                 # sözdizimi
   node --check sync_proxy_models.js    # sözdizimi
   ./vpn_proxy.sh status                # çalışma durumu
   ```
5. **Kullanıcıya/yol panosuna yansıyan bir değişiklik yapıyorsan**, aşağıdaki
   tabloda "Kullanıcıya etkisi" sütununu doldur ve commit mesajında **NEDEN**
   yaz. Sadece "ne" yazmak yeterli değil.

### Değişiklikten sonra kullanıcıya ne söylenmeli

| Yaptığın değişiklik | Kullanıcıya söylenecek |
|---|---|
| `vpn_proxy.sh` mantığı değişti | `./vpn_proxy.sh restart` gerekir (daemon eski kodu çalışıyor) |
| Yeni komut/menü seçeneği eklendi | Menü çıktısı değişti, hangi numara ne yaptığını yaz |
| `sync_proxy_models.js` değişti | Değişiklik varsa **opencode'u yeniden başlat**, model listesi ancak yeniden başlatınca yüklenir |
| Yeni port eklendi | `sync_proxy_models.js` içindeki `PROVIDERS` listesine de eklenmeli |
| Bir hata düzeltildi | Hatanın **belirtisini** ve **kök nedenini** yaz, "düzeltildi" demekle geçme |

### Bu oturumda ne değişti ve NEDEN

| Değişiklik | Neden | Kullanıcıya etkisi |
|---|---|---|
| **Hedef IP artık kodda gömülü değil** | VPN DHCP kiraları çok sık değişiyordu; her değişimde kodu düzenlemek gerekiyordu | `./vpn_proxy.sh 2` ile listeden geçiş; IP eklemek için `hosts.env` |
| `hosts.env` + `hosts` komutu eklendi | Hangi IP'nin ayakta olduğunu görmeden geçiş yapmak zordu | `./vpn_proxy.sh hosts` erişilebilirlik gösterir |
| Tüm scriptler tek pakete toplandı | 8 ayrı script'in her biri kendi VPN/parola mantığını taşıyordu; birinde düzeltme diğerlerinde yoktu | `./vpn_proxy.sh` yeni komut |
| Eski kodlar `legacy/v1/` altına | Eski kod dursun istendi ama karışmasın diye ayrıldı | Yok (arşiv) |
| `local "$1"` → `local "${1:-}"` | `set -u` ile menüden `1` seçilince `line 359: $2: unbound variable` patlıyordu; 8 fonksiyon etkileniyordu | Menü artık hata fırlatmıyor |
| `local` fonksiyon dışında kaldırıldı | `restart` fonksiyon dışı olduğu için `local w=0` hata veriyordu | `restart` çalışıyor |
| `do_start`'a `load_secrets` | Parola yüklenmiyordu → ssh `BatchMode=yes`'e düşüp `Permission denied` veriyordu, tünel hiç açılmıyordu | Tüneller açılıyor |
| `do_start` içinde `refresh_snapshot` | VPN durumu bayat kalıyor, açık VPN "kapalı" sanılıyordu | Açık VPN doğru tanınıyor |
| `stream_log`: `tail -f` → klavye kontrolü | `tail -f` stdin'i tüketiyordu; `q` yazınca menüye dönülmüyordu | Canlı logdan `q` ile menüye dönülüyor |
| `restart` VPN toparlanmasını bekler | `stop` hemen ardından `start` yarış durumu yaratıyordu | `restart` güvenilir |
| İlk çalıştırmada ayar yoksa sihirbaz | "Hangi proxy'leri istediğimi sormalı, direk açmasın" | İlk açılışta sorar |
| `sync_proxy_models.js` köke taşındı | Model listesi tünelle gelir; tünel açılmadan güncellenemiyordu | Menü 6 ile çağrılır |
| `lib/net_fix.sh` **kaldırıldı** | Yerel DNS arızası proxy'leri etkilemiyor (tüneller localhost); sadece teşhis raporluyordu | Yok (kapsam dışıydı) |
| `fetchViaCurl` fallback'i **geri alındı** | Aynı sebep; localhost tünelle DNS'e ihtiyaç yok | Yok |

## Kullanım

```bash
./vpn_proxy.sh            # menü (açar / kapatır / log / ayarlar)
./vpn_proxy.sh start      # seçili proxy'leri aç + daemon başlat
./vpn_proxy.sh stop       # daemon + tüm tüneller + portları kapat
./vpn_proxy.sh status     # VPN + proxy durumu
./vpn_proxy.sh setup      # hangi proxy'ler / retry ayarı
./vpn_proxy.sh watch      # canlı log akışı
./vpn_proxy.sh restart    # kapat + aç (VPN toparlanmasını bekler)
./vpn_proxy.sh hosts      # hedef makine listesi (IP'ler)
./vpn_proxy.sh 2          # 2. makineyi seç ve bağlan
```

## Menü

```
1) Proxy'leri aç (bağlan + daemon başlat)
2) Proxy'leri kapat (portları da kapat)
3) Durumu göster
4) Canlı log akışı ('q' ile menüye dön)
5) Ayarlar (hangi proxy'ler / retry)
6) OpenCode modellerini güncelle
7) Çıkış
```

## 📌 NOT: Hedef IP nasıl değiştirilir

VPN DHCP kiraları **sık değiştiği** için IP koda gömülü değil. Üç yol var,
hepsi de `10.1.37.223` (mevcut değer) varsayılan olarak kalır.

### 1) Liste dosyası — kalıcı, eklemesi kolay

`~/.config/sunumlar/hosts.env` (ilk çalıştırmada otomatik oluşur):

```
1  10.1.37.223  ubuntu-ana (varsayılan)
2  10.1.37.224  ubuntu-yedek
3  10.1.99.99   ofis-makinesi
```

Biçim: `<no>  <ip>  <açıklama>`

- **Yeni IP eklemek:** dosyayı aç, **sonuna** satır ekle. Numarayı elle yazma —
  sıralama listedeki sıraya göre otomatik yapılır, `#!/` yorum satırları
  atlanır.
- **Silmek:** satırı sil.
- **Açıklamayı değiştirmek:** sadece 3. sütunu düzenle (not tutmak için).
- Dosyaya dokunmadan da her şey çalışır; liste bozuksa 1. satırdaki IP kullanılır.

### 2) Numarayla seç — hızlı geçiş

```bash
./vpn_proxy.sh 2        # 2. makineyi seç VE bağlan (seçim kalıcı kaydedilir)
./vpn_proxy.sh hosts    # listeyi erişilebilirlik durumuyla göster
```

`hosts` çıktısı:

```
  ─────────────────────────────────────────
 → 1) 10.1.37.223     ubuntu-ana     🟢 erişilebilir (0s)
   2) 10.1.37.224     ubuntu-yedek   🔴 erişilemiyor
```

### 3) Ortam değişkeni — tek seferlik, kalıcılığı bozmaz

```bash
PROXY_HOST=10.1.37.224 ./vpn_proxy.sh start
```

### Öncelik sırası

| Sıra | Kaynak | Kalıcı mı? |
|---|---|---|
| 1 | `PROXY_HOST=...` ortam değişkeni | hayır (tek seferlik) |
| 2 | `./vpn_proxy.sh <no>` ile seçim | **evet** |
| 3 | `vpn_proxy.conf` içindeki kayıtlı `HOST` | evet |
| 4 | `hosts.env` 1. satır | evet (dosya) |
| 5 | `vpn_proxy.sh` içindeki `DEFAULT_PROXY_HOST` | — (gömülü yedek) |

**Hiçbiri yoksa mevcut değer (`10.1.37.223`) kullanılır.** Yani listeden
silmek, dosyayı bozmak veya ayarı temizlemek sistemi bozmaz.

> Not: DHCP kiraları sık değiştiği için **birden fazla IP'yi önceden listeye
> yazmak** en pratik yol — VPN açılınca `./vpn_proxy.sh hosts` ile hangisinin
> ayakta olduğunu görüp numarasıyla geçersiniz.

## Kurulum sihirbazı (bir kez)

1. **Hangi proxy'ler** açılsın — `1,2,3` gibi virgülle, ya da `hepsi`
2. **Retry** — koptuğunda otomatik yeniden bağlansın mı (`true`/`false`)
3. **SSH parolası** — bir kez sorulur, `~/.config/sunumlar/secrets.env`
   içine yazılır (chmod 600). Artık hiç sorulmaz.

Proxy sırası:

| # | ad | port |
|---|-----|------|
| 1 | opencode | 6446 |
| 2 | cline | 6447 |
| 3 | kilo | 5380 |
| 4 | antigravity | 4000 |

## Davranış

- **VPN algılama** `vpn_caffeinate_manager.sh` ile aynı mantığı kullanır:
  Tunnelblick (openvpn süreci + utun'da 100.x dışı IP), Tailscale
  (`scutil` Connected + 100.64/10), FortiClient, BlancVPN. VPN arayüzü açık
  olmadan hiçbir bağlantı denenmez.
- **Caffeinate** VPN açıkken çalışır, VPN kapanınca durur.
- **VPN gelince** seçili proxy'ler otomatik kurulur.
- **VPN kapanınca** tüneller kapatılır, portlar serbest bırakılılır.
- **Isınma (warm) aralığı**: 10s → 20s → 40s → 80s → 160s → **240s (4 dk tavan)**.
  Hepsi canlıyken aralık büyür, bir bağlantı kurulunca 10s'ye döner.
- **Pop-up yok**: daemon asla parola sormaz, asla diyalog göstermez.

## Asılı port sorunu

`ssh` bir zamanlar VPN düşünce canlı kalıp portu tutuyordu; port dinliyordu
ama API cevap vermiyordu (bugünkü 6447'in durumu). **Kök neden çözüldü:**

```
-o ServerAliveInterval=15 -o ServerAliveCountMax=3   # VPN düşünce ssh kapanır
-o ExitOnForwardFailure=yes                         # port bağlanamazsa çıkar
```

Ek olarak `free_port` bir port dinliyor ama cevap vermiyorsa yalnızca **o
portunu tutan `ssh` sürecini** öldürür. Başka bir program kullanıyorsa
dokunmaz ve uyarır.

## Retry = false

VPN açıldıktan sonra kurulamayan proxy'ler sürekli yeniden denenmez; tüm
bağlantılar kurulana kadar 4 dakikalık aralıkta beklenir.

## OpenCode neden model göstermiyor?

`~/.config/opencode/opencode.json` bu proxy'leri **localhost** üzerinden
kullanır:

| provider | baseURL |
|---|---|
| clineproxy | `http://localhost:6447/v1` |
| opencodefree | `http://localhost:6446/v1` |
| kiloproxy | `http://localhost:5380/v1` |

VPN kapalıyken bu portlar kapalı olduğu için OpenCode modelleri **listeleyemez**.
Bu altyapı hatası değil — VPN + tünel gerekiyor. `./vpn_proxy.sh status`
canlı olmayan proxy varsa bunu açıkça söyler.

## Dosyalar

| dosya | konum |
|---|---|
| ayarlar | `~/.config/sunumlar/vpn_proxy.conf` |
| parola | `~/.config/sunumlar/secrets.env` (chmod 600) |
| log | `~/.config/sunumlar/proxy/manager.log` |
| pid | `~/.config/sunumlar/proxy/manager.pid` |

## Dosya düzeni

```
sunumlar/
├── vpn_proxy.sh              # ← TEK GİRİŞ NOKTASI (tüm mantık burada)
├── sync_proxy_models.js      # ← opencode.json model senkronizasyonu
├── docs/
│   └── vpn_proxy.md          # ← bu dosya
│
├── legacy/v1/                # ESKİ kodlar — arşiv, KULLANMA
│   ├── vpn_caffeinate_manager.sh
│   ├── proxy_login.sh
│   ├── proxy_common.sh
│   ├── connect_opencode.sh
│   ├── connect_clineproxy.sh
│   ├── connect_kiloproxy.sh
│   ├── connect_antigravity_proxy.sh
│   └── sync_proxy_models.js
│
└── (diğer kök scriptleri — ham ssh -L tünelleri, dokunulmadı)
    ├── comfuitunnel.sh
    ├── tunnel_ollama.sh
    └── openclow_tunnel.sh
```

Kök dizinde başka tunnel scriptleri de var (`comfuitunnel.sh` vb.). Bunlar
tek satırlık ham `ssh -L` komutları — parola saklamaz, VPN algılamaz, kendini
onarmaz. `vpn_proxy.sh` bunların yaptığını artık otomatik yapar; onlar
dokunulmadan duruyor.

## Kapsam Dışı Bırakılanlar

- **Yerel DNS arızası** (`dig` çalışıyor, `getaddrinfo` timeout):
  VPN açıkken macOS'un çözümleyici zinciri bozuluyor. *Proxy tünelleri
  bundan etkilenmez* — localhost üzerinden çalışırlar. Yalnızca `tubitak`
  gibi doğrudan dış URL'e giden provider'lar etkilenir. Bu, proxy yöneticisinin
  işi değil; ayrı bir konu olarak bırakıldı.
- **`vpn_caffeinate_manager.sh`'in kendi caffeinate'i**: `vpn_proxy.sh` de
  caffeinate çalıştırıyor. İkisi aynı anda çalışırsa çakışabilir.
