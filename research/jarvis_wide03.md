# Facet: Bellek, RAG ve Kişiselleştirme

## Key Findings

- **Vektör veritabanları** pazarı 2026 itibarıyla LanceDB, Qdrant, Milvus, Weaviate, Chroma ve pgvector olmak üzere belirgin segmentlere ayrılmıştır. LanceDB 30M$ Series A yatırım alarak Midjourney, Runway ve Character.ai gibi şirketlerde on milyarlarca vektörü ölçeklendirirken; ChromaDB prototipleme için en hızlı yol sunarken 5–10 milyon vektör sonrası üretim duvarına çarpar. [^30^] [^32^]
- **Agent memory framework'leri** arasında Mem0 (~48K GitHub yıldızı) kişiselleştirme odaklı lider konumdayken, Letta (MemGPT) OS-tarzı bellek yönetimiyle uzun süreli ajanları destekler ve Cognee bilgi grafiği odaklı yapısıyla 38+ kaynaktan veri alır. [^29^] [^31^] [^52^]
- **Graph memory ile vector memory** arasındaki seçim kullanım durumuna bağlıdır: vector memory benzerlik tabanlı anlamsal geri çağırma için uygunken, graph memory varlıklar arası ilişkileri ve multi-hop muhakeme gerektiren senaryolarda üstündür. Hibrit mimariler (vector + graph) üretimde standart haline gelmektedir. [^34^] [^38^] [^36^]
- **RAG pipeline'larında** chunking stratejileri belirleyicidir: recursive chunking yaygın başlangıç noktasıyken, late chunking ve contextual retrieval daha gelişmiş teknikler sunar. Reranking adımında FlashRank (~60 ms, ~4MB model) hız odaklı, Cohere/Voyage ise doğruluk odaklı seçeneklerdir. [^49^] [^85^] [^86^]
- **Kişiselleştirme** teknikleri spektrumu: (1) prompt engineering (system prompt, few-shot CoT), (2) RAG tabanlı kişiselleştirme, (3) representation learning / fine-tuning, (4) RLHF/RLPHF arasında genişler. Gerçek dünya etkileşimlerinde few-shot CoT, Reminder ve RAG benzer iyileştirmeler gösterir; ancak uzun bağlamlarda RAG en etkilidir. [^50^] [^123^] [^130^]
- **Fine-tuning vs RAG** tartışmasında 2024 Menlo Ventures raporuna göre kurumsal AI dağıtımlarının %51'i RAG kullanırken sadece %9'u fine-tuning'e dayanmaktadır. RAFT çalışması hibrit sistemlerin her iki yaklaşımdan üstün performans gösterdiğini kanıtlamaktadır. [^45^] [^46^]
- **Uzun süreli bellek** için üç ana paradigma vardır: (1) vektör deposu yaklaşımı (bellek alma olarak), (2) özetleme yaklaşımı (bellek sıkıştırma olarak), (3) graf yaklaşımı (bilgi olarak). Zep'in zamansal bilgi grafiği uzun süreli doğrulukta %18.5 iyileştirme sağlarken, Mem0 %26 doğruluk kazancı ve token maliyeti azaltımı sunar. [^48^]

---

## 1. Vektör Veritabanları (Yerel/Embedded)

### 1.1 Karşılaştırma Matrisi

2026 itibarıyla temel vektör veritabanlarının karşılaştırması şu şekildedir: [^30^] [^32^] [^37^]

| Veritabanı | Tür | Lisans | Maksimum Ölçek | Hibrit Arama | Filtreleme | En İyi Olduğu Alan |
|---|---|---|---|---|---|---|
| **Qdrant** | Self-hosted / Cloud | Apache 2.0 | 100M–1B | v1.9+ (sparse) | Mükemmel | Filtreli self-hosted üretim |
| **Weaviate** | Self-hosted / Cloud | BSD-3 | 50M–500M | Native BM25+dense | İyi | Hibrit doküman arama |
| **Milvus** | Self-hosted / Cloud | Apache 2.0 | Billions+ | v2.5+ Sparse-BM25 | İyi | Kurumsal ölçekli retrieval |
| **LanceDB** | Embedded / Cloud | Apache 2.0 | 10B+ | Native | İyi | Multimodal + eğitim verisi |
| **ChromaDB** | Self-hosted | MIT | < 10M | Yok | Temel | Prototipleme |
| **pgvector** | Postgres extension | PostgreSQL | < 100M | Yok | Mükemmel (SQL) | Mevcut Postgres yığınları |
| **chromem-go** | Embedded (Go) | - | ~100K | Yok | Temel | Go uygulamaları, WASM |

