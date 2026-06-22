# Webtop Proxy Hide Butunlesik Analiz

## Kapsam

Bu dosya su girdileri birlestirir:

- `run_webtop.sh`
- `proxy_hide.md`
- `proxy_hide_SWE.md`
- `proxy_hide_kimi.md`

Not: Dizinde dort yerine uc adet `proxy_hide*.md` dosyasi bulundu. Analiz bu uc belge ve `run_webtop.sh` uzerinden yapildi.

Amac, metinlerdeki tum ana iddialari tek yerde toplamak, teknik olarak mesru olanlari ustte biriktirmek, mesru olmayanlari alta tasimak ve her biri icin nedenini aciklamaktir.

## Kisa Hukum

Bu belgelerdeki temel niyet dogru: host bilgisini azaltmak, oturumlari ephemerallestirmek, dogrudan cikisi kontrol etmek, telemetriyi azaltmak ve uygulamayi kisisel hesapla kullanmamak.

Ama belgeler asiri garanti veriyor. "Cursor/Windsurf asla sizi, bilgisayarinizi veya hesabinizi eslestiremeyecek" seviyesi bir vaat teknik olarak mesru degil. En iyi ihtimalle yapilabilecek sey, tanimlayici sinyalleri azaltmak, cihaza bagli kalici kimlikleri engellemek, dogrudan ag cikisini kontrol etmek ve hesap temelli baglamayi onlemektir. Tam garanti yoktur.

## `run_webtop.sh` Hakkinda Gercek Durum

Su anki scriptin gercek etkisi:

- Her calistirmada ayni isimli container silinip yeniden yaratiliyor.
- Host `uid/gid` degerleri `PUID/PGID` olarak container icine aktariliyor.
- `TZ="Europe/Istanbul"` dogrudan aktariliyor.
- Container dogrudan bridge ag uzerinden internete cikiyor.
- Script container icinde `apt`, `curl`, `npm` ve vendor repo erisimleri yapiyor.
- `windsurf --no-sandbox` ile baslatiliyor.
- Host home, ssh-agent, Wayland socket veya host proje dizini mount edilmiyor.
- `/config` hosta mount edilmedigi icin script bugunku haliyle sessionlar arasi kalici uygulama verisi tasimiyor.

Bu nedenle dokumanlardaki bazi riskler gercek, bazilari ise scriptin bugunku hali icin yanlis veya abartili.

## Uste Tasinacak Mesru Iddialar

Asagidaki iddialar teknik olarak mesrudur ya da cekirdegi dogrudur.

### 1. Host `PUID/PGID` degerlerini vermek gereksiz bir fingerprint sinyali uretir

Durum: `legitimate`

Gerekce:

- `run_webtop.sh` su an `id -u` ve `id -g` degerlerini dogrudan veriyor.
- Bu degerler tek basina kuvvetli bir global kimlik degildir ama uygulama tarafinda okunabilir bir hosta-ozel sinyal uretir.
- LinuxServer imajlari `PUID/PGID` kullanir; gizlilik icin sabit ve jenerik bir deger secmek daha dogrudur.

Sonuc:

- `1000/1000` gibi sabit bir cift kullanmak, host kullanici kimliginin tasinmasindan daha iyidir.

### 2. `TZ="Europe/Istanbul"` lokasyon hakkinda bilgi sizdirir

Durum: `legitimate`

Gerekce:

- Zaman dilimi dogrudan uygulama tarafindan okunabilir.
- Bu bilgi IP, dil, calisma saatleri ve baska sinyallerle birlestiginde profil olusturmaya yardim eder.

Sonuc:

- `UTC` veya bilincli secilen sabit bir timezone kullanmak mantiklidir.

### 3. Dogrudan internet cikisi gizlilik riskidir

Durum: `legitimate`

Gerekce:

- Script su an package repo, npm ve vendor endpointlerine dogrudan cikiyor.
- Bu trafik cihaziniza ait normal cikis IP'si, zamanlama ve baglanti metadatasi uretir.
- Proxy, egress gateway veya kontrollu cikis noktasi kullanmak bu riski azaltir.

