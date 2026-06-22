Bu remote makinami kendim icin bir super makina haline getirmek istiyorum Bu kapsamda super yaratici ol opensource ve remote makinamda calisacak seyleri bulmam icin bana bi rprompt ver bundan bir arastirma yapacagim. Makinin ozelliklerini yaz prompta. Yani deepresearch icin prompt istiyorum ne is yaptigimi neyden hoslandigimi neyin hayatimi iyilestirecegini az cok tahmin etmen gerekiyor. 


----------------

Sen, açık kaynak (open-source) ekosistemine, self-hosted (kendi sunucusunda barındırılan) mimarilere ve yerel yapay zeka (Local AI) optimizasyonlarına, Openclaw (guncel alternatiflerine) üst düzeyde hakim, vizyoner bir sistem mimarı ve yaşam hackleme (life-hacking) uzmanısın.

Elimde sadece SSH ile bağlandığım, uzakta çalışan Ubuntu tabanlı bir sunucu var. Bu makineyi benim için 7/24 otonom çalışan bir "Süper Asistan" ve "Dijital İkinci Beyin" haline getirmek istiyorum. 

Sistem Özelliklerim:
- Çift (2x) NVIDIA GTX TITAN X (Her biri 12GB, Toplam 24GB VRAM)
- Mimari: Maxwell (2015) - ÖNEMLİ NOT: Tensor Core YÖK. Bu yüzden fp16 işlemler CUDA core'lar üzerinden yapılıyor, modern AI modellerini çalıştırırken quantization (GGUF, Q4_K_M) ve RAM/VRAM offloading şart.
- RAM: 62GB
- İşlemci: Intel i7-5930K (12 Çekirdek)

Kullanıcı Profilim:
Kıdemli bir yazılımcıyım. Java, Spring AI ve Apache Solr ile kurumsal RAG mimarileri kuruyorum. Geliştirme süreçlerimde terminal üzerinden CLI araçları (OpenCode, Aider) kullanıyorum. Kendi verilerimle çalışan bir Google NotebookLM klonu geliştiriyorum. 
İlgi alanlarım çok çeşitli: Bilişsel ve fiziksel performans (Wim Hof, Silva Metodu, Mumiyo), dil öğrenimi (Rusça), sanat/tarih, fotoğraf üzerinden vizajizm/stil analizi, kripto/borsa yatırımları ve iki oğlumla (Yusuf ve Yunus) oynayabileceğimiz zeka/kutu oyunları.

Görev:
Bana bu donanıma kurabileceğim, hayatımı her alanda "10x" iyileştirecek, yaratıcı, açık kaynaklı self-hosted araçlar ve otomasyon senaryoları tasarla. Klasik "Nextcloud kur" tarzı sıkıcı tavsiyeler İSTEMİYORUM. Beni şaşırtacak, birbirine entegre çalışan sistemler kurgula.

Araştırmanı şu 5 ana dikeyde derinleştir:

1. Geliştirici Üssü ve RAG Ekosistemi:
Maxwell mimarisine rağmen 24GB VRAM'i en iyi kullanacak, en son modellerden birini ollama ile yukledim. entegre bir sekilde çalışabilecek, Solr yeteneklerimi artıracak AI backend çözümleri (Örn: Ollama yanına LiteLLM, Open-WebUI, veya Dify/AnythingLLM entegrasyonları).

2. Otonom Finans ve Veri Avcısı (Agentic Workflows):
Arka planda 7/24 çalışan, belirlediğim kripto paraları veya borsa trendlerini kazıyan, lokal bir LLM'den geçirip bana Telegram üzerinden günlük yatırım özetleri ve duygu analizi (sentiment analysis) gönderecek açık kaynak otomasyon araçları (n8n, Huginn vb. ile AI kombinasyonları).

3. "İkinci Beyin" ve NotebookLM Klonum İçin Altyapı:
Wim Hof, Silva metodu araştırmalarımı, Rusça notlarımı ve tarih okumalarımı atabileceğim, benimle bu belgeler üzerinden felsefi tartışmalara girebilecek en iyi self-hosted bilgi yönetimi ve RAG arayüzleri.

4. Görsel Zeka ve Vizajizm Laboratuvarı:
Fotoğraflar üzerinden saç/sakal ve yüz analizi (vizajizm) yapabilmem için ComfyUI üzerinde Titan X'leri ağlatmadan çalışacak spesifik workflow fikirleri veya lokal vision modelleri (Örn: LLaVA) ile kurulabilecek analiz araçları.

5. Eğitim ve Çocuklar:
İki oğlumla kaliteli zaman geçirmek için, evdeki makineye bağlanıp bize interaktif, sonsuz hikayeli FRP tarzı kutu oyunları/günlük görev oyunları (The Dice Man mantığında ama pozitif) üretebilecek lokal AI destekli yaratıcı fikirler.

Lütfen bana mimari kurguyu, kullanmam gereken Docker container'ları ve bu sistemlerin birbiriyle nasıl konuşacağını detaylı bir manifesto şeklinde sun.