### 1.2 Başlıca Veritabanları

**LanceDB**: Apache Lance sütunlu formatı üzerine kurulu, vektörleri ve ham veriyi (metin, görüntü, ses, video) tek birleşik dosya formatında depolar. 2025 Haziran'da 30M$ Series A yatırım aldı. Midjourney, Runway ve Character.ai üretimde kullanıyor. 2026 Ocak güncellemesiyle DuckDB SQL entegrasyonu eklendi. [^30^]

**ChromaDB**: "Dört satırda çalışan" prototipleme hızı ile bilinir. MIT lisanslı, Python-öncelikli. 5–10 milyon vektör sonrası performans duvarına çarpar; üretimde genellikle Qdrant veya Pinecone'a geçilir. [^30^] [^32^]

**Qdrant**: Rust ile yazılmış, açık kaynak, self-hosted veya bulut. HNSW + ACORN indeksi, v1.9+ ile sparse vektör hibrit arama, v1.15.2 ile sunucu tarafı IDF hesaplama. Filtreli sorgulamada en hızlı seçeneklerden biri. [^30^] [^37^]

**Milvus**: Zilliz tarafından desteklenen, GPU hızlandırmalı, kurumsal ölçek için tasarlanmış. 2025'te Sparse-BM25 ile Elasticsearch'e göre 30x latency avantajı elde etti. [^30^]

**chromem-go**: Philipp Gille tarafından geliştirilen, sıfır üçüncü taraf bağımlılığı ile gömülebilir Go vektör veritabanı. Chroma-benzeri API, bellek-içi opsiyonel kalıcılık, deneysel WASM desteği sunar. 1.000 dokümanı 0.3 ms'de, 100.000 dokümanı 40 ms'de sorgular. OpenAI, Azure, Cohere, Ollama gibi çoklu embedding sağlayıcıları destekler. [^93^]

### 1.3 Hibrit Arama ve Vektör Niceleme

Hibrit arama (dense + sparse BM25) yasal sorgularda ve özel terim aramalarında kritik öneme sahiptir. RRF (Reciprocal Rank Fusion) ve RSF (Relative Score Fusion) ana birleştirme yöntemleridir. [^30^] Vektör niceleme: skalar niceleme (int8) 4x bellek tasarrufu sağlarken ~%1 recall kaybı yaşatır; ikili niceleme 32x sıkıştırma sağlar ama ~%5 recall kaybı getirir. [^30^]

---

## 2. Agent Memory Framework'leri

### 2.1 Framework Karşılaştırması

2026 itibarıyla önde gelen agent memory framework'leri şu şekilde karşılaştırılır: [^29^] [^31^] [^124^]

| Framework | Mimari | Lisans | Temel Güçlü Yön | Uzmanlık Alanı |
|---|---|---|---|---|
| **Mem0** | Vektör + Graph + KV | Apache 2.0 / Managed | ~48K yıldız, en büyük ekosistem, kişiselleştirme | Döngüsel kullanıcılar, kişiselleştirme |
| **Letta** | Tiered RAM/disk (OS-tarzı) | Apache 2.0 / Managed | Ajan kendi belleğini yönetir | Uzun ufuksal ajanlar, sınırsız bellek |
| **Cognee** | KG + Vektör | Open core / Managed | 38+ bağlayıcı, bilgi grafiği | Yapılandırılmamış doküman alımı |
| **Zep / Graphiti** | Zamansal KG | Açık kaynak / Managed | Zamansal varlık takibi | "Şubat'ta kim bu hesabın sahibiydi" |
| **Hindsight** | Çok-stratejili hibrit | MIT / Managed | 4 paralel retrieval stratejisi + çapraz-kodlayıcı reranking | Kurumsal bilgi, self-improving bellek |
| **LocalRecall** | Hafif RESTful API | Açık kaynak | %100 yerel, Docker/Compose | Çevrimdışı/private dağıtımlar |

