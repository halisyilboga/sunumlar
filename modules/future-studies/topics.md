# Gelecek Beyin Fırtınası Oturumları: JSF vs Modern Mimari
**Tarih:** 28 Kasım 2025 (Planlanan)
**Amaç:** Mevcut sunumu derinleştirmek ve teknik "Aha Moment"ları artırmak.

Bu doküman, JSF ve Modern Mimari arasındaki ilişkiyi daha teknik ve spesifik açılardan incelemek için belirlenen 10 adet potansiyel beyin fırtınası konusunu içerir.

---

## 1. "Serverless JSF": AWS Lambda üzerinde JSF Çalışır mı?
*   **İlgili Agentlar:** `Architect` (Winston), `DevOps` (PM/Architect vekaleten)
*   **Teknik Tanım:** Modern "Serverless Java" (GraalVM Native Image, Quarkus) teknolojileri kullanılarak eski JSF kodlarının "Soğuk Başlatma" (Cold Start) sorunu olmadan Serverless ortamda çalıştırılabilirliği. JSF'in "Stateful" (Session bağımlı) yapısının, Serverless'ın "Stateless" doğasıyla çatışması ve çözümleri (Externalize Session -> Redis).
*   **Potansiyel Aha Moment:** "Next.js Server Actions, aslında 'Serverless JSF'in modern ve hafifletilmiş halidir. İkisi de 'Fonksiyon olarak Backend' mantığına hizmet eder."

## 2. The "Managed Bean" vs "React Hook" Savaşı
*   **İlgili Agentlar:** `Dev` (Amelia), `Tech Writer` (Paige)
*   **Teknik Tanım:** 
    *   **JSF:** `@ViewScoped`, `@RequestScoped`, `@SessionScoped` ve `@PostConstruct`/`@PreDestroy`.
    *   **React:** `useState`, `useEffect`, `useMemo`.
    *   Bu iki yaşam döngüsü yönetiminin (Lifecycle Management) kare kare karşılaştırması. Bellek yönetimi ve sızıntı (Memory Leak) riskleri.
*   **Potansiyel Aha Moment:** "React `useEffect` aslında JSF'in `@PostConstruct` ve `@PreDestroy` metodlarının birleşimidir, ancak manuel bağımlılık yönetimi (Dependency Array) nedeniyle hata yapmaya çok daha müsaittir."

## 3. Güvenlik: CSRF Token'ın Evrimi
*   **İlgili Agentlar:** `Architect` (Winston), `Analyst` (Mary)
*   **Teknik Tanım:** JSF'in `javax.faces.ViewState` gizli alanının sağladığı doğal CSRF koruması. Modern SPA'larda (React) bu korumayı sağlamak için JWT, Cookie, SameSite, Double Submit Cookie gibi yöntemlerle boğuşulması. Next.js Server Actions'ın bu güvenliği nasıl tekrar otomatize ettiği.
*   **Potansiyel Aha Moment:** "Güvenliği 'modernleştirmek' ve 'stateless' yapmak adına işleri zorlaştırdık. Şimdi Server Actions ile tekrar 'Framework-managed Security' konforuna dönüyoruz."

## 4. "RichFaces" Push vs "WebSocket" vs "Server Sent Events"
*   **İlgili Agentlar:** `Dev` (Amelia), `Architect` (Winston)
*   **Teknik Tanım:** JSF dünyasındaki `a4j:push` (Comet/Long Polling) teknolojisi ile modern dünyadaki `GraphQL Subscriptions` veya `Server Sent Events` (RSC Streaming) karşılaştırması. Gerçek zamanlı (Real-time) veri güncelleme desenleri.
*   **Potansiyel Aha Moment:** "Teknoloji değişti (Socket -> SSE) ama ihtiyaç (Real-time update) ve çözüm mantığı (Sunucudan İstemciye Push) tamamen aynı kaldı."

## 5. Navigasyon Kuralları: `faces-config.xml`'den `App Router`'a
*   **İlgili Agentlar:** `Tech Writer` (Paige), `PM` (John)
*   **Teknik Tanım:** JSF'in XML tabanlı, merkezi ve deklaratif navigasyon kuralları (`<navigation-case>`) ile Next.js'in dosya sistemi tabanlı (File-system based) routing yapısının karşılaştırması. Yönetilebilirlik ve görünürlük analizi.
*   **Potansiyel Aha Moment:** "Eskiden 'Büyüyünce XML yönetilemez oluyor' diye kaçtık, şimdi 'Dosya ağacı çok karmaşıklaştı' diyip Middleware (`middleware.ts`) ile tekrar merkezi kontrol mekanizmaları kuruyoruz."

