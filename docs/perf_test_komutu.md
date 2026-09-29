# OpenAI uyumlu performans testi (token/s & word/s ölçümü)

Diğer modellerle karşılaştırma için opencode içinde, **kod yazmadan**, modele büyük bir dosya yazdırıp hız ölçmek istiyorsunuz. Bu doküman, her seferinde aynı promptu elle yazmamanız için hazır promptu ve nasıl kullanılacağını içerir.

## Yöntem (kısaca)

1. Testi başlatmadan önce bir **başlangıç zamanı** al.
2. Modele belirli boyutta tek parça büyük bir metin dosyası yazdır.
3. Yazma bitince **bitiş zamanı** al.
4. Dosyanın **token sayısını** ve **kelime sayısını** hesapla.
5. `token/s` (t/s) ve `word/s` değerlerini çıkar.

## Zamanlama nasıl yapılır

opencode hesap makinesi/terminal komutu çalıştırabildiğinden, başlangıcı **IMMEDIATELY** yakalamak için test promptunun içinde aşağıdaki gibi elle işaretleyin:

- Testi göndermeden hemen önce terminalde `date +%s` çalıştırıp `$START` değerini not al.
- Yazma tamamlandığı anda `date +%s` çalıştırıp `$END` değerini not al.
- Süre = `END - START` saniye.
- t/s = token_sayisi / süre
- word/s = kelime_sayisi / süre

## Yeniden kullanılabilir prompt (command olarak)

Bu bloğu doğrudan modele yapıştırın. Aşağıya `$ARGUMENTS` açıklaması var; isterseniz `.opencode/command/perf-test.md` olarak kaydedip `/perf-test` ile çağırın.

```
[ÖLÇÜM BAŞLANGICI] Şu anki unix zamanını terminalde `date +%s` ile al ve START değişkenine kaydet. Sonra aşağıdaki adımları takip et.

1. Şu anki zamanı kaydet (START): `date +%s`
2. Aşağıda tarif edilen "BÜYÜK DOSYA" içeriğini, tek bir yazma sonucu olarak, kesintisiz şekilde üret ve `perf_output.txt` dosyasına yaz.
3. Yazma bitince şu anki zamanı kaydet (END): `date +%s`
4. Sonra aşağıdaki hesaplamaları yap:
   - süre = END - START (saniye)
   - perf_output.txt dosyasının token sayısını ve kelime sayısını ölç:
       · kelime sayısı = `wc -w perf_output.txt`
       · token sayısı = dosyayı boşluk ve noktalama temelli basit bir tokenizer'dan geçir veya `wc -c / ~4` gibi bir yaklaşım kullan; mümkünse gerçek tokenizer (örn. `npx @anthropic-ai/claude-code` yoksa basit `wc -w` tabanlı yaklaşım) kullan.
   - t/s = token_sayisi / süre
   - word/s = kelime_sayisi / süre
5. Sonucu şu formatta özetle:

## SONUÇ
- START: <unix_ts>
- END: <unix_ts>
- Süre: <sn> sn
- Kelime sayısı: <n>
- Token sayısı: <n>
- word/s: <x>
- token/s (t/s): <x>

[ÖLÇÜM BİTİŞİ]

## BÜYÜK DOSYA (BU İÇERİĞİ ÜRET)
Aşağıdaki konuyu anlatan, yaklaşık 2000 kelimelik, Türkçe, madde madde ve paragraflarla zenginleştirilmiş bilgilendirici bir makale yaz:
<konu: Buraya test etmek istediğin konuyu yaz, örn. "Yapay zeka tarihçesi">
```