Sonuc:

- Tam proxy zorlugu degilse bile en azindan kontrollu DNS ve kontrollu egress gerekir.

### 4. Kalici volume, host mount veya kisisel dosya tasimak baglamayi kolaylastirir

Durum: `legitimate`

Gerekce:

- Belgelerdeki "host home mount etme", "ssh agent verme", "git config kopyalama", "kendi dosyalarini tasima" uyarilari dogrudur.
- Bunlar hem dogrudan kimlik hem de davranissal baglam tasir.

Sonuc:

- Ephemeral calisma alani ve yeni kimlikli git/config ortami kullanilmalidir.

### 5. `--no-sandbox` yerel guvenligi zayiflatir

Durum: `legitimate`

Gerekce:

- Electron dokumani `--no-sandbox` icin bunun Chromium sandbox'ini kapattigini ve sadece test icin kullanilmasi gerektigini acikca soyler.
- Bu bir anonimlik ozelligi degil; tersine exploit etkisini buyutebilir.

Sonuc:

- Mecur degilseniz kaldirilmali. Mecbur kaliniyorsa bunun gizlilik degil yalnizca calistirma uyumlulugu karari oldugu not edilmelidir.

### 6. Browser fingerprint sinyallerini azaltmak faydalidir

Durum: `legitimate`

Gerekce:

- Sabit ekran boyutu, sabit dil, sabit timezone, WebRTC kapatma, Firefox telemetry kapatma, anti-fingerprinting tercihleri genel olarak mantiklidir.
- Bunlar garantili anonimlik saglamaz ama sinyal yuzeyini daraltir.

Sonuc:

- Browser tarafinda standardizasyon yararlidir.

### 7. Uygulama ici telemetry ayarlari varsa kapatilmasi gerekir

Durum: `legitimate`

Gerekce:

- Settings dosyasi uzerinden kapatilabilen telemetry veya update davranislari kapatilabilir.
- Bu, uygulamanin kendisinin sundugu resmi ayarlara dayanirsa mesrudur.

Sinir:

- Yalnizca gercekten desteklenen ayarlara guvenilebilir. Rastgele env var veya hayali CLI flag'lerine degil.

### 8. CPU/RAM, locale ve platform gibi sinyaller fingerprint yuzeyidir

Durum: `partially legitimate`

Gerekce:

- Evet, bunlar fingerprint yuzeyinin parcasi olabilir.
- Ancak internet uzerindeki uygulamalar MAC veya anakart seri numarasi kadar dogrudan bunlari gormez; bunlara ancak uygulama icindeki API'ler ve proc/sys erisimiyle sinirli sekilde ulasilir.

Sonuc:

- Kaynak limitleri ve sabitlestirme yararlidir ama belgelerdeki kadar "tam maskeleme" beklenmemelidir.

### 9. Ag katmaninda allowlist veya denylist dusunmek mantiklidir

Durum: `partially legitimate`

Gerekce:

- Telemetry alan adlarini bloklamak mantikli olabilir.
- Ama bunun hosts, iptables, proxy ve uygulama ayari kombinasyonuyla dikkatli yapilmasi gerekir.

Sinir:

- Yalnizca hosts dosyasi veya kaba IP engeli tek basina dogru cozum degildir.

### 10. Hesaba login olmak en guclu baglama sinyalidir

Durum: `legitimate`

Gerekce:

- Hesapla giris yaptiginiz anda tum cihaz izolasyonu cabasi buyuk olcude anlamsizlasir.
- Belgelerdeki "kendi hesabinla login olma" uyarisi dogrudur.

Sonuc:

- Ayrik hesap, guest mode veya login gerektirmeyen kullanim hedeflenmelidir.

## Alta Tasinacak Mesru Olmayan Iddialar

Asagidaki iddialar teknik olarak mesru degil, yanlis, kanitsiz, asiri iddiali veya dogrudan zararli.

