# Noritales Local SEO + LLM Blog Writer

Lokalde çalışan basit bir Streamlit aracı. Detaylı spesifikasyon: [Noritales_Local_SEO_LLM_Blog_Writer_SPEC.md](Noritales_Local_SEO_LLM_Blog_Writer_SPEC.md)

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`.env` içine `OPENROUTER_API_KEY` değerini yaz (veya uygulama açıldıktan sonra sidebar'dan gir).

## Çalıştırma

```bash
streamlit run app.py
```

## Akış

1. **Research** — konu + focus keyword + dil + kelime sayısı girilir, Research Model seçilir, `RESEARCH TOPIC` çalıştırılır (Request 1).
2. Research sonucundaki sorular okunup **Your Answers** kutusuna cevap yazılır.
3. **Article Prompt Builder Model** seçilip `BUILD ARTICLE PROMPT` çalıştırılır (Request 2, ayrı çağrı).
4. **Writer Model** seçilip `WRITE ARTICLE` çalıştırılır (Request 3, ayrı çağrı).
5. **Evaluator Model** seçilip `RUN SEO + LLM AUDIT` çalıştırılır — önce Python deterministik kontroller (URL doğrulama dahil), sonra Evaluator modeli (Request 4, ayrı çağrı).
6. Sonuca göre `REVISE ARTICLE` (80-89) veya `REGENERATE ARTICLE` (0-79 / hard fail, maksimum 2 kez) yapılabilir.
7. `Download Markdown` ile makale indirilir; `outputs/` klasörüne de kaydedilebilir.

Her adım tamamen bağımsız bir OpenRouter API çağrısıdır; hiçbiri birleştirilmez, her biri kendi modelini kullanır.
