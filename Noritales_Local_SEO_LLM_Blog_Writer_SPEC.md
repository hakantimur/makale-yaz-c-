# Noritales Local SEO + LLM Blog Writer
## Basit Lokal Uygulama — Geliştirici Spesifikasyonu

**Versiyon:** 1.0  
**Amaç:** Kullanıcının verdiği konu ve değiştirilemez focus keyword üzerinden; araştırmalı, kaynaklı, SEO uyumlu, insan editör kalitesinde ve Google + LLM görünürlüğüne uygun blog makalesi üretmek.

---

# 1. Projenin Özeti

Bu proje karmaşık bir SEO platformu değildir.

Uygulama **lokalde çalışan basit bir Streamlit aracı** olacaktır.

Kullanıcı şunları girer:

- Konu
- Focus keyword
- Dil
- Hedef kelime sayısı
- Opsiyonel hedef ülke/pazar
- OpenRouter API Key (sidebar'da; `.env`'den otomatik yüklenir, elle de girilebilir)
- Research modeli
- Article Prompt Builder modeli
- Writer modeli
- Evaluator modeli

Sistem **dört ayrı API request'i** ile çalışır. Hiçbir adım başka bir adımla birleştirilmez; her request kendi modelini ve kendi promptunu kullanır. Uygulama modelin web search desteğini otomatik algılamaz veya filtrelemez — hangi modelin bu işe uygun olduğuna kullanıcı kendisi karar verir.

```text
REQUEST 1 — RESEARCH (Research Model)
        ↓
Konu araştırması + kaynaklar + istatistikler
        ↓
Kullanıcıya 4–8 konuya özel soru
        ↓
Kullanıcının cevapları (Streamlit formu)

REQUEST 2 — BUILD ARTICLE PROMPT (Article Prompt Builder Model)
        ↓
Research Pack + Kullanıcı Cevapları
        ↓
Makaleye özel Writer Prompt

REQUEST 3 — WRITE ARTICLE (Writer Model)
        ↓
Makale + SEO metadata + excerpt + kaynaklar + tablo/görsel önerileri

REQUEST 4 — SEO + LLM QUALITY AUDIT (Evaluator Model)
        ↓
Python deterministik kontroller (URL doğrulama dahil) + Evaluator model değerlendirmesi
        ↓
Evaluator'ın kendi ürettiği tek bir holistik skor (0–100)
        ↓
PASS / REVISE / REGENERATE
```

---

# 2. Ana Marka Stratejisi

Tüm promptlarda aşağıdaki konumlandırma korunacaktır:

> **Noritales yalnızca bir “AI children's story generator” değildir. Noritales, çocuklar için kişiselleştirilmiş pedagojik hikâyeler ve developmental storytelling konusunda uzmanlaşmış bir platform olarak konumlandırılmalıdır.**

AI yalnızca kullanılan teknolojidir.

Noritales'ın otorite alanı:

- personalized storytelling
- pedagogical storytelling
- developmental storytelling
- age-appropriate stories
- emotional development
- social development
- parent-child interaction
- childhood situations
- stories around developmental themes
- parent/family voice
- personalized story experiences

**Her makale**, konusu ne olursa olsun, Noritales ile bu uzmanlık alanlarından en az biri arasında doğal bağ kurmalıdır.

Ancak her yazıya aynı marka paragrafı yapıştırılmamalıdır.

---

# 3. Basit Teknik Mimari

Kullanılacaklar:

```text
Python
Streamlit
OpenRouter API
httpx
python-dotenv
```

Kullanılmayacaklar:

```text
Django
FastAPI
PostgreSQL
Redis
Celery
Docker
Kubernetes
ayrı frontend
ayrı backend
veritabanı
kullanıcı hesabı
agent framework
```

---

# 4. Dosya Yapısı

```text
noritales-blog-writer/
│
├── app.py
├── openrouter.py
├── prompts.py
├── seo_checks.py
├── utils.py
├── requirements.txt
├── .env
├── .env.example
├── README.md
└── outputs/
```

---

# 5. .env