### 1. "Cursor/Windsurf asla sizi, bilgisayarinizi veya hesabinizi eslestiremeyecek"

Durum: `legitimate degil`

Cunku:

- Bu bir garanti ifadesidir ve teknik olarak savunulamaz.
- Hesap, yazim stili, repository icerigi, calisma saatleri, IP/egress noktasi, uzanti kullanimi, dosya adlari ve davranissal sinyaller yine baglama uretebilir.
- Guvenli ifade "baglama sinyallerini azaltir" olmalidir.

### 2. "Cursor arka planda surekli seri numarasi, BIOS ID, CPU ID, tum bagli cihazlar, OS kurulum tarihi topluyor"

Durum: `legitimate degil`

Cunku:

- Belgelerde bu iddia icin teknik kanit yok.
- Standart, unprivileged bir container icinde bu verilerin bir kismina zaten dogrudan ve guvenilir sekilde erisilemez.
- Bu seviyede kesin ve kapsamli toplama iddiasi kanit olmadan yazilmis.

### 3. "MAC adresi host ile ayni"

Durum: `legitimate degil`

Cunku:

- Docker bridge uzerindeki container kendi sanal arayuzune sahiptir.
- Uzak internet servisi sizin L2 MAC adresinizi gormez; NAT arkasinda host IP'sini gorur.
- Yerel MAC spoofing yerel ag baglaminda anlamli olabilir ama internet uzerindeki vendor'a host MAC'in gitmesi gibi bir durum yoktur.

### 4. "Container ismi sabit oldugu icin dis dunyada kalici identifier olur"

Durum: `legitimate degil`

Cunku:

- `webtop` gibi bir container adi Docker daemon seviyesinde lokal bilgidir.
- Uzak servis bunu kendiliginden gormez.
- Lokal operasyon hijyeni icin rastgelelestirme yapilabilir ama bu uzaktaki uygulama fingerprintinin ana parcasi degildir.

### 5. "Su an `/config` volume kalici oldugu icin cross-session tracking var"

Durum: `legitimate degil`

Cunku:

- Mevcut `run_webtop.sh` icinde `/config` icin host volume mount yok.
- Container her calismada silinip tekrar yaratildigi icin bugunku scriptte sessionlar arasi kalicilik temel durum degil.
- Bu risk ancak sonra volume eklerseniz gercek olur.

### 6. "Machine ID kesinlikle sessionlar arasi persist ediyor"

Durum: `partially legitimate ama bu script icin abartili`

Cunku:

- `machine-id` bir sistem kimligidir ve container icinde mevcut olabilir.
- Ama mevcut script container'i silip yeniden yarattigi ve `/config` mount etmedigi icin bunu "kalici cross-session takip" diye yazmak bugunku hali icin fazla iddiali.

### 7. `CURSOR_DISABLE_TELEMETRY`, `CURSOR_SKIP_LOGIN`, `CURSOR_NO_DEVICE_ID`, `WINDSURF_NO_FINGERPRINT` gibi env var'larin kesin etkili oldugu varsayimi

Durum: `legitimate degil`

Cunku:

- Belgelerde bu degiskenlerin uygulama tarafinda resmi olarak desteklendigine dair kanit yok.
- Uygulama tarafinda okunmayan bir env var hicbir sey yapmaz.
- Yalnizca vendor tarafindan dokumante edilmis ayarlara guvenilebilir.

### 8. `--disable-machine-id` gibi bayraklarin etkili oldugu varsayimi

Durum: `legitimate degil`

Cunku:

- Electron dokumani desteklenmeyen switch'lerin etkisiz olabilecegini soyler.
- Bu tur bayraklar belgelerde kesin cozum gibi sunulmus ama resmi destek gosterilmiyor.

### 9. `echo 0 > /proc/cpuinfo`, `echo "GenuineIntel" > /proc/cpuinfo`, `echo 0 > /sys/hypervisor/...` gibi onlemler

Durum: `legitimate degil`

Cunku:

