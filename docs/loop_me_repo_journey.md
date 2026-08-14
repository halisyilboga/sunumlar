# 🔄 Loop-Me: Bu Deponun Yaşayan Döngüleri ve Ajan Mimarisi

Bir geliştiricinin günlük pratiklerine uzaktan baktığınızda, karmaşık görünen her şeyin aslında iç içe geçmiş öngörülebilir döngülerden (loops) ibaret olduğunu fark edersiniz: sabahları tünelleri açmak, sunum slaytlarını derlemek, yapay zeka ajanlarına görev paylaştırmak ve terminal pencereleri arasında geçiş yapmak. Bir yaşamı ya da bir repoyu "loop merceğinden" incelemek, neyin rutin, neyin otomatikleştirilebilir ve en önemlisi neyin bir yapay zeka ajanına güvenle delege edilebilir olduğunu kristalize eder.

`sunumlar` deposu, ilk bakışta sadece statik sunumların barındığı bir klasör gibi görünse de, kaputun altına indiğinizde bu döngüleri işleten, kendi kendini güncelleyen ve AI ajanlarıyla ortaklaşa yaşayan dinamik bir kontrol merkezidir.

## 1. Ajan Orkestrasyon Döngüsü: BMAD ve Uzmanlaşmış İş Akışları

Bu depodaki ilk ve en kritik döngü, bilişsel yükü tek bir genel modele yüklemek yerine görevleri uzmanlaşmış alt ajanlara dağıtan **BMAD (Benchmark Multi-Agent Design)** ekosistemidir. `.agent/workflows/` dizini altında yaşayan onlarca iş akışı (workflow), her biri tek bir işi kusursuz yapmaya programlanmış sanal bir mühendislik ekibi gibi çalışır:

* **Strateji ve Tasarım Döngüsü:** Bir fikir ortaya atıldığında `/analyst` ve `/architect` devreye girer; gereksinimleri PRD ve mimari kararlara dönüştürür.
* **Uygulama ve Denetim Döngüsü:** `/dev` kodu üretirken, `/qa` ve `/code-review` bağımsız alt süreçlerde kodun standartlara ve sınırlara uygunluğunu acımasızca sınar.
* **Hikayeleştirme ve Sadeleştirme:** `/storyteller` ve `/editorial-review-prose`, teknik karmaşıklığı insan zihninin kolayca kavrayabileceği temiz anlatılara dönüştürür.

Bu döngünün kalbinde **"Push-Right" (Kontrolü Sona Öteleme)** prensibi yatar: Ajanlar işi tamamlayıp her detayı hazır hale getirene kadar insan geliştiriciyi gereksiz sorularla bölmez; karar noktasına gelindiğinde yalnızca onaylanmaya hazır, net bir karar özeti (brief) sunar.

## 2. Bağlam ve Terminal Döngüsü: OmniKey, Herdr ve Format Sonrası Kurtarma

Ajanlar ve insan geliştirici aynı ekosistemde çalışırken karşılaşılan en büyük sürtünme **bağlam kaybı ve arayüz çakışmalarıdır**. Çoklu ajan oturumları (Herdr), gelişmiş editör katmanları (Neovim), terminal çoğullayıcıları (Tmux) ve kabuk yapılandırmaları (Zsh) arasında düzinelerce kısayol ve konfigürasyon dosyası uçuşur.

Bu depoda inşa ettiğimiz **OmniKey**, bu kaosu öngörülebilir bir döngüye dönüştürür:

* **Canlı İzleme (Living Watcher):** `config.toml`, `.tmux.conf` veya `mappings.lua` dosyalarındaki her tuş değişikliğini `watchdog` ile anında yakalar, diff analizini çıkarır ve yerel SQLite veritabanına işler.
* **Çift Dilli Anlamsal Etiketleme & Çakışma Denetimi:** Eylemleri otomatik olarak Türkçe ve İngilizce arama terimleriyle eşlerken (örn: `remove_worktree` ➡️ `sil, worktree, remove`), Herdr ve Tmux arasındaki potansiyel tuş çakışmalarını (örn: `ctrl+s`, `prefix+j`) anında tespit edip raporlar.
* **Sıfır Kayıp ve Kurtarılabilirlik (Disaster Recovery):** Bir geliştiricinin en büyük korkusu makinesini sıfırladığında tüm bu bilişsel ergonomiyi kaybetmektir. OmniKey, tüm veritabanı durumunu `omnikey_export.json` olarak Git'e yedekler ve format sonrası tek bir `./restore.sh` komutuyla tüm terminal zekasını saniyeler içinde eski haline getirir.

## 3. Bilgi Sentezi ve Sinematik Sunum Döngüsü: Quarto ve Modüler Mimari

Üretilen mimari analizlerin, JSF vs Modern Mimari karşılaştırmalarının ve yapay zeka çağı araştırmalarının kalıcı birer varlığa dönüşmesi, deponun **bilgi sentezi döngüsü** ile gerçekleşir:

* **Katmanlı İçerik Ayrımı (`modules/` & `shared/`):** Her çalışma konusu bağımsız bir modül altında izole edilir. Derin teknik analizler `guide.md` dosyalarında yaşarken, izleyiciye aktarılacak görsel katman `content.qmd` içinde şekillenir.
* **Sinematik RevealJS Teması:** Tüm sunumlar `/shared/styles/cinematic.css` üzerinden ortak bir görsel dili konuşur. Bu merkezi stil yönetimi, tek bir kaynaktan tüm sunumların tipografisini, koyu mod estetiğini ve animasyon ritmini kontrol altında tutar.
* **Quarto Derleme Motoru:** `quarto preview` komutuyla içerik yazıldığı anda canlı olarak tarayıcıda izlenir; `quarto render` ile anında web üzerinde paylaşılabilecek interaktif HTML formatına bürünür. Ajanlar içerik ürettikçe sunum döngüsü bu içeriği anında görselleştirir.

## 4. Büyük Sentez: Otonom Bir Bilgi Kokpiti

Bu üç döngüyü—**Ajan Orkestrasyonu**, **OmniKey Bağlam Takibi** ve **Quarto Bilgi Sentezi**—bir araya getirdiğinizde, tekil araçların toplamından çok daha büyük bir şey ortaya çıkar: **Sürtünmesiz bir bilişsel kokpit.**

Geliştirici bir fikri tetikler; BMAD ajanları mimariyi tasarlar, kodu geliştirir ve test eder; OmniKey arka planda tüm bu süreçlerin terminal kısayollarını ve bağlamını canlı tutar; Quarto ise elde edilen teknik kazanımları sinematik sunumlara dönüştürür. Üstelik tüm bu zeka, Git tabanlı kurtarma mekanizmalarıyla donatılmıştır; yarın makine formatlansa dahi tek bir komutla ayağa kalkar.

`sunumlar` reposu bir dosya yığını değil; insanın stratejik niyetleriyle yapay zekanın otonom yürütme gücünün kusursuz bir döngüde buluştuğu yaşayan bir yazılım laboratuvarıdır.