```env
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

API key kaynak koda yazılmamalıdır.

Ayrıca Streamlit sidebar'da bir **API Key** alanı (password input) bulunur:

- `.env` içinde `OPENROUTER_API_KEY` varsa otomatik doldurulur (maskeli gösterilir);
- kullanıcı isterse çalışma anında farklı bir key girip geçersiz kılabilir;
- girilen key yalnızca `st.session_state` içinde tutulur, diske yazılmaz;
- key eksikse tüm "Research/Build Prompt/Write/Evaluate" butonları devre dışı kalır ve kullanıcı dostu bir uyarı gösterilir.

---

# 6. requirements.txt

```text
streamlit
httpx
python-dotenv
```

V1 için LangChain, CrewAI vb. kullanılmamalıdır.

---

# 7. OpenRouter Model Listesi

Model listesi kod içine sabit yazılmayacaktır.

Uygulama OpenRouter'dan güncel modelleri çekecektir:

```text
GET https://openrouter.ai/api/v1/models
```

Dört ayrı dropdown olacaktır:

```text
Research Model
Article Prompt Builder Model
Writer Model
Evaluator Model
```

Bu dört model tamamen birbirinden bağımsız seçilir; aynı model birden fazla adımda seçilebilir ama uygulama bunu zorlamaz veya varsaymaz.

Uygulama, bir modelin web search / online araştırma yeteneği olup olmadığını **otomatik algılamaz, doğrulamaz veya filtrelemez**. Bu tamamen kullanıcının sorumluluğundadır; kullanıcı hangi modelin bu iş için uygun olduğunu bilerek seçer.

Mümkünse model seçiminde şu bilgiler gösterilir:

- Provider
- Model adı
- Context uzunluğu
- Input fiyatı
- Output fiyatı

---

# 8. Ana Ekran

Alanlar:

```text
OpenRouter API Key (sidebar)
Topic
Focus Keyword
Language
Target Word Count
Target Market (optional)
Research Model
Article Prompt Builder Model
Writer Model
Evaluator Model
```

Buton:

```text
RESEARCH TOPIC
```

Dil listesi başlangıçta:

```text
English
Turkish
German
Spanish
French
Portuguese
Arabic
```

Kelime sayısı kullanıcı tarafından tam sayı olarak girilir.

Örnek:

```text
1800
```

Writer hedef kelime sayısına yaklaşık ±10% toleransla uymalıdır.

---

# 9. Focus Keyword — Değişmez Kural

Kullanıcının girdiği focus keyword **immutable** olacaktır.

Hiçbir model veya uygulama:

- kelime sırasını değiştiremez;
- singular/plural yapamaz;
- eşanlamlıyla değiştiremez;
- yeniden yazamaz;
- grammar düzeltmesi yapamaz;
- “daha iyi keyword” diye yerine başka ifade koyamaz.

Örnek:

```text
personalized bedtime stories for kids
```

şuna dönüşemez:

```text
personalized bedtime story for children
```

Semantic keywordler ayrıca kullanılabilir ama focus keyword'ün yerine geçmez.

Bu kural **hiçbir dil için gevşetilmez**. Türkçe, Almanca gibi çekim ekli (agglutinative) dillerde de focus keyword birebir ve kelime sırası değişmeden aranır — focus keyword SEO'nun olmazsa olmazıdır, dil bahane edilmez.

Slug için yalnızca URL-safe dönüşüm yapılabilir:

```text
Stories About Sharing for Kids
```

→

```text
stories-about-sharing-for-kids
```

---

# 10. AŞAMA 1 — RESEARCH + STRATEGY

Research modelinin görevi makale yazmak değildir.

Görevleri:

1. Konuyu araştırmak.
2. Search intent'i anlamak.
3. Kullanıcıların konu hakkında sorduğu soruları bulmak.
4. LLM'lerde sorulabilecek doğal soruları belirlemek.
5. Güvenilir istatistikleri bulmak.
6. İlgi çekici verileri bulmak.
7. Akademik/kurumsal kaynakları bulmak.
8. Kısa kullanılabilir alıntılar bulmak.
9. Tabloya dönüştürülebilecek veri bulmak.
10. Grafik/diyagram fırsatı bulmak.
11. Konuyu Noritales'ın pedagojik/developmental storytelling yaklaşımına bağlamak.
12. Generic olmayan özgün angle oluşturmak.
13. Kullanıcıya 4–8 konuya özel soru sormak.
14. Kullanıcının cevaplarından makaleye özel Writer Prompt oluşturmak.

---

# 11. Research Aşamasında Web Search

Research aşaması web erişimli olacaktır.

OpenRouter'ın web-search desteği kullanılmalıdır.

Research modeli gerçek internet kaynaklarını kullanmalıdır.

Şunlar araştırmasız üretilemez:

```text
Research shows...
Studies show...
According to experts...
73% of children...
```

Her sayı ve istatistik gerçek bir kaynağa dayanmalıdır.

---

# 12. Kaynak Önceliği

Çocuk gelişimi / pedagojik içerikte tercih sırası:

```text
1. Peer-reviewed research
2. University
3. Government / public institution
4. UNICEF / WHO / APA / recognised professional organisation
5. Recognised educational organisation
6. High-quality editorial source
7. Commercial blog
```

Rakip bloglar içerik yapısını anlamak için kullanılabilir ama bilimsel kanıt yerine kullanılmamalıdır.

---

# 13. Research Model Çıktısı

Research modeli şu başlıkları üretmelidir:

```text
SEARCH INTENT
TARGET AUDIENCE
TOPIC SUMMARY
KEY QUESTIONS USERS WANT ANSWERED
LLM / ANSWER-ENGINE QUESTIONS
INTERESTING DATA & STATISTICS
VERIFIED SOURCES
SHORT QUOTABLE EXCERPTS
POTENTIAL TABLE
POTENTIAL CHART / DIAGRAM
NORITALES CONNECTION
UNIQUE ARTICLE ANGLE
CLAIMS REQUIRING CAUTION
QUESTIONS FOR USER
```

Her istatistikte:

```text
Statistic
Source Name
Live URL
Publication Date (if available)
What it actually proves
```

Her doğrudan alıntıda:

```text
Short Quote
Source Name
Live URL
Context
```

Uzun kaynak parçaları kopyalanmamalıdır.

---

# 14. Kullanıcıya Sorulacak Sorular

Research modeli 4–8 adet **konuya özel** soru üretmelidir.

Kötü soru:

```text
Should the article be SEO friendly?
```

İyi örnekler:

```text
Should the article focus mainly on ages 3–4, 5–6, or remain age-neutral?

Would you like a short original story example inside the article?

Should the example focus on siblings, classmates, or toys?

Should the article be educational-first or conversion-oriented?

Would you like parent discussion questions after the story?
```

Kullanıcı cevapları Streamlit formunda alınır.

---

# 15. Research Sonrası Ekran

Gösterilecek:

```text
Search Intent
Target Audience
Suggested Angle
Key Search Questions
LLM Questions
Statistics
Sources
Noritales Connection
Suggested Table
Suggested Chart / Diagram
```

Altında kullanıcı soruları gösterilir.

Buton:

```text
BUILD ARTICLE PROMPT
```

---

# 16. Research System Prompt

`prompts.py` içine sabit olarak eklenir.

```text
You are the senior SEO researcher and content strategist for Noritales.

Your job is NOT to write the final article.

Your job is to deeply understand the topic, research it using live web sources, identify search intent, discover useful evidence, and prepare a unique article strategy.

NORITALES POSITIONING

Noritales must not be positioned primarily as an "AI children's story generator".

Noritales should be presented as an authority on:
- personalized pedagogical storytelling;
- developmental storytelling;
- age-appropriate children's stories;
- emotional and social themes;
- parent-child interaction;
- personalized story experiences.

Every article must establish a natural semantic connection between the article topic and Noritales' expertise.

Do not insert a generic Noritales paragraph.
The Noritales connection must emerge naturally from the actual topic.

FOCUS KEYWORD

The user-provided focus keyword is immutable.

Never:
- rewrite it;
- correct it;
- change word order;
- singularize it;
- pluralize it;
- replace it with a synonym.