### 2.2 Mem0 Detaylı İnceleme

Mem0 üç kapsamlı bellek kapsamı sunar: `user_id`, `agent_id`, `run_id`/`session_id`, `app_id`/`org_id`. [^6^] Çatışma çözümü: yeni bilgi mevcut kayıtlarla çatıştığında self-editing yapar, kopya giriş oluşturmaz. [^126^] Graph memory (Mem0g) 2025 Eylül'de Kuzu gömülü graph veritabanı desteği eklendi. Mem0g, vektör-only yaklaşıma göre LLM Score'da 68.4% vs 66.9% performans gösterirken latency maliyeti p95'te 2.59 sn (vektör-only 1.44 sn) getirir. [^6^]

OpenMemory MCP: 2025 Mayıs'ta tanıtılan yerel-first bellek sunucusu, MCP protokolü üzerinden Cursor, Claude Desktop, Windsurf gibi istemcilerle çalışır. Tamamen yerel depolama, bulut senkronizasyonu yok. [^54^]

**Sınırlamalar**: Graph memory Pro tier'de ($249/ay) paywall arkasındadır. Zamansal olgu modellemesi yoktur (oluşturma zaman damgası vardır ama geçerlilik penceresi veya olgu üstlenme yoktur). LongMemEval'de bağımsız benchmark %49.0 ile Zep'in %63.8'inin gerisindedir. [^126^]

### 2.3 Letta (MemGPT) Detaylı İnceleme

Letta, LLM-as-an-Operating-System paradigmasını benimser. Bellek mimarisi katmanlıdır: [^39^] [^104^]

1. **Core Memory (Memory Blocks)**: Her zaman ajan tarafından görülebilen, yüksek öncelikli kalıcı bilgi. `persona`, `human` gibi bloklar. Ajan kendi belleğini düzenleyebilir: `core_memory_append`, `core_memory_replace`, `memory_insert`, `memory_rethink` araçları.
2. **Inner Thoughts (Özel Muhakeme)**: Kullanıcıya görünmeyen iç monolog adımları.
3. **Recall Memory (Konuşma Kalıcılığı)**: Eski mesajlar atılmaz; özetlenir ve kalıcı depolamada saklanır.
4. **Archival Memory (Uzun Süreli Depolama)**: Şirket dokümanları, politikalar, PDF'ler için ayrı depolama. `archival_memory_insert()` aracıyla erişilir.
5. **Vector DB Entegrasyonu**: Harici vektör veritabanları ile semantik arama.

Benchmark: Letta LongMemEval-S'te Mem0'a göre anlamlı şekilde üstün performans göstermiştir (P@5: 0.683 vs 0.156). [^33^]

### 2.4 Cognee Detaylı İnceleme

Cognee, ECL (Extract, Cognify, Load) pipeline'ına dayanır: [^47^] [^51^] [^52^] [^53^]

- **Extract**: 38+ kaynaktan heterojen veri alımı (metin, görüntü, ses)
- **Cognify**: LLM tabanlı varlık ve ilişki çıkarımı, Pydantic modelleri ile şema tabanlı dönüşüm
- **Load**: Graph (NetworkX, FalkorDB, Neo4j), ilişkisel veya vektör depolara yazma

**memify** katmanı: Derecelendirilmiş yanıtlar kenar ağırlıklarına geri beslenerek belleğin kullanımla keskinleşmesini sağlar. Zamansal farkındalık: DataPoint modeli versiyonlama ve zaman damgalarını yerleşik olarak içerir; çatışan bilgilerde eski ilişkiler silinmeden geçersiz kılınabilir. [^53^]

Cognee 2026 Şubat'ta 7.5M$ seed yatırım aldı. [^52^]

### 2.5 LocalRecall

LocalRecall, hafif bir RESTful API katmanıdır ve vektör depolama için chromem-go kullanır (Milvus ve Qdrant desteği planlanmaktadır). Markdown, PDF ve diğer formatları destekler. LocalAGI ve LocalAI ile entegre olur. Docker/Compose dağıtımı ile çevrimdışı/private RAG senaryoları için uygundur. [^55^] [^56^]

### 2.6 Graph Memory vs Vector Memory: Ne Zaman Hangisi?