## 6. Exception Handling: "Error Page"den "Error Boundary"ye
*   **İlgili Agentlar:** `Dev` (Amelia), `UX Designer` (Sally)
*   **Teknik Tanım:** JSF `web.xml` hata sayfaları ve global exception handler yapısı ile React `ErrorBoundary` ve Next.js `error.tsx` yapısının karşılaştırması. Hata anında UI'ın (ve kullanıcının) nasıl kurtarıldığı (Graceful Degradation).
*   **Potansiyel Aha Moment:** "React Error Boundary, aslında `try-catch` bloğunun Component haline gelmiş şeklidir. JSF'in 'Tüm sayfa patlar' mantığına göre çok daha granüler (Bölgesel) hata yönetimi sağlar."

## 7. Dependency Injection: `CDI` vs `React Context`
*   **İlgili Agentlar:** `Architect` (Winston), `Dev` (Amelia)
*   **Teknik Tanım:** Java EE CDI (`@Inject`, `@Named`) mekanizmasının sağladığı "Bağlam Bağımsızlığı" ile React Context API (`useContext`) ve Prop Drilling sorunu. Veriye erişim desenleri.
*   **Potansiyel Aha Moment:** "JSF'te `EL (Expression Language)` sayesinde her veriye ağacın her yerinden erişebiliyorduk. React'ta 'State'i yukarı taşı' (Lifting State Up) diye yıllarca uğraştıktan sonra Context API ile JSF'in o rahatlığına (Global Erişim) geri döndük."

## 8. Uluslararasılaştırma (i18n): `.properties` vs `.json`
*   **İlgili Agentlar:** `Tech Writer` (Paige), `Analyst` (Mary)
*   **Teknik Tanım:** JSF `<f:loadBundle>` ve Java `ResourceBundle` (`message.properties`) yapısı ile modern `next-intl` veya `react-i18next` yapısının karşılaştırması. SSR (Sunucu Tarafı Render) ile i18n performans avantajı.
*   **Potansiyel Aha Moment:** "Client-side i18n (React) yapmak, tüm dil dosyasını (veya büyük parçalarını) tarayıcıya indirmeyi gerektirir. JSF gibi sunucuda çeviri yapıp hazır HTML göndermek (Next.js) her zaman daha performanslı ve SEO dostudur."

## 9. Veritabanı İşlemleri: JPA/Hibernate vs Prisma/Drizzle
*   **İlgili Agentlar:** `Architect` (Winston), `Dev` (Amelia)
*   **Teknik Tanım:** JSF sayfalarında yaşanan meşhur "N+1 Select Sorunu" ve `LazyInitializationException` hatalarının modern React Server Components dünyasındaki karşılığı (`Promise.all` şelalesi, Suspense sınırları). Veri çekme stratejileri.
*   **Potansiyel Aha Moment:** "JSF'te veriyi ekrana basarken `LazyLoad` hatası alırdık, şimdi React'ta `Suspense` ile 'Yükleniyor...' gösteriyoruz. Temel sorun (Veri ile UI'ın senkronizasyonu) aynı, sadece çözümün makyajı değişti."

## 10. Test Stratejisi: Selenium vs Playwright (ve Arquillian)
*   **İlgili Agentlar:** `Tester` (Murat - Tea), `Dev` (Amelia)
*   **Teknik Tanım:** JSF uygulamalarını test etmenin zorluğu (Arquillian ile container içi testler, dinamik ID'ler yüzünden kırılgan Selenium testleri). Modern araçların (Playwright, Cypress, React Testing Library) getirdiği kolaylıklar ve `data-testid` standartları.
*   **Potansiyel Aha Moment:** "JSF'in en zayıf karnı test edilebilirlikti. Dinamik üretilen ID'ler (`form:j_id123`) otomasyonu imkansız kılıyordu. Modern frameworklerin en büyük farkı, 'Test Edilebilirlik' kavramını birinci sınıf vatandaş yapmasıdır."