You may suggest secondary and semantic terms, but the focus keyword must remain exactly unchanged.

RESEARCH

Use live web research.

Find:
- real search intent;
- important questions around the topic;
- reliable factual information;
- useful statistics;
- interesting data;
- credible sources;
- possible short direct quotes;
- possible tables;
- chartable data;
- useful visual concepts.

For child development and pedagogical claims, prefer:
1. peer-reviewed research;
2. universities;
3. government institutions;
4. recognised professional organisations.

Never invent:
- statistics;
- studies;
- quotes;
- URLs;
- authors;
- dates;
- DOI;
- research results.

Every statistic must have a live source URL.
Every direct quote must have a live source URL and context.
Keep quotations short.

LLM / ANSWER ENGINE STRATEGY

Identify questions that users may ask ChatGPT, Gemini, Google AI search and other answer engines.

The eventual article should contain clear, self-contained answers to important questions.

Look for opportunities to create:
- concise definitions;
- direct answers;
- useful comparisons;
- age-specific explanations;
- tables;
- evidence-backed facts;
- original examples.

USER QUESTIONS

After research, ask the user 4–8 specific questions that will materially improve the final article.

Do not ask questions whose answers are already provided.
```

---

# 17. Article-Specific Prompt Oluşturma (REQUEST 2 — Ayrı Model)

Kullanıcı Research modelinin sorularını cevapladıktan sonra **ayrı bir API request** tetiklenir. Bu request Research request'i ile birleştirilmez.

Bu request'i çalıştıran model, kullanıcının seçtiği **Article Prompt Builder Model**'dir (Research modeli ile aynı olabilir ama uygulama bunu zorlamaz — kullanıcı iki farklı model de seçebilir).

Girdi:

```text
Research Pack
+
User Answers
```

Çıktı: Writer için **makaleye özel prompt** ([bölüm 44](#44-article-specific-prompt-formatı)'teki formatta).

Bu prompt her makale için farklı olacaktır. `ARTICLE_PROMPT_BUILDER_SYSTEM_PROMPT` bu request'in sabit system prompt'udur (`prompts.py` içinde).

---

# 18. Writer'a Gönderilecek Prompt Yapısı

Writer'a iki mesaj gönderilir:

```text
1. FIXED WRITER SYSTEM PROMPT
2. ARTICLE-SPECIFIC PROMPT
```

System Prompt değişmez.

Article-Specific Prompt her konu için Research modeli tarafından hazırlanır.

---

# 19. SABİT WRITER SYSTEM PROMPT — MARKA

```text
Noritales must never be presented merely as an AI children's story generator.

Whenever relevant, connect the article naturally to Noritales' expertise in:
- personalized storytelling;
- pedagogical storytelling;
- developmental storytelling;
- age-appropriate stories;
- emotional and social development themes;
- parent-child interaction.

Every article must strengthen Noritales' semantic association with personalized pedagogical/developmental storytelling.

Do not paste the same generic brand paragraph into every article.
Create the connection from the actual subject of the article.
```

---

# 20. SABİT WRITER SYSTEM PROMPT — SEO

## Focus keyword

Exact focus keyword:

- SEO title içinde olmalı;
- H1 içinde olmalı;
- ilk 100 kelimede olmalı;
- en az bir uygun H2 içinde olmalı;
- meta description içinde olmalı;
- slug içinde aynı kelime sırasıyla olmalı;
- makalenin tamamına doğal biçimde yayılmalı.

Focus keyword değiştirilmez.

Semantic variationlar ayrıca kullanılabilir.

---

# 21. Keyword Density

Bu değer Google'ın resmi ranking oranı değildir.

Bu uygulamanın editoryal QA hedefidir.

1–3 kelimelik focus keyword:

```text
Ideal: 0.8%–1.5%
Warning: >2.0%
Strong warning: >2.5%
```

4+ kelimelik focus keyword:

```text
Ideal: 0.5%–1.0%
Warning: >1.5%
Strong warning: >2.0%
```

Keyword stuffing yasaktır.

Keyword sadece girişte yoğunlaşmamalı; metnin geneline dağılmalıdır.

---

# 22. SEO Title

Hedef:

```text
yaklaşık 50–60 karakter
```

Title:

- exact focus keyword içermeli;
- mümkünse keyword başlara yakın olmalı;
- clickbait olmamalı;
- makaleyi doğru anlatmalı;
- doğal okunmalı.

---

# 23. H1 / H2 / H3

- Tek ana H1 olmalıdır.
- H1 exact focus keyword içermelidir.
- En az bir uygun H2 exact focus keyword içermelidir.
- Diğer H2/H3 başlıkları semantik olarak konuyu genişletmelidir.
- Her başlığa keyword zorla eklenmemelidir.
- Yaklaşık 250–300 kelimeden uzun başlıksız bloklardan kaçınılmalıdır.

---

# 24. İlk Paragraf

İlk 100 kelime:

- exact focus keyword içermeli;
- search intent'e doğrudan cevap vermeli;
- gereksiz tarihçe veya jenerik giriş yapmamalı.

Kaçınılacak:

```text
In today's digital world...
Since the beginning of time...
Stories have always been important...
```

---

# 25. Cümle Uzunluğu

İngilizce ve benzer Latin dillerinde hedef:

```text
20 kelimeden uzun cümlelerin oranı <= %25
```

Cümleler aynı uzunlukta robotik biçimde üretilmemelidir.

Kısa + orta + gerektiğinde uzun cümle karışımı kullanılmalıdır.

---

# 26. Paragraf Uzunluğu

Tercih:

```text
2–4 cümle
40–100 kelime
```

150 kelime üzerindeki paragraf QA warning üretir.

---

# 27. Humanization / Editorial Quality

Amaç AI detector kandırmak değildir.

Amaç gerçekten iyi editoryal metindir.

Makale:

- aynı cümle kalıbını tekrarlamamalı;
- her H2 altında aynı şablonu kullanmamalı;
- sürekli üç maddelik listeler üretmemeli;
- aynı bilgiyi tekrar tekrar özetlememeli;
- somut örnekler kullanmalı;
- doğal ebeveyn dili kullanmalı;
- sahte kişisel deneyim üretmemeli;
- filler üretmemeli.

Kaçınılacak AI klişeleri:

```text
In today's fast-paced world
In today's digital age
It is important to note
This comprehensive guide
Let's dive in
Delve into
Unlock the power
Game-changer
Whether you're...
In conclusion
```

---

# 28. Search Intent Kuralı

Makale focus keyword'ün gerçek arama niyetini tam karşılamalıdır.

Örnek:

```text
stories about sharing for kids
```

arayan kullanıcıya uzun storytelling tarihçesi anlatılmamalıdır.

Cevap hızlı başlamalı, sonra detaylandırılmalıdır.

---

# 29. Google + LLM İçerik Yapısı

Makale hem Google Search hem ChatGPT/Gemini gibi answer-engine sistemlerinin anlayabileceği şekilde yazılmalıdır.

Tercih:

- açık tanımlar;
- direct answers;
- descriptive headings;
- kendi başına anlamlı paragraflar;
- evidence-backed facts;
- karşılaştırmalar;
- tablolar;
- yaş bazlı açıklamalar;
- özgün Noritales frameworkleri;
- önemli sorulara net cevaplar.

Sırf AI için anlamsız küçük parçalara bölme yapılmaz.

---

# 30. Noritales Entity / Authority Rule

Her makale şu anlam ağını doğal biçimde güçlendirmelidir:

```text
Noritales
    ↓