- Bunlar normal bir Linux sistemde bu sekilde yazilabilir hedefler degildir.
- `proc` ve `sys` altindaki bu girdilerin buyuk bolumu bu yontemle degistirilemez.
- Kavramsal olarak "maskeleriz" denmis ama pratik komut yanlistir.

### 10. `/sys/devices/virtual/dmi/id` gibi dizinlere `/dev/null` bind etme onerileri

Durum: `legitimate degil`

Cunku:

- Dosyayi dosyaya bind etmekle dizini dosyaya bind etmek ayni sey degildir.
- Bir kisim ornekler dogrudan gecersiz veya asiri kirilgan.

### 11. `--userns=keep-id` ve `--uts=none` gibi Docker ornekleri

Durum: `legitimate degil`

Cunku:

- Docker CLI icin bu degerler bu sekilde gecerli degildir.
- Ornek komutlar "hardening" gibi sunuluyor ama pratikte calismayabilir.

### 12. `--cap-drop=ALL` ile birlikte `--cap-add=SYS_ADMIN`, `seccomp=unconfined`, `apparmor=unconfined`, `label=disable` kullanmanin "guvenlik" olarak sunulmasi

Durum: `legitimate degil`

Cunku:

- `SYS_ADMIN` cok guclu bir capability'dir.
- `seccomp=unconfined` ve benzer ayarlar sandbox'i gevsatir.
- Bunlar bazen uyumluluk icin kullanilabilir ama anonimlik veya guvenlik artisi olarak yazilmalari yanlistir.

### 13. `/etc/hosts` icinde `*.cursor.sh`, `*.codeium.com` gibi wildcard satirlarin calisacagi varsayimi

Durum: `legitimate degil`

Cunku:

- `hosts` dosyasi statik host adlari icindir; wildcard mantigi yoktur.
- Bu satirlar beklenen etkiyi saglamaz.

### 14. Kaba IP bloklariyla Cloudflare araliklarini dusurmenin dogru telemetry engeli oldugu varsayimi

Durum: `legitimate degil`

Cunku:

- Cloudflare IP bloklari cok genistir.
- Bunlari bloklamak bircok ilgisiz servisi de keser.
- TLS uzerindeki trafik icinde `iptables -m string` ile alan adi yakalamak da guvenilir degildir.

### 15. "MitM SSL decryption + JA3/TLS standartlastirma" kolay ve dogrudan uygulanabilir bir katmandir

Durum: `legitimate degil`

Cunku:

- Bu, siradan proxy kurmaktan cok daha karmasiktir.
- Sertifika guveni, uygulama certificate pinning'i, HTTP/2/TLS davranisi ve uygulama kararliligi uzerinde agir etkileri vardir.
- "Sonraki adim" gibi yazilmis ama gercek dunya maliyeti cok yuksektir.

### 16. `state.vscdb` dosyasina JSON yazarak Windsurf storage override etmek

Durum: `legitimate degil`

Cunku:

- `.vscdb` tipik olarak SQLite veritabani formatidir, JSON dosyasi degil.
- Bu ornek uygulandiginda beklenen sekilde calismasi yerine dosyayi bozma riski tasir.

### 17. Firefox profil yolunu `*.default-release` veya `*.default-esr` ile quoted sekilde yazmak

Durum: `legitimate degil`

Cunku:

- Verilen snippet'lerde wildcard literal kalir veya gercek profile hedeflenmez.
- Bu, fikir olarak dogru olsa bile uygulama seviyesi ornegin dogru olmadigini gosterir.

### 18. `--disable-web-security`, `--disable-webrtc-encryption`, `--disable-xss-auditor` gibi bayraklarin gizlilige yardim ettigi varsayimi

Durum: `legitimate degil`

Cunku:

- Bunlar gizlilikten cok guvenlik mekanizmalarini zayiflatir veya alakasizdir.
- Bir kismi eski, bir kismi riskli, bir kismi dogrudan ters etkilidir.