| Özellik | Vector Memory | Graph Memory |
|---|---|---|
| Arama Türü | Semantik benzerlik | İlişkisel gezinme |
| Veri Türü | Yapılandırılmamış metin | Birbiriyle bağlı varlıklar |
| Gecikme | Orta | Yüksek |
| Muhakeme | İlişkisel (associative) | Yüksek (multi-hop) |
| Kurulum Maliyeti | Düşük | Yüksek |

**Graph memory** tercih edilmeli: karmaşık varlık ilişkileri gerektiren senaryolarda (tıbbi hasta bağlamları, kurumsal hesap hiyerarşileri, teknik sistem bağımlılıkları, yasal akıl yürütme). [^34^] [^38^]

**Vector memory** yeterli: basit kişiselleştirme, geçmiş konuşmaları hatırlama, doküman arama gibi benzerlik-tabanlı senaryolarda. [^34^]

**Hibrit**: Vector DB ile ilk alma (bağlamsal benzerlik), ardından graph traversal (ilişkisel hassasiyet) en üretimde benimsenen yaklaşımdır. [^38^] [^111^]

---

## 3. RAG Pipeline'ları

### 3.1 Document Ingestion ve Chunking

Chunking stratejileri belirleyicidir: [^49^]

- **Fixed-size chunking**: En basit, prototipleme için yeterli. Tutarlı kavramları parçalar arasında kırar.
- **Recursive chunking**: Öncelikli ayırıcı listesi (paragraf → satır → boşluk) kullanır. Çoğu RAG pipeline'ı için yaygın başlangıç noktası.
- **Semantic chunking**: Bitişik cümle gömüntüleri arasında kosinüs benzerliği hesaplar; eşik altında düşünce değişimi varsa sınır konur. Daha fazla chunk üretir, karışık kazanım gösterir.
- **Late chunking**: Tam doküman önce gömüntülenir, sonra chunk'lar çıkarılır. ~%3 ortalama göreli iyileştirme raporlanmıştır. Büyük bağlam penceresi gerektirir.
- **Contextual retrieval**: Her chunk'a LLM tarafından üretilmiş bağlam özeti eklenir. Hibrit retrieval + reranking ile birlikte en etkili, ancak indeksleme maliyeti yüksek.
- **Pseudo-Instruction Chunking (PIC)**: Doküman düzeyinde özet ile chunk sınırları yönlendirilir. 6 QA veri setinde hits@5: 58.4 (fixed-size: 54.5, semantic: 56.0). [^49^]

### 3.2 Embedding Modelleri

2026 itibarıyla embedding modeli seçimi maliyet-kalite dengesi açısından kritiktir: [^101^] [^103^] [^110^]

| Model | Maliyet/1M | MTEB/Güçlü Yön | En İyi Olduğu Alan |
|---|---|---|---|
| **Voyage-3.5** | $0.06 | nDCG@3: 0.9429 (3 alan ortalama) | Genel amaçlı üstün kalite |
| **Cohere embed-v4** | $0.10 | 100+ dil, ikili/int8 niceleme | Çok dilli uygulamalar |
| **OpenAI text-embedding-3-large** | $0.13 | 3072 boyut, Matryoshka | Güvenli varsayılan seçim |
| **BGE-M3 (BAAI)** | Ücretsiz (self-host) | Dense + sparse + multi-vektör | Açık kaynak, GPU gerektirir |
| **pplx-embed-v1-0.6b** | $0.004 | Voyage-3.5'in %92'si | Maliyet-öncelikli RAG |
| **Nomic Embed v2** | Ücretsiz (self-host) | CPU'da çalışabilir, 8192 token | Yerel/edge dağıtımlar |

**Kritik bulgu**: Voyage-3.5, kendi amiral gemisi Voyage-4-large'dan yarı fiyatına daha iyi 3-alan ortalama performans gösterir. OpenAI text-embedding-3-large hukuk alanında (CUAD) 8 daha ucuz model tarafından geçilir. [^101^]

### 3.3 Reranking

Reranking, iki aşamalı retrieval'in ikinci aşamasıdır: [^86^] [^90^]