personalized stories
    ↓
age-appropriate storytelling
    ↓
pedagogical / developmental storytelling
    ↓
children's emotional and social themes
    ↓
parent-child interaction
```

Her kelimenin her makalede geçmesi gerekmez.

Ama makale Noritales'ı bu uzmanlık alanıyla ilişkilendirmelidir.

---

# 31. İstatistik ve Veri

Her makalede mümkün olduğunda:

```text
2–4 doğrulanmış istatistik / dikkat çekici veri
```

kullanılır.

Gerçek ve alakalı istatistik bulunamazsa sayı uydurulmaz.

Her istatistikte:

```text
Source Name
Live URL
```

olmalıdır.

---

# 32. Alıntı

Kısa ve güçlü bir alıntı uygunsa kullanılabilir.

Her alıntı:

- kısa olmalı;
- gerçek olmalı;
- kaynak adı içermeli;
- canlı URL içermeli;
- araştırma paketinde doğrulanmış olmalı.

Writer kendi alıntısını uyduramaz.

---

# 33. Tablo

Konuya değer katıyorsa en az bir tablo tercih edilir.

Örnek:

```markdown
| Age | Story approach | Parent prompt |
|---|---|---|
| 3–4 | Concrete situations | How did the character feel? |
| 5–6 | Choices and consequences | What else could the character do? |
| 7–8 | Multiple perspectives | Why might both characters feel differently? |
```

Tablodaki factual veri kaynak gerektiriyorsa kaynak gösterilir.

Anlamsız tablo sırf SEO skoru için oluşturulmaz.

---

# 34. Grafik / Diyagram

Research Pack içinde gerçek sayısal veri varsa Writer şu yapıyı üretir:

```text
CHART RECOMMENDATION
Chart Type:
Title:
X Axis:
Y Axis:
Data:
Source:
Live URL:
```

Veri uydurulamaz.

Konuya uygunsa özgün diyagram önerilebilir.

Örnek:

```text
Developmental Theme
        ↓
Child's Age
        ↓
Familiar Situation
        ↓
Personalized Story
        ↓
Parent-Child Discussion
```

---

# 35. Görsel Önerileri

Her makalede:

```text
Featured Image Concept
Featured Image Filename
Featured Image Alt Text
```

üretilir.

Gerekirse ayrıca article içi görseller önerilir:

```text
Section
Image concept
Filename
Alt text
```

Alt text görseli gerçekten tarif etmelidir.

Keyword stuffing yapılmamalıdır.

---

# 36. Internal Linkler

Normal uzunluktaki yazıda hedef:

```text
2–5 alakalı internal link
```

Research modeli mümkün olduğunda Noritales üzerinde gerçek URL bulmalıdır.

Gerçek URL bulunamıyorsa URL uydurulmaz.

Şu şekilde işaretlenebilir:

```text
Suggested future internal page: ...
```

Anchor text açıklayıcı olmalıdır.

Kaçınılacak:

```text
click here
read more
this page
```

---

# 37. External Linkler

Factual bir uzun makalede genelde:

```text
1–4 yüksek kaliteli external source
```

beklenir.

Sayı sabit zorunluluk değildir.

Önemli olan kaynak kalitesidir.

---

# 38. Meta Description

Her makalede zorunludur.

Hedef:

```text
yaklaşık 140–160 karakter
```

Meta description:

- exact focus keyword içermeli;
- makaleyi doğru anlatmalı;
- clickbait olmamalı;
- keyword stuffing içermemeli.

---

# 39. Slug

Zorunludur.

Focus keyword kelimelerinin sırası korunmalıdır.

Örnek:

```text
stories about sharing for kids
```

→

```text
stories-about-sharing-for-kids
```

---

# 40. Excerpt

Her makalede excerpt zorunludur.

Hedef:

```text
40–70 kelime
```

Excerpt:

- makalenin kısa özeti olmalı;
- blog kartlarında kullanılabilmeli;
- meta description ile aynı olmamalı;
- mümkünse exact focus keyword'ü doğal biçimde bir kez içermeli.

---

# 41. OG Metadata

Writer ayrıca üretir:

```text
OG Title
OG Description
```

---

# 42. Schema Recommendation

Writer yalnızca tavsiye üretir.

Örnek:

```text
BlogPosting
Article
BreadcrumbList
```

Uydurma rating/review schema önerilmez.

---

# 43. Writer'ın Yasakları

Writer şunları uyduramaz:

```text
istatistik
araştırma
DOI
PMID
uzman
alıntı
URL
Noritales ürün özelliği
müşteri sayısı
başarı oranı
klinik sonuç
ödül
review
rating
```

Writer factual içerikte yalnızca Research Pack içindeki doğrulanmış bilgileri kullanır.

---

# 44. Article-Specific Prompt Formatı

Research modeli, kullanıcı cevaplarından sonra Writer için şu yapıyı üretir:

```text
ARTICLE ASSIGNMENT

