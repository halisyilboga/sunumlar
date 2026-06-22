# 🐍 Sunumlar: Modüler Mimari Rehberi

Bu depo, modern yazılım mimarisi, yapay zeka ajanları ve gelecek çalışmaları üzerine hazırlanmış modüler içerikleri barındıran "Agentic-Ready" bir bilgi tabanıdır.

## 🏗️ Mimari Yapı

Proje, hem insanlar hem de AI ajanları tarafından kolayca navigasyon yapılabilecek şekilde katmanlı bir yapıda organize edilmiştir:

```text
.
├── modules/                # Tematik odak noktaları
│   ├── jsf-modern-arch/    # JSF vs Modern Mimari (Quarto)
│   ├── ai-developer-era/   # Yapay Zeka ve Mimari Etik
│   ├── future-studies/     # Gelecek araştırmaları
│   └── analysis/           # Derinlemesine mimari analizler
├── shared/                 # Ortak kaynaklar ve varlıklar
│   ├── assets/             # Görseller, diyagramlar
│   ├── styles/             # Global CSS temaları (cinematic.css)
│   └── components/         # Ortak UI bileşenleri
├── agents/                 # AI Ajan konfigürasyonları ve promptlar
├── scripts/                # Otomasyon ve kurulum scriptleri
└── maindocs/               # Birleştirilmiş ana dökümantasyon
```

## 🚀 Sunumları Çalıştırma (Quarto)

Bu proje [Quarto CLI](https://quarto.org/docs/get-started/) kullanılarak derlenir.

### JSF ve Modern Mimari Sunumu

Sunumu önizlemek için ilgili modül dizinine gitmenize gerek kalmadan kök dizinden şu komutu çalıştırabilirsiniz:

```bash
quarto preview modules/jsf-modern-architecture/content.qmd
```

**Alternatif olarak HTML olarak derlemek için:**
```bash
quarto render modules/jsf-modern-architecture/content.qmd
```

## 🎨 Tasarım Sistemi

Proje, **Cinematic RevealJS** temasını kullanır. Tüm modüller `/shared/styles/cinematic.css` dosyasından beslenir. Bu sayede görsel tutarlılık ve merkezi kontrol sağlanır.

### Görsel Varlıklar
Tüm diyagramlar ve görüntüler `/shared/assets/` altında toplanmıştır. Dökümanlarda bu dosyalara relative path ile (örn: `../../shared/assets/images/...`) erişilmelidir.

## 🤖 AI Ajanları İçin Notlar

Bu repo, AI ajanlarının (Antigravity vb.) projeyi tam olarak anlayabilmesi için optimize edilmiştir:
- **Modüler Yapı**: Her konu kendi içinde izole edilmiştir.
- **Standart Yollar**: `shared/` dizini tüm ortak bağımlılıkları barındırır.
- **Açık İsimlendirme**: `guide.md` derin teknik içerik, `content.qmd` sunum katmanıdır.

---
*Son Güncelleme: 2024-04-03 - Modüler Mimari Reorganizasyonu Tamamlandı*