### 19. `--network none` ile baslatip ayni anda setup sirasinda dogrudan `apt/curl/npm` kullanmanin tutarli oldugu varsayimi

Durum: `legitimate degil`

Cunku:

- Tam agsiz mod ile online kurulum ayni anda yurumez.
- Belgelerdeki ag mimarisi ile kurulum adimlari arasinda operasyonel celiski var.

### 20. "Host hakkinda sifir bilgi sizdirilir"

Durum: `legitimate degil`

Cunku:

- Pratikte sifir sizinti dili kullanilamaz.
- Timing, egress IP, davranis, package pull paterni, hata raporlari, manuel kullanici hareketleri gibi residual sinyaller kalir.

## Belgelerden Cikarilan Gercekci Hedef Modeli

Asagidaki hedef ifadesi teknik olarak savunulabilir:

"Amac, container icindeki uygulamanin host kullanici kimligini, yerel timezone'u, kalici uygulama state'ini ve kontrolsuz direkt ag cikisini gormesini azaltmak; sessionlar arasi baglayici kimlikleri minimuma indirmek; hesaba dayali baglamayi onlemek; ve outbound trafik uzerinde denetlenebilir bir egress katmani kurmaktir."

Bu ifade savunulabilir. "Tam anonimlik" ve "asla eslestiremez" savunulabilir degil.

## Uygulamaya Gecmeden Once Korunacak Ana Ilkeler

Belgelerin birlesmis ve gercekci cekirdegi su olmalidir:

1. Container state'i ephemeral olmali.
2. Host `uid/gid`, timezone ve benzeri sinyaller sabit/jenerik olmali.
3. Host home, ssh-agent, git config, proje klasoru gibi dogrudan kimlik tasiyan mount'lar olmamali.
4. Uygulama hesabi ayrik olmali; mumkunse login olmamali.
5. Outbound trafik kontrollu bir proxy veya egress katmanindan gecmeli.
6. Destekli telemetry ayarlari kapatilmali.
7. Browser ve Electron tarafinda yalnizca gercekten desteklenen ayarlar kullanilmali.
8. "Guvenlik hardening" ile "anonimlik" birbirine karistirilmamali.
9. Asiri bayrak kalabaligi yerine test edilebilir, az sayida, etkisi bilinen onlem tercih edilmeli.

## Sonuc

Uc dokumanin ortak cekirdegi faydali ama su anki halleriyle iki ciddi problem var:

- Garanti dili kullaniyorlar.
- Teknik olarak gecersiz, etkisiz veya zararli onlemleri de "zorunlu guvenlik" gibi sunuyorlar.

Bu nedenle uygulamaya gecmeden once dogru zemin su olmali:

- Mevcut scriptte gercek sızıntilari duzelt.
- Yalnizca resmi olarak desteklenen ayar ve Docker semantigine dayan.
- Ephemeral state + kontrolu egress + hesap ayrimi + host mount minimizasyonu dordeksenli model kur.
- "Tam anonimlik" vaadini tamamen birak.

## Referanslar

Teknik siniflandirma su kaynaklarla uyumlu yapildi:

- Docker `docker run` referansi: https://docs.docker.com/reference/cli/docker/container/run
- Docker bridge network davranisi: https://docs.docker.com/engine/network/drivers/bridge/
- Docker bind mount davranisi: https://docs.docker.com/engine/storage/bind-mounts/
- LinuxServer `PUID/PGID` aciklamasi: https://docs.linuxserver.io/general/understanding-puid-and-pgid/
- LinuxServer `webtop` kullanim dokumani: https://docs.linuxserver.io/images/docker-webtop/
- `machine-id` dokumani: https://www.freedesktop.org/software/systemd/man/devel/machine-id.html
- `hosts(5)` man sayfasi: https://man7.org/linux/man-pages/man5/hosts.5.html
- Electron command line switch dokumani: https://www.electronjs.org/docs/latest/api/command-line-switches
- Electron sandbox dokumani: https://www.electronjs.org/docs/latest/tutorial/sandbox/