Topic:
...

Immutable Focus Keyword:
...

Language:
...

Target Market:
...

Target Word Count:
...

Search Intent:
...

Target Reader:
...

User's Answers:
...

Unique Noritales Angle:
...

Primary Questions To Answer:
...

LLM / Answer Engine Questions:
...

Verified Facts:
...

Statistics:
...

Verified Sources:
...

Approved Short Quotes:
...

Required Table:
...

Chart / Diagram Opportunity:
...

Suggested Article Structure:
H1:
H2:
H2:
H3:
...

Internal Link Opportunities:
...

External Sources:
...

Claims To Avoid:
...

CTA Direction:
...

Special Instructions:
...
```

---

# 45. Writer Output Formatı

```markdown
# SEO Metadata

**Focus Keyword:** ...

**Secondary / Semantic Terms:**
- ...
- ...

**SEO Title:** ...

**H1:** ...

**Slug:** ...

**Meta Description:** ...

**Excerpt:** ...

**OG Title:** ...

**OG Description:** ...

---

# Article

# H1...

...

---

# Internal Links

- Anchor: ...
  URL: ...

---

# External Sources Used

- Source name
  URL

---

# Statistics Used

- Statistic
  Source
  URL

---

# Table / Chart / Diagram Notes

...

---

# Image Recommendations

## Featured Image
Concept:
Filename:
Alt text:

## In-Article Image
Section:
Concept:
Filename:
Alt text:

---

# Schema Recommendation