| Reranker | Tür | Güçlü Yön | Zayıf Yön | En İyi Olduğu Alan |
|---|---|---|---|---|
| **Cohere** | Cross-encoder API | Yüksek doğruluk, çok dilli | Maliyet (API ücretleri) | Genel RAG, kurumsal |
| **Voyage** | Cross-encoder API | En üst düzey doğruluk | Maliyet, latency | Finans, hukuk |
| **FlashRank** | Hafif cross-encoder (ONNX) | Çok hızlı (~10-60 ms), düşük kaynak | Doğruluk daha düşük | Hız-kritik, kaynak kısıtlı |
| **bge-reranker** | Açık kaynak cross-encoder | Yüksek doğruluk, self-host | GPU/CPU altyapısı gerekir | Açık kaynak tercihi |
| **ColBERT** | Multi-vektör (Late Interaction) | Ölçekte verimli | İndeksleme yoğun | Çok büyük koleksiyonlar |
| **MixedBread** | Açık kaynak cross-encoder | SOTA iddiası, çok dilli, uzun bağlam | Görece yeni | Yüksek performans RAG |

**FlashRank**: ~4MB en küçük model, Torch/Transformers bağımlılığı yok, CPU'da çalışır. ms-marco-TinyBERT-L-2-v2 ile ~10ms/50 doküman; MiniLM-L-12-v2 ile ~25ms/50 doküman. Tam cross-encodere göre ~%85-90 kalite. [^88^] [^90^]

FlashRank ayrıca token bütçesi altında optimal alt küme seçimi yapan marjinal-fayda reranker olarak da önerilir; %35 context token tasarrufu ve %22 yanıt süresi iyileştirmesi sağlar. [^85^]

### 3.4 Context Window Yönetimi

LLM bağlam penceresi sabit bir tavan olduğundan, etkili yönetim stratejileri şunlardır: [^87^] [^94^]

1. **Hiyerarşik Bağlam Yapısı**: Sistem talimatları ve görev tanımı → en doğrudan alakalı retrieval sonuçları → ek arka plan bilgisi → araç tanımları.
2. **Dinamik Bağlam Sıkıştırma**: Düşük öncelikli içeriğin (eski mesajlar, uzun dokümanlar) özetlenmesi.
3. **Seçici Enjeksiyon**: LLM yönlendirmeli routing mantığı ile sorgu doğasına göre dinamik bilgi parçası seçimi.
4. **Yapılandırılmış Etiketleme**: XML/Markdown etiketleri ile kaynak ve tür ayrımı.
5. **Adaptive Kontrol**: Model kapasitesine göre sonuç sayısı, benzerlik eşikleri ve özetleme oranlarının dinamik ayarlanması. [^87^]

---

## 4. Kişiselleştirme Teknikleri

### 4.1 Sistem Prompt / Persona Tasarımı

Sistem prompt'ları ajanın kişiliğini, tonunu ve davranış kısıtlamalarını tanımlar. OpenAI Agents SDK'de kişiselleştirme için context engineering örneği: profil (global müşteri kimliği, isim, yaş, ton tercihi, koltuk tercihi) + global_memory (notlar) + session_memory yapısı. [^130^]

Persona geliştirmede few-shot prompting ile doğrulanmış persona örnekleri verildiğinde yapılandırılmış ve tutarlı çıktılar üretilir. [^42^] [^43^]

### 4.2 Few-shot Prompting ile Kişisel Davranış Kalıpları

Few-shot kişiselleştirme, kullanıcının geçmiş yanıtlarından ve profilinden örnekler ekleyerek LLM'i belirli bir kullanıcıya uyarlar. FERMI (Few-shot Personalization with Mis-aligned Responses) yaklaşımı, hizalanmamış yanıtların bağlamını kullanarak iteratif prompt iyileştirmesi yapar ve ChatGPT üzerinde OpQA'da %54.6 doğruluk (baseline %45.5) elde eder. [^50^]

Uzun ufuksal tercih takibinde few-shot Chain-of-Thought, Reminder ve RAG benzer iyileştirmeler gösterir; ancak uzun bağlamlarda (142K+ token) RAG en etkili yöntemdir. [^123^]

### 4.3 Fine-tuning vs RAG + Prompt Engineering

