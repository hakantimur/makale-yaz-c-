# Noritales Local SEO + LLM Blog Writer

Lokalde çalışan basit bir Streamlit aracı. Detaylı spesifikasyon: [Noritales_Local_SEO_LLM_Blog_Writer_SPEC.md](Noritales_Local_SEO_LLM_Blog_Writer_SPEC.md)

## Çalıştırma (en kolay yol)

`run.bat` dosyasına çift tıkla.

İlk çalıştırmada otomatik olarak:
- `.venv` sanal ortamı oluşturulur ve bağımlılıklar kurulur,
- `.env` yoksa `.env.example`'dan oluşturulur,
- Streamlit tarayıcıda açılır (`http://localhost:8501`).

`OPENROUTER_API_KEY`'i `.env` dosyasına yazabilir veya uygulama açıldıktan sonra sol sidebar'dan girebilirsin.

## Manuel kurulum (istersen)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

## Akış

1. **Research** — konu + focus keyword + dil + kelime sayısı girilir, Research Model seçilir, `RESEARCH TOPIC` çalıştırılır (Request 1).
2. Research sonucundaki sorular okunup **Your Answers** kutusuna cevap yazılır.
3. **Article Prompt Builder Model** seçilip `BUILD ARTICLE PROMPT` çalıştırılır (Request 2, ayrı çağrı).
4. **Writer Model** seçilip `WRITE ARTICLE` çalıştırılır (Request 3, ayrı çağrı).
5. İstersen **🎨 GÖRSEL VE GRAFİK EKLE** ile makaleye 1-2 gerçek AI görseli ve varsa gerçek grafik(ler) eklenir (Image Model, ayrı çağrı). Bu adım metni beğendikten sonra yapılırsa gereksiz görsel maliyetinden kaçınılır — ama istediğin an tekrar çalıştırılabilir. Bir görsel/grafik başarısız olursa makale durmaz, sadece o öğe atlanır.
6. **Evaluator Model** seçilip `RUN SEO + LLM AUDIT` çalıştırılır — önce Python deterministik kontroller (URL doğrulama, gömülü link/CTA/istatistik kontrolü dahil), sonra Evaluator modeli (Request 4, ayrı çağrı). Gömülü görseller/grafikler LLM'e gönderilmeden önce otomatik olarak metinden çıkarılır (aksi halde context boyutu patlar).
7. Sonuca göre `REVISE ARTICLE` (80-89) veya `REGENERATE ARTICLE` (0-79 / hard fail, maksimum 2 kez) yapılabilir.
8. `Download Markdown` ile ham markdown, `Download HTML` ile **Wagtail'e yapıştırmaya hazır gerçek HTML** indirilir.

Her adım tamamen bağımsız bir OpenRouter API çağrısıdır; hiçbiri birleştirilmez, her biri kendi modelini kullanır.

## Wagtail'e yayınlama

Bu araç Wagtail'e otomatik yayın yapmaz (V1 kapsamı dışında) — makaleyi elle yapıştırırsın. Önemli:

- **"Download HTML" çıktısını Wagtail'in `RawHTMLBlock`'una yapıştır, düz `RichTextField`'a değil.** Wagtail'in varsayılan rich text editörü (Draftail) güvenlik amacıyla özel `class` attribute'larını ve tanımadığı HTML yapılarını temizler — CTA butonları, istatistik/alıntı kutucukları ve grafikler görünmez hale gelir.
- Sitenin CSS'ine şu class'lar için stil eklemen gerekir: `noritales-cta-button`, `noritales-stat-card` (+ `noritales-stat-number`, `noritales-stat-label`), `noritales-quote-box`, `noritales-tip-box`, `noritales-chart`, `noritales-image`. Uygulamanın kendi önizlemesinde kullanılan örnek stiller [app.py](app.py) içinde (`<style>` bloğu) — aynısını sitenin CSS'ine taşıyabilirsin.
- Görseller ve grafikler HTML'e **base64 olarak gömülüdür** (data URI) — ayrıca bir dosya yükleme/hosting adımına gerek yoktur, kopyala-yapıştır yeterlidir. Aynı görsellerin bir kopyası `outputs/images/<slug>/` altına da kaydedilir (yedek/referans amaçlı).
- Doğrudan Markdown'ı (tablo/başlık/kalın yazı içeren) ham metin olarak yapıştırma — `|`, `#`, `**` gibi işaretler RawHTMLBlock'ta yorumlanmadığı için olduğu gibi görünür. Bu yüzden HTML export özelliği var.