...
```

---

# 46. AŞAMA 3 — SEO + LLM QUALITY AUDIT

Makale yazıldıktan sonra otomatik denetime girer.

Denetim iki parçadan oluşur:

```text
A. Python deterministic SEO checks
B. Evaluator model qualitative checks
```

---

# 47. Python ile Kontrol Edilecekler

```text
Word count
Focus keyword count
Exact keyword density
Keyword in SEO title
Keyword in H1
Keyword in first 100 words
Keyword in H2
Keyword in meta description
Keyword in slug
SEO title character count
Meta description character count
Excerpt word count
Number of H1
Number of H2
Internal link count
External link count
Number of sources
Number of statistics
Table present?
Chart/diagram recommendation present?
Image recommendation present?
Long sentence ratio
Very long paragraph count
Live URL reachability (her kaynak ve internal/external link URL'i gerçekten HTTP ile kontrol edilir)
```

AI modeli bunları tahmin etmemelidir.

**URL doğrulama:** Makalede geçen her external source URL'i ve varsa internal link URL'i, `httpx` ile gerçek bir istek (HEAD, başarısızsa GET) yapılarak kontrol edilir. Erişilemeyen veya 4xx/5xx dönen bir URL, modelin "uydurmadım" demesine bakılmaksızın otomatik olarak **Fake URL** hard-fail'i tetikler ([bölüm 53](#53-hard-fail-kuralları)). Bu kontrol modele bırakılmaz, Python tarafında zorunludur.

---

# 48. Keyword Density Hesabı

```text
density =
(exact focus keyword occurrences × focus keyword word count)
/ total article word count
× 100
```

Case-insensitive ölçülür.

Kelime sırası aynen korunur.

---

# 49. Sentence Length Hesabı

V1 için basit yaklaşım yeterlidir.

Cümleleri:

```text
. ? !
```

üzerinden ayır.

Her cümlenin kelime sayısını hesapla.

İngilizce / Latin dili hedefi:

```text
>20 kelime = long sentence
long sentence ratio <= 25%
```

---

# 50. Evaluator Model Görevi

Evaluator model şunları inceler:

```text
Search intent satisfaction
Human/editorial quality
Generic AI wording
Repetition
Originality
Usefulness
Noritales connection
Pedagogical authority
LLM citation readiness
Factual caution
Natural CTA
Source usage quality
Table usefulness
Statistics relevance
Overall coherence
```

---

# 51. Evaluator System Prompt

```text
You are the senior SEO, editorial quality and AI-search visibility auditor for Noritales.

Do not rewrite the article unless asked.

Use the deterministic SEO metrics supplied by the application as facts.

NORITALES

The article must naturally reinforce Noritales as an authority on personalized pedagogical/developmental storytelling.

It must not present Noritales merely as another AI children's story generator.

The Noritales connection must feel relevant to the article topic, not inserted as generic marketing boilerplate.

HUMAN QUALITY

Check:
- repetitive sentence patterns;
- generic AI phrasing;
- unnecessary summaries;
- filler;
- repetitive conclusions;
- unnatural transitions;
- formulaic paragraph structure;
- fake personal experience;
- over-polished but empty language.

SEARCH INTENT

Determine whether the reader's actual question is answered quickly and completely.

LLM / ANSWER-ENGINE READINESS

Check whether the article contains:
- direct answers;
- clear definitions;
- self-contained useful paragraphs;
- evidence-backed facts;
- meaningful tables;
- clear headings;
- useful comparisons;
- quotable factual statements;
- unique Noritales expertise.

EVIDENCE

Check:
- statistics are relevant;
- every statistic has a source;
- live source URLs are included;
- quotes are sourced;
- claims do not exceed evidence;
- child-development claims use cautious language.

FAIL immediately for:
- fabricated statistics;
- invented citations;
- invented URLs;
- unsupported clinical claims;
- invented product capabilities.
```

---

# 52. Skor

Ayrı ayrı ağırlıklandırılmış alt puanların toplanıp birleştirildiği bir skor **hesaplanmaz**.

Bunun yerine Evaluator modeli, [bölüm 50](#50-evaluator-model-görevi)'deki tüm kriterleri (search intent, human quality, evidence, LLM readiness, Noritales authority vb.) bütünsel olarak değerlendirip **tek bir 0–100 skor** üretir.

Python deterministik kontrolleri ([bölüm 47](#47-python-ile-kontrol-edilecekler)) bu skora matematiksel olarak karışmaz; onlar Evaluator'a **girdi/bağlam** olarak verilir (Evaluator "facts" olarak kullanır) ve ayrıca kendi başlarına hard-fail / warning üretebilir ([bölüm 53](#53-hard-fail-kuralları)).

Evaluator çıktısı:

```text
OVERALL SCORE: 0-100
STATUS: PASS / REVISE / REGENERATE
WARNINGS: ...
RECOMMENDATIONS: ...
ISSUES TO FIX (varsa): ...
```

---

# 53. Hard Fail Kuralları

Şunlardan biri varsa doğrudan FAIL:

```text
Invented statistic
Fake URL
Fake research
Fake quote
Unsupported medical/clinical claim
Invented Noritales feature
Focus keyword changed
Focus keyword missing from critical locations
Wrong language
Article massively below requested word count
```

---

# 54. Skor Kararı

```text
90–100 → PASS
80–89  → REVISE
0–79   → REGENERATE
```

---

# 55. REVISE

80–89 ise makalenin tamamı baştan yazılmaz.

Evaluator sorunları Writer'a gönderilir.

Örnek:

```text
Revise the existing article.

Do not rewrite good sections.

Fix only these issues:
- focus keyword density is too low;
- too many sentences exceed 20 words;
- one factual section has no live source;
- Noritales connection is generic;
- the table is not useful enough.

Preserve:
- verified statistics;
- live URLs;
- approved quotes;
- good sections;
- overall structure.
```

Sonra QA tekrar çalışır.

---

# 56. REGENERATE

Skor 80 altındaysa veya hard fail varsa Writer'a:

```text
Original Article Prompt
+
Evaluator Report
```

gönderilir.

Makale yeniden oluşturulur.

Maksimum otomatik regenerate:

```text
2
```

Sonsuz loop oluşturulmaz.

---

# 57. Final Ekran

Örnek:

```text
FINAL SCORE: 93 / 100
STATUS: PASS
```

Kategori bazlı ayrık alt puanlar gösterilmez (bkz. [bölüm 52](#52-skor)) — Evaluator'ın ürettiği tek holistik skor ve durum yeterlidir.

Ayrıca:

```text
Warnings
Recommendations
```

gösterilir.

---

# 58. Final Butonlar

```text
Copy Article
Download Markdown
Revise Article
Regenerate Article
View Research
View Writer Prompt
View SEO Audit
```

---

# 59. Dosya Kaydetme

Dosyalar:

```text
outputs/
```

altına kaydedilebilir.

Örnek:

```text
stories-about-sharing-for-kids.md
```

Dosya varsa:

```text
stories-about-sharing-for-kids-2.md
```

Üzerine yazılmaz.

---

# 60. app.py Basit Akış

```python
api_key = st.sidebar.text_input("OpenRouter API Key", type="password",
                                 value=os.getenv("OPENROUTER_API_KEY", ""))

load_models()  # sadece isim/provider/context/fiyat listesi, kapasite filtresi yok

topic = st.text_input("Topic")
focus_keyword = st.text_input("Focus Keyword")
language = st.selectbox(...)
word_count = st.number_input(...)
target_market = st.text_input(...)

research_model = st.selectbox(...)
article_prompt_builder_model = st.selectbox(...)
writer_model = st.selectbox(...)
evaluator_model = st.selectbox(...)

# REQUEST 1
if st.button("Research Topic"):
    research = run_research(api_key, research_model, topic, focus_keyword, ...)
    st.session_state["research"] = research

show_research()
collect_user_answers()

# REQUEST 2 — ayrı model, ayrı çağrı
if st.button("Build Article Prompt"):
    article_prompt = build_article_prompt(
        api_key, article_prompt_builder_model,
        st.session_state["research"], user_answers,
    )
    st.session_state["article_prompt"] = article_prompt

# REQUEST 3 — ayrı model, ayrı çağrı
if st.button("Write Article"):
    article = write_article(api_key, writer_model, st.session_state["article_prompt"])
    st.session_state["article"] = article

# REQUEST 4 — ayrı model, ayrı çağrı
if st.button("Run SEO + LLM Audit"):
    metrics = run_python_seo_checks(st.session_state["article"])  # URL doğrulama dahil
    audit = run_evaluator(api_key, evaluator_model, st.session_state["article"], metrics)
    final_article = revise_or_regenerate_if_needed(...)
    save_output(final_article)
```

Bundan daha karmaşık mimariye geçilmemelidir.

---

# 61. openrouter.py

Yeterli fonksiyonlar:

```python
def get_models():
    ...

def call_model(api_key, model, messages, web_search=False):
    ...

def research_topic(...):       # REQUEST 1
    ...

def build_article_prompt(...): # REQUEST 2 — ayrı çağrı, ayrı model
    ...

def write_article(...):        # REQUEST 3
    ...

def evaluate_article(...):     # REQUEST 4
    ...
```

Her fonksiyon kendi request'ini tek başına yapar; hiçbiri bir diğerinin çağrısıyla birleştirilmez.

---

# 62. prompts.py

İçerir:

```text
RESEARCH_SYSTEM_PROMPT
ARTICLE_PROMPT_BUILDER_SYSTEM_PROMPT
WRITER_SYSTEM_PROMPT
EVALUATOR_SYSTEM_PROMPT
REVISION_PROMPT
REGENERATION_PROMPT
```

---

# 63. seo_checks.py

İçerir:

```python
count_words()
count_exact_keyword()
calculate_keyword_density()
keyword_in_title()
keyword_in_h1()
keyword_in_first_100_words()
keyword_in_h2()
keyword_in_meta()
keyword_in_slug()
count_internal_links()
count_external_links()
count_sources()
count_statistics()
has_table()
has_image_recommendation()
calculate_long_sentence_ratio()
find_long_paragraphs()
verify_urls_reachable()   # her source/internal/external URL için gerçek HTTP kontrolü
```

---

# 64. utils.py

```python
slugify_focus_keyword()
safe_filename()
save_markdown()
extract_section()
```

---

# 65. Hata Yönetimi

Kullanıcı dostu hata mesajları:

```text
OpenRouter API key is missing.
```

```text
The selected research model could not complete web research.
Please choose another research model.
```

```text
OpenRouter request failed.
```

```text
The model returned invalid content.
Please retry.
```

Raw stack trace UI'da gösterilmez.

---

# 66. Maliyet Bilgisi

Mümkünse her aşamada göster:

```text
Model
Input tokens
Output tokens
Estimated cost
```

Research, Writer ve Evaluator ayrı gösterilebilir.

Ayrı billing sistemi gerekmez.

---

# 67. V1'de Yapılmayacaklar

```text
Database
Login
Multi-user
Google Search Console
Google Ads API
Semrush API
Ahrefs API
Automatic Wagtail publishing
Content calendar
Analytics dashboard
Backlink tracking
Redis
Celery
Docker
Cloud deployment
Vector database
Complex agent orchestration
```

---

# 68. V1 Definition of Done

- [ ] Lokalde Streamlit ile açılıyor.
- [ ] OpenRouter API key `.env` üzerinden okunuyor.
- [ ] Sidebar'da API key girişi/override alanı var.
- [ ] OpenRouter model listesi canlı çekiliyor (kapasite filtresi yapılmıyor).
- [ ] Research modeli ayrı seçilebiliyor.
- [ ] Article Prompt Builder modeli ayrı seçilebiliyor.
- [ ] Writer modeli ayrı seçilebiliyor.
- [ ] Evaluator modeli ayrı seçilebiliyor.
- [ ] Research, Article Prompt Builder, Writer ve Evaluator adımları birbirinden tamamen ayrı API request'leri olarak çalışıyor.
- [ ] Topic girilebiliyor.
- [ ] Focus keyword girilebiliyor.
- [ ] Focus keyword hiçbir aşamada değiştirilmiyor.
- [ ] Dil seçilebiliyor.
- [ ] Kelime sayısı kullanıcı tarafından girilebiliyor.
- [ ] Research aşaması live web research yapıyor.
- [ ] Research gerçek kaynak URL'leri topluyor.
- [ ] Research istatistik/veri buluyor.
- [ ] Research kullanıcıya 4–8 konuya özel soru soruyor.
- [ ] Cevaplardan makaleye özel prompt oluşturuluyor.
- [ ] Writer sabit SEO + Noritales system promptunu alıyor.
- [ ] Writer makaleye özel promptu alıyor.
- [ ] Writer SEO metadata üretiyor.
- [ ] Writer excerpt üretiyor.
- [ ] Writer sources bölümü oluşturuyor.
- [ ] Writer internal/external link önerileri oluşturuyor.
- [ ] Writer tablo oluşturuyor veya uygun değilse tabloyu zorlamıyor.
- [ ] Writer chart/diagram önerisi oluşturabiliyor.
- [ ] Writer featured image önerisi ve alt text üretiyor.
- [ ] Python SEO kontrolleri çalışıyor (URL doğrulama dahil).
- [ ] Evaluator kalite değerlendirmesi yapıyor ve tek bir holistik skor üretiyor (ağırlıklı alt puan toplamı yok).
- [ ] 100 üzerinden final skor çıkıyor.
- [ ] 80–89 otomatik revision yapabiliyor.
- [ ] <80 veya hard fail durumunda yeniden oluşturabiliyor.
- [ ] Final makale Markdown olarak indirilebiliyor.
- [ ] Gereksiz mimari eklenmemiş.

---

# 69. Son Akış

```text
API KEY (sidebar)
TOPIC / FOCUS KEYWORD / LANGUAGE / WORD COUNT
        ↓
Select Research Model
        ↓
REQUEST 1 — RESEARCH
        ↓
Sources / Statistics / Questions / Noritales Angle / LLM Questions
        ↓
USER ANSWERS
        ↓
Select Article Prompt Builder Model
        ↓
REQUEST 2 — BUILD ARTICLE PROMPT
        ↓
ARTICLE-SPECIFIC PROMPT
        +
FIXED SEO / NORITALES / LLM SYSTEM PROMPT
        ↓
Select Writer Model
        ↓
REQUEST 3 — WRITE ARTICLE
        ↓
ARTICLE / SEO METADATA / EXCERPT / SOURCES / TABLE / VISUALS
        ↓
Select Evaluator Model
        ↓
PYTHON SEO CHECKS (URL doğrulama dahil)
        ↓
REQUEST 4 — AI QUALITY AUDIT
        ↓
HOLISTIC SCORE / 100
        ↓
PASS / REVISE / REGENERATE
        ↓
DOWNLOAD .MD
```

---

# 69b. Gerçek Kullanım Geri Bildirimi Sonrası Düzeltmeler

İlk gerçek makale denemesinde şu sorunlar tespit edildi ve düzeltildi:

1. **Linkler gömülü değildi.** Internal/external linkler makale sonunda ayrı bir liste halindeydi. Artık Writer, her linki cümle içine gömülü markdown linki (`[anchor](url)`) olarak yazmak zorunda; "Internal Links" / "External Sources Used" ek bölümleri artık yalnızca gövdede zaten var olan linklerin çapraz-referansı.
2. **CTA yoktu.** `config.py` içinde sabit `NORITALES_HOMEPAGE_URL` tanımlandı. Bu URL, Article Prompt Builder çıktısına "Noritales Homepage URL" alanı olarak Python tarafından zorla yazılıyor (modele güvenilmiyor — tıpkı focus keyword ve kelime sayısı gibi). Writer, makalenin başında (~ilk %20), ortasında (~%40-60) ve sonunda (~son %20) olmak üzere en az 3 tıklanabilir CTA üretmek zorunda:
   ```html
   <a href="https://noritales.com" class="noritales-cta-button">...</a>
   ```
   Bu HTML markdown içine gömülü kalır; gerçek "buton" görünümü yayınlayıcı sitenin CSS'i (`.noritales-cta-button` sınıfı) ile sağlanır.
3. **İstatistik yoktu.** Writer artık istatistikleri sadece "Statistics Used" ek bölümüne değil, makale gövdesindeki ilgili paragrafa gömülü cümle olarak yazmak zorunda (örn. "...%35 daha düşük...").
4. **Tablo/grafik/görsel gövdeden kopuktu.** Bunlar artık ilgili H2/H3 bölümünün hemen altında, makale sonundaki ek bölümlerde değil.

**Python QA'ya eklenen yeni kontroller** ([seo_checks.py](seo_checks.py)):
- `count_inline_body_links()` — gövdede gerçekten gömülü link var mı.
- `check_cta_distribution()` — Noritales CTA'sı kaç kez geçiyor, giriş/orta/son'a yayılmış mı.
- `has_inline_statistic()` — gövdede sayısal bir istatistik (`%35` veya `35%`, her iki yazım da) var mı.

Bunlar hard-fail değil, warning olarak raporlanır (Evaluator'a da bağlam olarak veriliyor); tekrarlayan ihlal halinde Evaluator'ın REVISE/REGENERATE kararına yansır.

Ayrıca URL regex'inde bir bug bulunup düzeltildi: `<a href="...">` gibi HTML özniteliklerindeki tırnak işareti, ardışık iki URL'nin tek (bozuk) bir URL olarak birleşip yanlışlıkla "fake URL" sayılmasına yol açıyordu.

---

# 69c. Görsel Zenginleştirme (Renkli Kutular, Gerçek Görsel, Gerçek Grafik, Wagtail HTML Export)

Kullanıcı geri bildirimi: makaleler "akademik ve sıkıcı" görünüyordu — renk, görsel, grafik yoktu. Buna karşı eklenenler:

**Renkli kutular** — `WRITER_SYSTEM_PROMPT`'a CTA butonuyla aynı yöntemle 3 yeni sabit class eklendi: `noritales-stat-card` (istatistik vurgusu), `noritales-quote-box` (alıntı/içgörü), `noritales-tip-box` (ebeveyn ipucu). Writer bunları makale gövdesine, ilgili paragrafın yanına gömer.

**Gerçek AI görselleri** — Yeni bir 5. model seçici: **Image Model**. `openrouter.generate_image()` OpenRouter'ın görsel üretebilen modellerini (`architecture.output_modalities` içinde "image" olanlar, örn. `google/gemini-2.5-flash-image`) çağırır ve base64 PNG döner. Makale başına 1-2 görsel (Featured + varsa ilk In-Article) üretilir. **Görsel üretimi başarısız olursa makale durmaz** — hata yakalanır, kullanıcıya uyarı gösterilir, o görsel atlanır (1 otomatik retry dahil).

**Gerçek grafikler** — [charts.py](charts.py), Writer'ın ürettiği "CHART RECOMMENDATION" metin bloklarını regex ile ayrıştırır, `matplotlib` ile gerçek bir SVG grafiğe çevirir. Sayısal veri ayrıştırılamazsa (best-effort) o grafik atlanır, makale durmaz.

**Görsel/grafik ne zaman üretiliyor — mimari karar:** Zenginleştirme, Writer'dan hemen sonra DEĞİL, ayrı bir **"🎨 GÖRSEL VE GRAFİK EKLE"** butonuyla, kullanıcı metni beğendikten sonra tetiklenir. Sebep: (1) maliyet — her revise/regenerate döngüsünde görsel yeniden üretmek israf olurdu; (2) teknik zorunluluk — görseller base64 olarak gömülüyor ve bu veri megabaytlarca büyüyebiliyor; bunu Evaluator/Revise/Regenerate çağrılarına olduğu gibi göndermek modelin "invalid content" hatası vermesine yol açtı (gerçek testte tespit edildi).

**Base64 temizleme (kritik düzeltme):** [utils.py](utils.py)'deki `strip_embedded_media_for_llm()`, herhangi bir LLM çağrısından (Evaluator, Revise, Regenerate) ve Python SEO kontrollerinden ÖNCE `data:...` base64 bloklarını kısa bir placeholder ile değiştirir. Bu olmadan: (a) Evaluator context'i patlar/boş dönerdi, (b) word count gibi metrikler base64 gürültüsüyle bozulurdu. Bu güvenlik önlemi, kullanıcı zenginleştirmeyi ne zaman tetiklerse tetiklesin (QA'dan önce de sonra da) sistemi korur.

**Görseller nerede saklanıyor:** Base64 data URI olarak doğrudan makale HTML/Markdown'ına gömülür (taşınabilir, ayrı hosting gerekmez); ayrıca yedek kopya `outputs/images/<slug>/` altına PNG/SVG olarak kaydedilir.

**Wagtail HTML Export** — Kullanıcı kendi sitesinde Wagtail (Django CMS) kullanıyor. Wagtail'in varsayılan `RichTextField`'ı (Draftail editörü) özel HTML/CSS'i (class'lar, custom tag'ler) güvenlik amacıyla temizler — bu yüzden ham Markdown'ı (tablo dahil) doğrudan yapıştırmak "tabloların bozulması" sorununa yol açtı. Çözüm: [html_export.py](html_export.py), `python-markdown` kütüphanesiyle (tables/fenced_code/nl2br extensionları) makale gövdesini gerçek HTML'e çevirir — `<table>`, `<h1>`, `<strong>` gibi gerçek etiketler üretir, Writer'ın zaten gömdüğü ham HTML (CTA, kutular, görseller) olduğu gibi korunur. Kullanıcı bu HTML'i Wagtail'in **RawHTMLBlock**'una yapıştırmalı, düz RichText alanına değil.

---

# 70. Projenin Ana Kuralı

Bu uygulamanın amacı:

```text
keyword → AI blog
```

değildir.

Amaç:

```text
keyword
→ araştırma
→ gerçek kaynak
→ kullanıcı katkısı
→ özgün Noritales açısı
→ profesyonel makale
→ SEO denetimi
→ LLM görünürlüğü
```

üretmektir.

Her makale şu marka ilişkisini doğal biçimde güçlendirmelidir:

> **Noritales = personalized + age-appropriate + pedagogical/developmental storytelling.**