| Boyut | Fine-tuning | RAG + Prompt Engineering |
|---|---|---|
| **Veri güncelliği** | Eğitim anında donmuş | Anlık güncellenebilir |
| **Bilgi takibi** | Yok (hallucination riski) | Var (kaynak belirtilebilir) |
| **Maliyet** | Yüksek (eğitim, GPU) | Düşük (sorgu başına embedding) |
| **Görev spesifikliği** | Yüksek doğruluk | Bağlama bağımlı |
| **Bakım** | Yeniden eğitim gerektirir | Doküman güncellemesi yeterli |
| **Uygulama karmaşıklığı** | Yüksek | Orta |

2024 Menlo Ventures raporuna göre kurumsal AI dağıtımlarının %51'i RAG, %9'u fine-tuning kullanır. RAFT (UC Berkeley) hibrit sistemlerin en iyi performansı gösterdiğini kanıtlar. [^45^] Fine-tuning, yüksek hacimli ve düşük gecikmeli görevlerde, spesifik format/ton kontrolünde avantajlıdır. [^46^]

### 4.4 Kullanıcı Tercihlerini Öğrenme ve Hafızada Tutma

İki ana yaklaşım: [^127^]

1. **Explicit Personalization**: Sistem doğrudan kullanıcıdan ton, içerik türü, bilgi derinliği gibi tercihleri sorar.
2. **Implicit Personalization**: Sistem geçmiş etkileşimlerden, davranış kalıplarından ve bağlamsal ipuçlarından tercihleri çıkarır.

Ek biçimler: bağlamsal kişiselleştirme (cihaz, zaman, konum), işbirlikçi kişiselleştirme (benzer kullanıcılardan öğrenme), hedef odaklı kişiselleştirme, adaptif öğrenme. [^127^]

AdaPA-Agent, kullanıcı tercihlerinin göreli güçlerini dinamik olarak modelleyen bir yaklaşımdır; mevcut etkileşimlerden ek geri bildirim gerektirmeden öğrenir ve ReAct'e göre %18.9 iyileştirme sağlar. [^131^]

OpenAI Agents SDK'de oturum sonrası bellek konsolidasyonu: oturum notları global belleğe sadece kalıcı olduğu kanıtlanırsa terfi ettirilir; geçici tercihler ("bu seferlik pencere koltuğu istiyorum") atılır. [^130^]

---

## 5. Long-term Memory / Persistent Knowledge

### 5.1 Konvansiyonel Hafıza (Özetleme)

Özetleme yaklaşımı, konuşma geçmişini periyodik olarak yoğunlaştırarak sürekli özetler oluşturur. Letta'da terfi edilen (evicted) içerik özyinelemeli olarak özetlenir. [^39^] Experience compression through summarization helps maintain long-term memory manageable. [^36^]

### 5.2 Yapısal Hafıza (Graph / Entity Extraction)

Zep / Graphiti zamansal bilgi grafiği yaklaşımı: varlıklar ve ilişkiler zamanla nasıl değiştiğini izler. Baseline retrieval sistemlerine göre uzun ufuksal doğrulukta %18.5 iyileştirme ve ~%90 latency azalması sağlar. [^48^]

Mem0g: Varlık çıkarıcı konuşma metninden düğümleri tanımlar, ilişki üreteci etiketli kenarlar oluşturur, çatışma detektörü yeni bilginin mevcut graph öğeleriyle çelişip çelişmediğini işaretler. [^6^]

Cognee: ECL pipeline ile LLM tabanlı varlık/ilişki çıkarımı, zamansal farkındalık (versiyonlama + zaman damgası), çatışan bilgilerde eski ilişkileri geçersiz kılma. [^53^]

### 5.3 Hibrit Yaklaşımlar

Üretimde standartlaşan hibrit bellek mimarisi: [^111^] [^36^]

- **KV Store**: Hızlı gerçekler, oturum durumu, yapılandırma bayrakları (durum için)
- **Vector Store**: Benzer deneyimleri çağırma, doküman arama (anımsatma için)
- **Graph Store**: İlişkiler üzerinde akıl yürütme, varlık takibi, görev planlama (hikaye için)

Hibrit RAG sistemleri üretimde standart haline gelmektedir. CrewAI dört bellek türü sunar: ChromaDB destekli kısa süreli, SQLite destekli uzun süreli, varlık belleği ve harici bellek (Mem0 eklentisi dahil). [^102^]

### 5.4 Dört Katmanlı Bellek Mimarisi

AI ajanları için dört bellek katmanı: [^107^] [^105^]

1. **Internal Knowledge (Ağırlıklar)**: Statik, eğitimde donmuş genel dünya bilgisi.
2. **Context Window (RAM)**: Tek bir çıkarım adımında LLM'e iletilen bilgi. Transformer attention ile kuadratik ölçeklenir.
3. **Short-Term Memory (Ajan RAM'i)**: Aktif bağlam penceresi + yakın etkileşimler + uzun süreli bellekten alınan detaylar. Uçucu ve hızlı.
4. **Long-Term Memory (Disk)**: Kalıcı, kişiselleştirme ve sürekliliği sağlayan dış depolama. Retrieval pipeline ile kısa süreli belleğe taşınır.

---

## Major Players & Sources

- **Mem0 (mem0.ai)**: Kişiselleştirme ve çok kapsamlı bellek yönetiminde lider. ~48K GitHub yıldızı, $24M fonlama. Graph memory Pro tier'de mevcut. [^126^] [^31^]
- **Letta (letta.com, eski MemGPT)**: OS-tarzı ajan-yönetimli bellek. Core memory blocks, self-editing tools, recall/archival memory katmanları. Apache 2.0, ~21K yıldız. [^39^] [^104^]
- **Cognee (cognee.ai)**: Bilgi grafiği odaklı ECL pipeline. 38+ kaynak, 3 depo katmanı (graph, vektör, ilişkisel). $7.5M seed yatırım. [^52^] [^51^]
- **Zep / Graphiti**: Zamansal bilgi grafiği uzmanı. LongMemEval'de en yüksek skor. [^48^] [^29^]
- **Hindsight**: Kurumsal bilgi için çok-stratejili retrieval (semantik + BM25 + graph + zamansal). MIT lisanslı. [^124^] [^31^]
- **LocalRecall**: %100 yerel, hafif RESTful API. chromem-go tabanlı. [^55^] [^56^]
- **chromem-go**: Philipp Gille tarafından geliştirilen sıfır bağımlılıklı gömülü Go vektör veritabanı. [^93^]
- **Qdrant**: Rust tabanlı, açık kaynak, üretimde filtreli sorgulama lideri. [^30^]
- **LanceDB**: Multimodal lakehouse vizyonu. Midjourney, Runway, Character.ai üretimde kullanıyor. [^30^]
- **FlashRank**: Prithiviraj Damodaran tarafından geliştirilen ultra-hafif reranking kütüphanesi. [^92^] [^85^]
- **Voyage AI**: Retrieval optimizasyonunda lider embedding ve reranker sağlayıcısı. [^101^]

---

## Trends & Signals

- **Graph memory üretime geçiş**: 2024'te deneysel olan graph memory, 2026 itibarıyla üretim ortamlarında kullanılıyor. Mem0g, Zep/Graphiti, Cognee ana sürücüler. [^6^] [^48^]
- **Çok kapsamlı bellek (Multi-scope) API'leri**: Mem0'un `user_id`/`agent_id`/`run_id`/`app_id` modeli, ajan belleği tasarımında standartlaşan bir API deseni haline geldi. [^6^] [^126^]
- **Yerel-first bellek çözümleri**: OpenMemory MCP (Mem0), LocalRecall, chromem-go ile yerel, gizlilik-odaklı bellek talebi artıyor. [^54^] [^55^]
- **RAG + Fine-tuning hibritleşmesi**: RAFT ve benzeri çalışmalar, sadece RAG veya sadece fine-tuning yerine her ikisini birleştiren sistemlerin geleceğini gösteriyor. [^45^]
- **Agent belleği kategorisinin fonlanması**: 2025-2026 döneminde Mem0, Cognee, Hindsight ve diğerleri toplam 50M$+'lık yatırım aldı. "AI Memory bir özellik değil, kategori" olarak konumlandırılıyor. [^52^] [^126^]
- **Embedding modeli pazarının parçalanması**: OpenAI'nin varsayılan konumu zayıflıyor; Voyage, Cohere, pplx-embed ve açık kaynak modeller alan özelinde üstünlük kuruyor. [^101^]
- **Reranking standartlaşması**: İki aşamalı retrieval (bi-encoder + reranker) artık üretim RAG sistemlerinin beklenen yapı taşı. [^86^]
- **MCP protokolü entegrasyonu**: OpenMemory MCP, Mem0'un MCP sunucusu ile bellek sistemlerinin Model Context Protocol üzerinden entegre olması yönünde bir işaret. [^54^]

---

## Controversies & Conflicting Claims

- **Graph memory latency maliyeti**: Mem0g, vektör-only'e göre daha iyi LLM Score (68.4% vs 66.9%) sunarken p95 latency 2.59 sn (vektör-only 1.44 sn) getirir. Üretimde bu maliyet kabul edilebilir mi? Basit kişiselleştirme senaryolarında Mem0 dokümantasyonu graph memory'yi devre dışı bırakmayı önerir. [^6^]
- **Mem0 vs Zep benchmark farkı**: Mem0 LongMemEval'de %49.0 skor alırken Zep %63.8 alır. Ancak Mem0 LOCOMO'da lider konumdadır. Bu farklı benchmark'ların farklı güçlü yönleri ölçtüğünü gösterir: Mem0 kişiselleştirmede, Zep zamansal akıl yürütmede üstün. [^126^] [^29^]
- **Ajanların belleği doğrudan güncelleme yetkisi**: Tüm büyük bellek sistemleri ajanın belleği doğrudan güncellemesine izin verir; hiçbiri yerleşik "insan inceleme-onay kapısı" sunmaz. Markdown vault + semantic search deseni bu açığı kapatmayı önerir. [^29^]
- **Fine-tuning vs RAG**: Menlo Ventures raporu kurumsal dağıtımlarda RAG'ın baskınlığını gösterirken, RAFT hibritin üstünlüğünü kanıtlar. Ancak fine-tuning maliyet ve operasyonel karmaşıklığı nedeniyle yaygınlaşmıyor. [^45^] [^46^]
- **Semantic chunking değeri**: Redis blog'una göre semantic chunking daha fazla chunk üretir ve karışık kazanım gösterir; "her zaman daha iyi olduğunu varsaymayın, kendi corpus'unuzda benchmark edin" önerilir. [^49^]

---

## Recommended Deep-Dive Areas

- **Hindsight memory framework**: Kurumsal bilgi için tasarlanmış, 4 paralel retrieval stratejisi + çapraz-kodlayıcı reranking sunan en yeni ve az bilinen framework'lerden biri. Üretimde Mem0/Letta kadar bilinmiyor ancak benchmark ve mimari olarak güçlü. [^124^] [^31^]
- **Zamansal (temporal) bellek modelleri**: Zep/Graphiti'nin zamansal bilgi grafiği yaklaşımı ve Cognee'nin versiyonlanmış DataPoint modeli, "bilgi zamanla nasıl değişir?" sorusuna yanıt arayan sistemler için kritik. Mem0'da bu özellik eksik. [^48^] [^53^] [^126^]
- **MCP + yerel bellek ekosistemi**: OpenMemory MCP'nin Model Context Protocol üzerinden cross-client bellek paylaşımı nasıl çalışıyor? Yerel-first, gizlilik-odaklı mimarilerin geleceği. [^54^]
- **Kişiselleştirme için RLHF/RLPHF**: P-RLHF ve benzeri teknikler, kullanıcı geri bildirimini doğrudan ödül sinyali olarak kullanarak kişiselleştirme yapar. Şu anda daha çok akademik olsa da üretime taşınma potansiyeli yüksek. [^123^]
- **Context engineering ve bağlam penceresi yönetimi**: 200K+ token çağında RAG sistemlerinin bağlam penceresini nasıl yöneteceği (hiyerarşik yapı, dinamik sıkıştırma, seçici enjeksiyon) henüz olgunlaşmamış bir alan. [^94^]
- **Ajan belleği için insan-in-the-loop onay akışları**: Hiçbir büyük framework yerleşik "ajan öğrenme önerisi → insan inceleme → onay/red" döngüsü sunmaz. Bu boşluk, özellikle düzenlenmiş endüstrilerde (finans, sağlık, hukuk) kritik bir eksiklik. [^29^]
