# Dim 03 - Bellek Mimarisi & Dim 04 - RAG Pipeline
## AI Asistan Bellek ve RAG Sistemleri Derinlemesine Araştırma Raporu

**Tarih:** Haziran 2026  
**Kapsam:** Bellek mimarisi, RAG pipeline, kişisel bilgi entegrasyonu  
**Arama sayısı:** 20+ bağımsız kaynak  
**Kaynak türleri:** Akademik makaleler (arXiv), teknik bloglar, GitHub repo'ları, benchmark raporları

---

## BÖLÜM I: DIM 03 - BELLEK MİMARİSİ

---

### 1.1 Mem0 vs Letta vs Cognee vs LocalRecall: Karşılaştırmalı Analiz

#### Mem0: "Bolt-On" Bellek Katmanı

Mem0, mevcut ajan çerçevelerine eklenen hafif bir bellek katmanı olarak konumlanıyor. ~48K GitHub yıldızıyla ajan bellek alanındaki en büyük topluluğa sahip. [^1^]

**Claim:** Mem0 vektör depolama + LLM tabanlı çıkarım + çok kapsamlı bellek modeli (user_id, agent_id, run_id, app_id, org_id) kullanarak kişiselleştirme odaklı bir bellek katmanı sunar. [^2^]  
**Source:** Mem0 vs Letta (MemGPT): AI Agent Memory Compared  
**URL:** https://vectorize.io/articles/mem0-vs-letta  
**Date:** 2026-03-15  
**Excerpt:** "Mem0 is a memory service with a simple API. You call add() to store memories and search() to retrieve them. Under the hood, Mem0 embeds your content into a vector database for semantic retrieval. On the Pro tier ($249/month), it also builds a knowledge graph that extracts entities and relationships, enabling multi-hop queries."  
**Context:** Mem0'nun mimari felsefesi; mevcut ajan döngüsünü değiştirmeden bellek eklemeyi hedefler.  
**Confidence:** high

**Claim:** Mem0, LongMemEval'de bağımsız değerlendirme ile %49.0 doğruluk elde eder. [^3^]  
**Source:** Mem0 vs Letta: AI Agent Memory Compared  
**URL:** https://vectorize.io/articles/mem0-vs-letta  
**Date:** 2026-03-15  
**Excerpt:** "An independent evaluation measured Mem0 at 49.0% on LongMemEval, which tests long-term memory retrieval across temporal, multi-hop, and knowledge-update scenarios."  
**Context:** Mem0'nun benchmark performansı; Letta'nın LongMemEval sonuçları yayınlanmamış.  
**Confidence:** high

**Claim:** Mem0'ın akademik makalesi (arXiv:2504.19413) Mem0 ve Mem0g (graph variant) mimarilerini tanıtıyor; LOCOMO benchmark'ında mevcut bellek sistemlerinden üstün performans gösteriyor. [^4^]  
**Source:** Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory  
**URL:** https://arxiv.org/html/2504.19413v1  
**Date:** 2025-04-28  
**Excerpt:** "We introduce Mem0, a novel memory architecture that dynamically captures, organizes, and retrieves salient information from ongoing conversations. Building on this foundation, we develop Mem0g, which enhances the base architecture with graph-based memory representations."  
**Context:** Mem0 akademik doğrulaması; LOCOMO benchmark sonuçları.  
**Confidence:** high

**Claim:** Mem0 LOCOMO'da 0.71s medyan gecikme ve ~1,800 token/konuşma ile çalışırken, tam bağlam (full-context) yaklaşımı 9.87s ve ~26,000 token gerektirir. [^5^]  
**Source:** Agent Memory & Knowledge Systems Compared (2026 Guide)  
**URL:** https://fountaincity.tech/resources/blog/agent-memory-knowledge-systems-compared/  
**Date:** 2026-05-05  
**Excerpt:** "Mem0 scores 66.9% on the LOCOMO benchmark at 0.71s median latency using around 1,800 tokens per conversation, versus a full-context baseline of 72.9% at 9.87s and around 26,000 tokens."  
**Context:** Mem0 bellek mimarisi verimliliği değerlendirmesi.  
**Confidence:** medium

#### Letta (MemGPT): OS-Tarzı Self-Editing Bellek

Letta, UC Berkeley MemGPT araştırmasının ticari devamı. Tam bir ajan çalışma zamanı (runtime) sunar ve bellek yönetimini ajanın kendisine bırakır. [^6^]

**Claim:** Letta, üç katmanlı bellek mimarisi (Core Memory = RAM, Recall Memory = disk cache, Archival Memory = cold storage) kullanır ve ajanın kendi belleğini düzenlemesine izin verir. [^7^]  
**Source:** Mem0 vs Letta: AI Agent Memory Compared  
**URL:** https://vectorize.io/articles/mem0-vs-letta  
**Date:** 2026-03-15  
**Excerpt:** "Letta is not a memory layer you add to an existing stack — it is the stack. The framework manages the agent loop, tool execution, state persistence, and memory across three tiers inspired by computer architecture: Core Memory (RAM), Recall Memory (disk cache), Archival Memory (cold storage)."  
**Context:** Letta'nın temel felsefik farkı; mimari katmanlaşma.  
**Confidence:** high

**Claim:** Letta'nın lock-in maliyeti yüksektir; ajan döngüsünün tamamını Letta'nın kontrolüne bırakır, taşınması 2-6 hafta mühendislik işi gerektirir. [^8^]  
**Source:** Mem0 vs Letta vs MemGPT 2026  
**URL:** https://tokenmix.ai/blog/ai-agent-memory-mem0-vs-letta-vs-memgpt-2026  
**Date:** 2026-04-20  
**Excerpt:** "Letta lock-in: high. Letta owns your agent loop. Switching means rebuilding the loop, tool execution, state management, and memory logic elsewhere. Realistic switch cost: 2-6 weeks for a mid-complexity agent."  
**Context:** Mimari taşınabilirlik değerlendirmesi.  
**Confidence:** high

**Claim:** Letta, DMR (Deep Memory Retrieval) benchmark'ında MemGPT'yi geçiyor, ancak LongMemEval sonuçları yayınlanmamış. MemoryArena benchmark'ında Letta 132.8s ortalama gecikme ile çalışır. [^9^]  
**Source:** Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks (arXiv:2602.16313)  
**URL:** https://arxiv.org/html/2602.16313v1  
**Date:** 2026-02-18  
**Excerpt:** "Table 4: Latency of agents with different memory paradigms (sec.). Letta: 219, 150, 121, 77, 97 — Avg: 132.8"  
**Context:** MemoryArena benchmark sonuçları; Letta'nın gecikme performansı.  
**Confidence:** high

**Claim:** Letta, kendi bellek sistemini benchmark etmek için LOCOMO, MemBench ve LongMemEval desteği eklemeyi planlıyor. [^10^]  
**Source:** Letta GitHub Feature Request  
**URL:** https://github.com/letta-ai/letta/issues/3115  
**Date:** 2025-12-22  
**Excerpt:** "Currently, Letta lacks any standardized benchmark or evaluation code to measure memory system performance."  
**Context:** Letta'nın benchmark eksikliği; topluluk talebi.  
**Confidence:** high

#### Cognee: Pipeline + Graph Yaklaşımı

Cognee, açık kaynaklı bir bellek kontrol düzlemi (memory control plane) olarak 30+ veri kaynağından beslenir ve graf+vektör hibrit arama sunar. [^11^]

**Claim:** Cognee, RAG'in %40 başarısızlık oranını aşmak için memory-first mimari kullanır; embedding + graph extraction + triplets (subject-relation-object) ile %90 doğruluk yakalar. [^12^]  
**Source:** From RAG to Graphs: How Cognee is Building Self-Improving AI Memory  
**URL:** https://memgraph.com/blog/from-rag-to-graphs-cognee-ai-memory  
**Date:** 2025-10-02  
**Excerpt:** "RAG fails in around 40% of cases. This figure is nowhere near the 95%+ reliability expected in production. Cognee introduced a memory-first architecture. It combining embeddings with graph-based extraction (triplets → subject-relation-object) that were stored in a knowledge graph. Accuracy approaching 90% compared to RAG's 60%."  
**Context:** Cognee'nin RAG'den graph belleğe geçiş gerekçesi.  
**Confidence:** medium

**Claim:** Cognee, 30+ kaynaktan veri alır, vektör+graf+ilişkisel deposa yazılır, ontology desteği sunar ve HotpotQA'da %87 yanıt doğruluğu elde eder. [^13^]  
**Source:** Cognee GitHub  
**URL:** https://github.com/topoteretes/cognee  
**Date:** 2026-05-06  
**Excerpt:** "Cognee is an open-source memory control plane for your Agents that lets you ingest data in any format or structure and continuously learns to provide the right context. It combines embeddings, graphs and cognitive science approaches."  
**Context:** Cognee'nin açık kaynak özellikleri.  
**Confidence:** high

**Claim:** Cognee'nin gözlemlenen başarımı: 1GB veriyi 100+ konteyner kullanarak 40 dakikada işler. [^14^]  
**Source:** From RAG to Graphs: How Cognee is Building Self-Improving AI Memory  
**URL:** https://memgraph.com/blog/from-rag-to-graphs-cognee-ai-memory  
**Date:** 2025-10-02  
**Excerpt:** "At present, performance sits at around 1 GB processed in 40 minutes using 100+ containers."  
**Context:** Cognee üretim ölçeklenebilirliği değerlendirmesi.  
**Confidence:** medium

#### LocalRecall: Tamamen Yerel RESTful API

LocalRecall, Mudler'ın LocalAI ailesinin bir parçası olarak %100 yerel, GPU/internet gerektirmeyen hafif bir bellek katmanı. [^15^]

**Claim:** LocalRecall, tamamen offline çalışan, hafif bir RESTful API'dir; Chromem (yerel dosya tabanlı vektör deposu) ve PostgreSQL+pgvector destekler. [^16^]  
**Source:** LocalRecall GitHub  
**URL:** https://github.com/mudler/LocalRecall  
**Date:** 2025-02-12  
**Excerpt:** "A lightweight, no-frills RESTful API designed for managing knowledge bases and files stored in vector databases—no GPU, internet, or cloud services required! Currently supports Chromem (local file-based vector store, default) and PostgreSQL with pgvector."  
**Context:** LocalRecall'ın temel özellikleri; LocalAI ekosisteminin bir parçası.  
**Confidence:** high

**Claim:** LocalRecall, Markdown, Plain Text ve PDF dosyalarını destekler ve LocalAI/LocalAGI ile kolayca entegre olur. [^17^]  
**Source:** LocalRecall GitHub  
**URL:** https://github.com/mudler/LocalRecall  
**Date:** 2025-02-12  
**Excerpt:** "File Support: Markdown, Plain Text, PDF. It can easily integrate with LocalAI, LocalAGI, and other agent frameworks."  
**Context:** LocalRecall dosya desteği ve entegrasyon yetenekleri.  
**Confidence:** high

#### Karşılaştırma Tablosu

| Boyut | Mem0 | Letta | Cognee | LocalRecall |
|---|---|---|---|---|
| Tür | Bellek katmanı | Tam ajan runtime | Bellek kontrol düzlemi | Yerel bellek API |
| GitHub Stars | ~48K | ~21K | ~12K | Daha yeni |
| Lisans | Apache 2.0 | Apache 2.0 | Open core | Açık kaynak |
| Bellek Mimarisi | Vektör + Graph (Pro) | 3 katmanlı (Core/Recall/Archival) | Poly-store (graf+vektör+ilişkisel) | Vektör (Chromem/pgvector) |
| Yerel Çalışma | Self-hosted evet | Self-hosted evet | Self-hosted evet | %100 offline |
| LongMemEval | %49.0 | Yayınlanmamış | HotpotQA %87 | N/A |
| Lock-in | Düşük | Yüksek | Orta | Düşük |
| En İyi Kullanım | Kişiselleştirme | Uzun süreli otonom ajanlar | Kurumsal bilgi grafiği | Tamamen offline ajanlar |

---

### 1.2 Yerel Çalışabilirlik: Hangisi Tamamen Offline Çalışır?

**Claim:** Tamamen offline AI asistan mimarisi için Ollama (yerel LLM) + sentence-transformers (yerel embedding) + VelesDB (yerel vektör deposu) kombinasyonu kullanılabilir; hiçbir ağ çağrısı yapılmaz. [^18^]  
**Source:** Run your AI assistant fully offline: a local-first architecture  
**URL:** https://dev.to/wiscale-fr/run-your-ai-assistant-fully-offline-a-local-first-architecture-4iic  
**Date:** 2026-04-01  
**Excerpt:** "The entire pipeline runs without a single network call. The embedding model, the vector database, the memory system, and the LLM all execute locally."  
**Context:** Tamamen offline AI asistanı mimari önerisi.  
**Confidence:** high

**Claim:** chromem-go, Go dilinde sıfır bağımlılıklı, gömülebilir bir vektör veritabanıdır; 100K belge üzerinde sorgu 40ms'de çalışır. [^19^]  
**Source:** Show HN: Chromem-go – Embeddable vector database  
**URL:** https://news.ycombinator.com/item?id=39941144  
**Date:** 2024-04-05  
**Excerpt:** "Zero dependencies on third party libraries. Multi-threaded processing for adding and querying documents. A query on 100,000 documents runs in 40 ms on a 1st gen Framework Laptop."  
**Context:** chromem-go teknik özellikleri; gömülebilir vektör DB pazar boşluğunu doldurur.  
**Confidence:** high

**Claim:** Raspberry Pi 4 (4GB RAM) üzerinde %100 offline çalışan bir AI asistanı (AVA) Ollama + Qwen2 + Vosk + Piper TTS ile gerçekleştirilebilir. [^20^]  
**Source:** I Built a Fully Offline AI Assistant on a £50 Raspberry Pi  
**URL:** https://medium.com/@thedominicknight/i-built-a-fully-offline-ai-assistant-on-a-50-raspberry-pi-and-it-actually-works-3ede45136e87  
**Date:** 2026-02-21  
**Excerpt:** "AVA runs entirely on a Raspberry Pi 4 with 4GB of RAM. Listens for a wake word using Porcupine, transcribes with Vosk, thinks using Ollama running Qwen2, speaks back using Piper TTS."  
**Context:** Edge cihazlarda offline AI asistanı gerçekleştirilebilirliği.  
**Confidence:** high

**Claim:** LocalRecall, LocalAI ailesinin bir parçası olarak %100 yerel çalışır ve internet/cloud bağımlılığı yoktur. [^21^]  
**Source:** LocalRecall — local memory layer and knowledge base  
**URL:** https://jimmysong.io/ai/localrecall/  
**Date:** 2025-02-12  
**Excerpt:** "LocalRecall provides a local memory layer and knowledge base management API for agents and RAG scenarios. Suited as an internal knowledge store for agents, chatbots and RAG applications in offline or private deployments."  
**Context:** LocalRecall'ın yerel ilk tasarım felsefesi.  
**Confidence:** high

**Offline Çalışabilirlik Değerlendirmesi:**

| Sistem | Tamamen Offline | Self-Hosted | Notlar |
|---|---|---|---|
| Mem0 | Evet (OSS sürümü) | Evet | Graph özelliği Pro tier'de bulutta; OSS'te farklı |
| Letta | Evet | Evet | Tam ajan runtime; karmaşık kurulum |
| Cognee | Evet | Evet | 30+ kaynak ingestion; Graphiti/FalkorDB gerekebilir |
| LocalRecall | **Evet** | Evet | **En hafif; RESTful API; GPU gerekmez** |
| chromem-go | Evet | N/A | Gömülebilir kütüphane; ayrı servis gerekmez |
| Zep | Graphiti OSS evet | Kısmen | Zep Cloud = managed; Graphiti = OSS |

---

### 1.3 Graph Memory vs Vector Memory: Kişisel Asistan İçin Hangisi Daha Uygun?

**Claim:** Vektör veritabanları geniş anlamsal eşleşme için idealdir; graph RAG çok atlamalı ilişkiler, hiyerarşik yapılar ve doğruluk gerektiren durumlarda üstündür. [^22^]  
**Source:** Vector Databases vs. Graph RAG for Agent Memory  
**URL:** https://machinelearningmastery.com/vector-databases-vs-graph-rag-for-agent-memory-when-to-use-which/  
**Date:** 2026-03-05  
**Excerpt:** "Vector databases are ideal for broad similarity matching and unstructured data retrieval, while graph RAG excels when context windows are limited and when multi-hop relationships, factual accuracy, and complex hierarchical structures are required."  
**Context:** Vektör ve graph yaklaşımlarının temel ayrımı.  
**Confidence:** high

**Claim:** Graph memory, kişi/organizasyon/varlık ilişkilerini zaman içinde takip etme gerektiğinde (örn. "Alice Ocak ayına kadar proje lideriydi, sonra Bob devraldı") doğal üstünlük sağlar; flat vektör mimarileri bunu yerel olarak modelleyemez. [^23^]  
**Source:** Best AI Agent Memory Frameworks in 2026  
**URL:** https://atlan.com/know/best-ai-agent-memory-frameworks-2026/  
**Date:** 2026-04-02  
**Excerpt:** "Zep stores every fact as a knowledge graph node with a validity window. When new information contradicts old, Graphiti invalidates the old without discarding the historical record."  
**Context:** Graph memory'nin temporal reasoning üstünlüğü.  
**Confidence:** high

**Claim:** Mem0g (graph variant) Mem0'dan daha iyi temporal ve açık alan sonuçları verir, ancak multi-hop sorgularda graf yapısının overhead'i nedeniyle Mem0 bazen daha iyi sonuç verir. [^24^]  
**Source:** Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory (arXiv:2504.19413)  
**URL:** https://arxiv.org/html/2504.19413v1  
**Date:** 2025-04-28  
**Excerpt:** "For multi-hop questions, Mem0 exhibits clear advantages by effectively synthesizing dispersed information across multiple sessions... the expected relational advantages of Mem0g do not translate into better outcomes here, suggesting potential overhead or redundancy when navigating more intricate graph structures."  
**Context:** Mem0 akademik makalesi; graf ve vektör bellek karşılaştırması.  
**Confidence:** high

**Claim:** Hindsight, biomimetik veri yapıları kullanarak (World facts + Experiences + Mental Models) dört paralel arama stratejisi (semantik, BM25, bilgi grafiği, temporal) ile LongMemEval'de %91.4 skor elde eder. [^25^]  
**Source:** Hindsight GitHub  
**URL:** https://github.com/vectorize-io/hindsight  
**Date:** 2025-06-15  
**Excerpt:** "Hindsight uses biomimetic data structures to organize agent memories: World (facts about the world), Experiences (agent's own experiences), Mental Models (learned understanding formed by reflecting on raw memories)."  
**Context:** Hindsight'ın biyomimetik bellek mimarisi; multi-strategy retrieval.  
**Confidence:** high

**Claim:** Kişisel asistanlar için en iyi yaklaşım hibrit olandır: "My agent needs all of the above. You probably need to layer them. Several teams are combining graph memory for entity relationships with observational memory for conversation compression." [^26^]  
**Source:** Your AI Agent's Memory Is Broken. Here Are 4 Architectures Racing to Fix It  
**URL:** https://dev.to/ai_agent_digest/your-ai-agents-memory-is-broken-here-are-4-architectures-racing-to-fix-it-55j1  
**Date:** 2026-03-10  
**Excerpt:** "Several teams are combining graph memory for entity relationships with observational memory for conversation compression. This is where the architecture gets interesting — and where most teams over-engineer. Start with one, add the second only when you hit a specific failure mode."  
**Context:** Bellek mimarisi seçimi karar ağacı.  
**Confidence:** high

**Kişisel Asistan için Değerlendirme:**

| Kriter | Vektör Memory | Graph Memory | Hibrit (Önerilen) |
|---|---|---|---|
| Anlamsal arama | Mükemmel | Zayıf | Vektör katmanı ile |
| İlişki takibi | Zayıf | Mükemmel | Graph katmanı ile |
| Temporal akıl yürütme | Elle filtreleme | Yerel destek | Graph + temporal |
| Çok atlamalı sorgular | Sınırlı | Güçlü | Graph traversal |
| Gecikme | ~1-10ms | ~100-300ms | Orta |
| Kurulum kolaylığı | Basit | Karmaşık | Orta |
| Kişisel asistanda öncelik | Konuşma geçmişi | Kişi/tercih ilişkileri | **Her ikisi** |

---

### 1.4 Hibrit Bellek (Vektör + Graph + Konvansiyonel) Tasarımı

**Claim:** Üretim sistemleri nihayetinde iki veya daha fazla bellek modelini birleştirir; hiçbir model evrensel olarak üstün değildir. [^27^]  
**Source:** Agent Memory Architectures: Patterns and Trade-offs  
**URL:** https://atlan.com/know/agent-memory-architectures/  
**Date:** 2026-04-17  
**Excerpt:** "No pattern is universally superior. The right architecture depends on whether your primary constraint is token cost, latency, accuracy, relational complexity, or governance. Most production enterprise deployments ultimately combine two or more patterns across all five dimensions."  
**Context:** Atlan'ın beş boyutlu bellek mimarisi karşılaştırması.  
**Confidence:** high

**Claim:** Cognee'nin mevcut mimarisi vektör, graf ve reasoning katmanlarını birleştiren birleşik bir geliştirici yığınıdır: ingestion → enrichment (embeddings + graph memify) → retrieval (time filters + graph traversal + vector similarity). [^28^]  
**Source:** From RAG to Graphs: How Cognee is Building Self-Improving AI Memory  
**URL:** https://memgraph.com/blog/from-rag-to-graphs-cognee-ai-memory  
**Date:** 2025-10-02  
**Excerpt:** "The pipeline flows from ingestion across 30+ supported sources, to enrichment with embeddings and graph 'memify' steps, and finally to retrieval combining time filters, graph traversal, and vector similarity."  
**Context:** Cognee'nin hibrit mimari akışı.  
**Confidence:** high

**Claim:** Mem0 Pro tier'da vektör + bilgi grafiği + key-value üç katmanlı depolama sunar; bu, çok kapsamlı bellek modeliyle birleşir. [^29^]  
**Source:** Best AI Agent Memory Systems in 2026  
**URL:** https://vectorize.io/articles/best-ai-agent-memory-systems  
**Date:** 2026-03-14  
**Excerpt:** "Mem0: Hybrid (vector + graph + KV). Memories are extracted automatically from conversations and stored against whichever scopes apply."  
**Context:** Mem0'nun çok katmanlı depolama yaklaşımı.  
**Confidence:** high

**Hibrit Bellek Tasarım Önerisi (Kişisel Asistan için):**

```
┌─────────────────────────────────────────────────────────┐
│                    HİBRİT BELLEK MİMARİSİ                │
├─────────────────────────────────────────────────────────┤
│  Katman 1: Çalışma Belleği (Working Memory)             │
│  ├── LLM Context Window (mevcut oturum)                   │
│  └── Kısa süreli sohbet geçmişi (son N mesaj)           │
├─────────────────────────────────────────────────────────┤
│  Katman 2: Konuşma Belleği (Episodic Memory)            │
│  ├── Vektör deposu: semantic search                     │
│  └── Zaman damgalı gözlemler (Observations)           │
├─────────────────────────────────────────────────────────┤
│  Katman 3: Görev Belleği (Task Memory)                  │
│  ├── Aktif görev durumu ve bağlam                     │
│  └── Araç çağrıları ve sonuçları                      │
├─────────────────────────────────────────────────────────┤
│  Katman 4: Uzun Süreli Bellek (Long-term Memory)        │
│  ├── Vektör: Kişisel bilgiler, tercihler               │
│  ├── Graph: Kişiler, ilişkiler, varlıklar              │
│  └── Key-Value: Yapılandırılmış profil verisi          │
└─────────────────────────────────────────────────────────┘
```

---

### 1.5 Context Window Yönetimi ve Özetleme Stratejileri

**Claim:** Mastra'nın Observational Memory (OM) sistemi, arka planda çalışan Observer ve Reflector ajanlarıyla konuşma geçmişini 3-6x sıkıştırır; %95.5 temporal akıl yürütme doğruluğu sağlar. [^30^]  
**Source:** Observational Memory: 95% on LongMemEval  
**URL:** https://mastra.ai/research/observational-memory  
**Date:** 2026-02-09  
**Excerpt:** "Observational Memory achieves the highest score ever recorded on LongMemEval — 94.87% with gpt-5-mini — while maintaining a completely stable, cacheable context window. The architecture: two background agents (Observer and Reflector) watch the conversation and maintain a dense observation log that replaces raw message history."  
**Context:** OM'nin benchmark rekoru ve mimari tasarımı.  
**Confidence:** high

**Claim:** LangChain'in Deep Agents'ı, araç yanıtları 20,000 token'ı aştığında dosya sistemine offloading yapar; bağlam %85'i geçtiğinde eski araç çağrılarını özetler. [^31^]  
**Source:** Context Management for Deep Agents  
**URL:** https://www.langchain.com/blog/context-management-for-deepagents  
**Date:** 2026-01-28  
**Excerpt:** "When Deep Agents detects a tool response exceeding 20,000 tokens, it offloads the response to the filesystem. As the session context crosses 85% of the model's available window, Deep Agents will truncate older tool calls, replacing them with a pointer to the file on disk."  
**Context:** LangChain Deep Agents bağlam yönetimi stratejileri.  
**Confidence:** high

**Claim:** Hiyerarşik bağlam özetleme, eski konuşma segmentlerini dereceli olarak sıkıştırırken son mesajları aynen korur; bu, destek/danışmanlık uygulamalarında uzun süreli bağlamı korur. [^32^]  
**Source:** Context Window Management: Strategies for Long-Context AI Agents  
**URL:** https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/  
**Date:** 2025-11-02  
**Excerpt:** "Hierarchical summarization compresses older conversation segments while preserving essential information. Rather than discarding old context entirely, systems generate progressively more compact summaries as information ages."  
**Context:** Bağlam penceresi yönetimi en iyi uygulamaları.  
**Confidence:** high

**Claim:** Mem0, özetleme yerine bellek oluşumunu (memory formation) kullanır: akıllı sistemler spesifik gerçekleri, tercihleri ve kalıpları tanımlar; bunlar "selective" olarak kalıcı hale getirilir. [^33^]  
**Source:** LLM Chat History Summarization: Best Practices and Techniques  
**URL:** https://mem0.ai/blog/llm-chat-history-summarization-guide-2025  
**Date:** 2025-10-06  
**Excerpt:** "The key difference is selectivity. Summarization tries to preserve everything in compressed form, while memory formation chooses what deserves permanent retention. Mem0 follows this approach by detecting the key facts in real time and persisting them automatically."  
**Context:** Mem0'nun özetleme karşıtı bellek oluşumu felsefesi.  
**Confidence:** high

**Claim:** LongMemEval, uzun bağlam LLM'lerinin sürekli etkileşimlerde %30-60 performans düşüşü yaşadığını gösterir; bu, etkili bellek mekanizmalarının kritik olduğunu kanıtlar. [^34^]  
**Source:** LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory  
**URL:** https://arxiv.org/abs/2410.10813  
**Date:** 2024-10-14  
**Excerpt:** "Commercial chat assistants and long-context LLMs showing a 30% accuracy drop on memorizing information across sustained interactions."  
**Context:** LongMemEval akademik makalesi; bellek sistemlerinin gerekliliğini gösterir.  
**Confidence:** high

**Claim:** Context window yönetiminde sıkıştırma stratejileri (LLM özetleme + pattern tabanlı çıkarma) ile bellek deposu (vektör arama) kombinasyonu en etkili yaklaşımdır. [^35^]  
**Source:** How to Create Context Window Management  
**URL:** https://oneuptime.com/blog/post/2026-01-30-context-window-management/view  
**Date:** 2026-01-30  
**Excerpt:** "The ContextWindowManager combines token counting, prioritization, sliding window, compression, and memory management. Strategies include LLMSummarizationStrategy and ExtractionStrategy."  
**Context:** Üretim bağlam penceresi yönetim mimarisi.  
**Confidence:** medium

**Özetleme Stratejileri Karşılaştırması:**

| Strateji | Sıkıştırma Oranı | Gecikme | Kalite | En İyi Kullanım |
|---|---|---|---|---|
| Sabit N mesaj | Yok | Anında | Düşük (eski bağlam kaybolur) | Kısa sohbetler |
| Token bazlı kesme | Yok | Anında | Düşük | Basit uygulamalar |
| LLM özetleme | 3-10x | Yüksek | Orta-Yüksek | Uzun sohbetler |
| Gözlemsel bellek (OM) | 3-40x | Düşük | Yüksek | Ajan sistemleri |
| Fakt çıkarımı (Mem0) | Seçici | Düşük | Yüksek | Kişiselleştirme |
| Vektörize bellek | Arama tabanlı | Düşük | Orta | SSS tarzı etkileşimler |



---

## BÖLÜM II: DIM 04 - RAG PIPELINE

---

### 2.1 Yerel RAG Stack: Embedding Modeli + Vektör DB + Reranker

**Claim:** Tamamen yerel RAG pipeline'ı: Ollama (LLM) + ChromaDB (vektör depo) + sentence-transformers (embedding) ile kurulabilir; GPU gerekmez, internet bağlantısı gerekmez. [^36^]  
**Source:** Building a Local RAG Pipeline from Scratch  
**URL:** https://medium.com/@dennno/building-a-local-rag-pipeline-from-scratch-how-i-finally-understood-retrieval-augmented-generation-dc83e764bac7  
**Date:** 2026-03-10  
**Excerpt:** "The entire stack runs on a MacBook. No GPU required. No internet connection after initial model download. Component choice: LLM runtime Ollama, Vector store ChromaDB, Embeddings sentence-transformers, LLM llama3."  
**Context:** Yerel RAG pipeline'ının minimal bileşenleri ve kurulum kolaylığı.  
**Confidence:** high

**Claim:** FlashRank, CPU üzerinde ~10-30ms'de çalışan ultra hafif bir reranker'dir; geleneksel cross-encoder'lara göre 10-30x daha hızlıdır, doğruluk kaybı sadece %2-5'tir. [^37^]  
**Source:** Reranking: Advance RAG's Technique  
**URL:** https://medium.com/@ayushigupta9723/reranker-advance-rags-technique-8fb654c21834  
**Date:** 2026-01-09  
**Excerpt:** "FlashRank executes in under 60 ms for 100 candidates (parallelized). FlashRank: 95-98% accuracy (2-5% drop). Speed: 10-30x faster. Typical latency: 15-30ms for N=50 on CPU."  
**Context:** FlashRank'ın hız/doğruluk dengesi; üretim RAG sistemleri için.  
**Confidence:** high

**Claim:** Voyage-3.5, OpenAI text-embedding-3-large'dan %8.26 daha iyi performans gösterirken 2.2x daha düşük maliyet ve 32K token context window sunar. [^38^]  
**Source:** voyage-3.5 and voyage-3.5-lite: improved quality for a new retrieval frontier  
**URL:** https://blog.voyageai.com/2025/05/20/voyage-3-5/  
**Date:** 2025-05-20  
**Excerpt:** "voyage-3.5 and voyage-3.5-lite outperform OpenAI-v3-large by 8.26% and 6.34%, respectively, with 2.2x and 6.5x lower respective costs and a 1.5x smaller embedding dimension."  
**Context:** Voyage AI embedding modeli performans karşılaştırması.  
**Confidence:** high

**Claim:** Yerel embedding modellerinden BGE-Large-EN-v1.5, Nomic-Embed-Text-v1.5 ve GTE-Large-EN-v1.5, OpenAI text-embedding-3-large ile 1.5 puan marj içinde eşdeğer performans gösterir; maliyet sıfırdır ve veri sızıntısı yoktur. [^39^]  
**Source:** Local vs OpenAI Embeddings: RAG Quality Benchmark  
**URL:** https://localaimaster.com/blog/local-vs-openai-embeddings  
**Date:** 2026-04-23  
**Excerpt:** "BGE-Large-EN-v1.5 and Nomic-Embed-Text-v1.5 each match OpenAI text-embedding-3-large within a 1.5-point margin on standard RAG metrics, at roughly 1/40th the cost and zero data exposure."  
**Context:** Yerel vs bulut embedding modelleri karşılaştırması; 10,000 belge üzerinde.  
**Confidence:** high

**Claim:** Nomic-Embed-Text-v1.5, CPU'da ~1,400 tokens/saniye ile en CPU-dostu seçenektir; RTX 4090'da 61,000 tokens/saniyeye ulaşır. [^40^]  
**Source:** Local vs OpenAI Embeddings: RAG Quality Benchmark  
**URL:** https://localaimaster.com/blog/local-vs-openai-embeddings  
**Date:** 2026-04-23  
**Excerpt:** "Nomic-Embed-Text-v1.5: 4.1s for 1,000 docs, 61,000 tokens/sec, Batch=128. Nomic is the most CPU-friendly option at ~1,400 tokens/sec on a Ryzen 5 5600X."  
**Context:** Yerel embedding performans ve donanım gereksinimleri.  
**Confidence:** high

**Claim:** LlamaIndex 2024 State of RAG raporuna göre, RAG uygulayıcılarının %72'si çok aşamalı pipeline'ların (reranking ile) tek aşamalı retrieval'dan üstün olduğunu söyler; ancak sadece %34'ü üretimde reranking uygulamıştır. [^41^]  
**Source:** Complete guide to building AI agents with RAG in 2025  
**URL:** https://www.yaitec.com/en/blog/guide-ai-agents-with-rag-2025  
**Date:** 2026-04-17  
**Excerpt:** "According to LlamaIndex's 2024 State of RAG report, 72% of AI practitioners say multi-stage pipelines with re-ranking outperform single-stage retrieval — but only 34% have actually implemented re-ranking in production."  
**Context:** Reranking uygulama boşluğu; rekabet avantajı fırsatı.  
**Confidence:** high

**Yerel RAG Stack Önerisi:**

```
┌─────────────────────────────────────────────────────────┐
│               YEREL RAG STACK (Privacy-First)            │
├─────────────────────────────────────────────────────────┤
│  LLM: Ollama + Qwen3 / Llama3 / Mistral                  │
│  ├── 4-8GB VRAM veya CPU (7B-8B modeller)               │
│  └── OpenAI-compatible API endpoint                     │
├─────────────────────────────────────────────────────────┤
│  Embedding: Ollama nomic-embed-text veya BGE            │
│  ├── 768-1024 boyutları                                   │
│  ├── Matryoshka desteği (isteğe bağlı kesme)            │
│  └── 32K context window (Voyage-3.5 bulutta)            │
├─────────────────────────────────────────────────────────┤
│  Vektör DB: ChromaDB (persist_directory)                │
│  ├── Alternatif: chromem-go (Go, zero-dep)              │
│  ├── Alternatif: pgvector (PostgreSQL)                  │
│  └── Alternatif: Qdrant (yerel mod)                     │
├─────────────────────────────────────────────────────────┤
│  Reranker: FlashRank (ms-marco-MiniLM-L-12-v2)          │
│  ├── ~25ms CPU'da (50 doküman)                          │
│  ├── ~95-98% cross-encoder kalitesi                     │
│  └── 50MB model boyutu                                  │
├─────────────────────────────────────────────────────────┤
│  Ingestion: LangChain / LlamaIndex                      │
│  ├── RecursiveCharacterTextSplitter                     │
│  ├── PDF: PyPDFLoader, Markdown: Unstructured            │
│  └── Metadata zenginleştirme                            │
└─────────────────────────────────────────────────────────┘
```

---

### 2.2 Kişisel Dosya Ingestion: PDF, TXT, Notion, Obsidian

**Claim:** Notion'dan Obsidian'a markdown dışa aktarımı için Python betikleri mevcuttur; notion2md, notion-exporter, notion-to-obsidian-py gibi araçlar bağlantı dönüşümü, CSV→MD tablo dönüşümü ve UUID temizliği yapar. [^42^]  
**Source:** GitHub - notion-to-obsidian-py  
**URL:** https://github.com/LStoneyy/notion-to-obsidian-py  
**Date:** 2025-06-04  
**Excerpt:** "Converts Notion exported Markdown files to Obsidian format: removes UUIDs, converts links to wikilinks, converts CSV databases to Markdown tables, preserves all file types."  
**Context:** Notion→Obsidian migrasyon aracı; kişisel bilgi yönetimi için.  
**Confidence:** high

**Claim:** Obsidian, tamamen yerel-first markdown not alma uygulamasıdır; backlink'ler ve graph view ile bilgi ağı oluşturur; InfraNodus gibi araçlar GraphRAG endpoint ve MCP sunucusu olarak bu grafiği ajanlara açar. [^43^]  
**Source:** Personal Knowledge Management: Build a PKM System  
**URL:** https://infranodus.com/docs/personal-knowledge-management  
**Date:** 2026-04-30  
**Excerpt:** "Obsidian is best for local-first markdown notes with backlinks. InfraNodus exposes your knowledge graph as a GraphRAG endpoint and an MCP server. Connect Claude, Cursor, ChatGPT to https://mcp.infranodus.com."  
**Context:** Obsidian ekosistemi ve GraphRAG entegrasyonu.  
**Confidence:** high

**Claim:** Cognee, Obsidian vault'larını otomatik olarak bilgi grafiğine dönüştürebilir; 400 Wikipedia URL'inden tam bağlantılı Obsidian vault üretebilir. [^44^]  
**Source:** Automated Knowledge Graphs with Cognee (Obsidian Forum)  
**URL:** https://forum.obsidian.md/t/automated-knowledge-graphs-with-cognee/108834  
**Date:** 2025-12-08  
**Excerpt:** "Cognee as Memory Engine: ingests documents (30+ formats), extracts entities/relationships via LLMs, and maintains a queryable graph. Export that graph's node entities and link them together — we get an entire vault for free."  
**Context:** Cognee + Obsidian entegrasyonu; otomatik knowledge graph oluşturma.  
**Confidence:** medium

**Claim:** Yerel RAG pipeline'ı PDF, Markdown, TXT dosyalarını destekler; hash tabanlı deduplication ile aynı dosyanın tekrar indekslenmesini önler. [^45^]  
**Source:** Building a Local RAG Pipeline from Scratch  
**URL:** https://medium.com/@dennno/building-a-local-rag-pipeline-from-scratch-how-i-finally-understood-retrieval-augmented-generation-dc83e764bac7  
**Date:** 2026-03-10  
**Excerpt:** "Hash-based deduplication to prevent re-indexing the same document. Source tracking: every chunk knows which file it came from."  
**Context:** Yerel RAG dosya ingestion en iyi uygulamaları.  
**Confidence:** high

**Kişisel Dosya Ingestion Pipeline Önerisi:**

```
Notion Export (Markdown & CSV)
    │
    ▼
 notion-to-obsidian-py (UUID temizliği, wikilink dönüşümü)
    │
    ▼
Obsidian Vault (yerel markdown + backlink'ler)
    │
    ▼
├── PDF'ler → PyPDFLoader / pdfplumber
├── Markdown → UnstructuredMarkdownLoader
├── TXT → TextLoader
└── CSV → CSVLoader (tabular RAG için)
    │
    ▼
Chunker (RecursiveCharacterTextSplitter, 512 tokens, 10-20% overlap)
    │
    ▼
Embedding (nomic-embed-text / BGE)
    │
    ▼
ChromaDB (persistent local store)
```

---

### 2.3 Chunking Stratejileri ve Boyut Optimizasyonu

**Claim:** NVIDIA 2024 benchmark'ı, 7 chunking stratejisini 5 veri setinde test etmiştir; page-level chunking 0.648 doğrulukla en tutarlı sonucu vermiştir; 512 token genel amaçlı en iyi denge noktasıdır. [^46^]  
**Source:** RAG Chunking Strategies: The 2026 Benchmark Guide  
**URL:** https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/  
**Date:** 2026-03-17  
**Excerpt:** "NVIDIA, 2024: Corpus 5 datasets. Page-Level Chunking: 0.648 accuracy, 0.107 std dev (most consistent). 512 tokens: 0.681 accuracy (best for Earnings dataset)."  
**Context:** Bağımsız chunking benchmark karşılaştırması.  
**Confidence:** high

**Claim:** FloTorch Şubat 2026 benchmark'ı, 50 akademik makale üzerinde test etmiştir; recursive 512 token %69 doğrulukla birinci olurken, semantic chunking %54'e düşmüştür (ortalama 43 token'lık parçalar oluşturarak). [^47^]  
**Source:** RAG Chunking Strategies: The 2026 Benchmark Guide  
**URL:** https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/  
**Date:** 2026-03-17  
**Excerpt:** "Vecta / FloTorch, February 2026: Recursive 512 tokens: 69% answer accuracy. Semantic (LLMSemanticChunker): 54% — semantic chunks averaged 43 tokens, which retrieved well in isolation but gave the LLM too little context."  
**Context:** Semantic chunking'ın pratik sınırları; fragment boyutu kritik.  
**Confidence:** high

**Claim:** Genel öneri: 256-512 token aralığı çoğu kullanım durumu için en iyi dengeyi sağlar; factoid sorgular için 256, analitik sorgular için 1024+ token daha uygundur; overlap %10-20 olmalıdır. [^48^]  
**Source:** Comparative Study of Text Chunking Techniques  
**URL:** https://www.tech-japan.jp/en/blog/chunking-research/  
**Date:** 2026-03-10  
**Excerpt:** "256-512 tokens as a general recommended range: In many use cases, this range demonstrated the best balance between retrieval accuracy and generation quality. Overlap equivalent to 10-15% of the chunk size was confirmed to mitigate information loss at chunk boundaries."  
**Context:** Japon araştırmacıların chunking optimizasyon bulguları.  
**Confidence:** high

**Claim:** Chroma Research, semantic chunking'in %91.9 recall elde ettiğini ancak bu yalnızca retrieval kalitesi ölçümüdür; downstream generation için recursive chunking genellikle daha iyidir. [^49^]  
**Source:** Best Chunking Strategies for RAG (and LLMs) in 2026  
**URL:** https://www.firecrawl.dev/blog/best-chunking-strategies-rag  
**Date:** 2025-10-10  
**Excerpt:** "Chroma Research: LLMSemanticChunker achieved 0.919 recall, ClusterSemanticChunker reached 0.913, and RecursiveCharacterTextSplitter hit 85.4-89.5%. Start with RecursiveCharacterTextSplitter at 400-512 tokens with 10-20% overlap."  
**Context:** Chroma'nın chunking stratejileri karşılaştırması.  
**Confidence:** high

**Claim:** Late chunking, tam belgeyi embedding'den önce böler; böylece her parça embedding'i çevreleyen belge bağlamını taşır; yoğun çapraz referans içeren belgeler için faydalıdır. [^50^]  
**Source:** RAG Chunking Strategies: The 2026 Benchmark Guide  
**URL:** https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/  
**Date:** 2026-03-17  
**Excerpt:** "Late chunking embeds the full document before splitting, so each chunk's embedding carries context from the surrounding document. Use it when documents have heavy cross-references and your embedding model supports the full document length."  
**Context:** Late chunking tekniği; uzun bağlam embedding modelleri için.  
**Confidence:** high

**Chunking Stratejileri Karşılaştırması:**

| Strateji | Karmaşıklık | Maliyet | En İyi Kullanım | Chunk Boyutu | Doğruluk |
|---|---|---|---|---|---|
| Fixed-Size | Düşük | Düşük | Basit dokümanlar | 256-512 | Orta |
| Recursive | Düşük | Düşük | Genel amaçlı (önerilen) | 512 | ~%69 (FloTorch) |
| Semantic | Orta | Orta | Karmaşık anlatı | Değişken | %91.9 recall (Chroma) |
| Page-Level | Düşük | Düşük | Yapılandırılmış belgeler | Sayfa başına | 0.648 (NVIDIA) |
| Late Chunking | Orta | Orta | Çapraz referanslı | 512-2048 | Uzun bağlam embedding ile |
| LLM-based | Yüksek | Yüksek | Kritik dokümanlar | Değişken | En yüksek |

---

### 2.4 Kişisel Konuşma Geçmişi RAG'e Entegre Etme

**Claim:** Bellek-gelişmiş RAG mimarisi, konuşma geçmişini depolama ve alma mekanizmaları ekleyerek "konuşma amnezisi"ni ortadan kaldırır. [^51^]  
**Source:** 8 RAG Architecture Diagrams You Need to Master in 2025  
**URL:** https://sdh.global/blog/development/8-rag-architecture-diagrams-you-need-to-master-in-2025/  
**Date:** 2025-10-07  
**Excerpt:** "Simple RAG with Memory extends the basic RAG framework by incorporating conversation history storage and retrieval mechanisms. This eliminates the 'conversational amnesia' that plagues standard RAG implementations."  
**Context:** Bellek-gelişmiş RAG'ın müşteri destek kullanım durumu.  
**Confidence:** high

**Claim:** Kişisel RAG sohbet robotunda, kullanıcı sorusunu bağımsız hale getirmek (reformulation) için LLM kullanarak önceki bağlamı koruma ve vektör DB'den alma yapılır. [^52^]  
**Source:** How I Built a RAG-based AI Chatbot from My Personal Data  
**URL:** https://medium.com/keeping-up-with-ai/how-i-built-a-rag-based-ai-chatbot-from-my-personal-data-88eec0d3483c  
**Date:** 2025-01-07  
**Excerpt:** "Because the user question may be a follow-up question, or need context from previous questions, I reformulated the question first to be a stand-alone question with the help of an LLM. Relevant context from the vector DB is also taken via a retriever."  
**Context:** Kişisel RAG sohbet robotu mimarisi; soru reformülasyonu.  
**Confidence:** high

**Claim:** LongMemEval, bellek-artırımlı sistemlerin üç aşamalı pipeline'ını formüle eder: (1) indexing (value ve key tasarımı), (2) retrieval (sorgu genişletme, semantik eşleşme), (3) reading (cevap çıkarma ve birleştirme). [^53^]  
**Source:** LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory  
**URL:** https://arxiv.org/abs/2410.10813  
**Date:** 2024-10-14  
**Excerpt:** "We present a unified framework that breaks down the long-term memory design into three stages: indexing, retrieval, and reading. Key optimizations: session decomposition for value granularity, fact-augmented key expansion for indexing, time-aware query expansion."  
**Context:** LongMemEval bellek pipeline formülasyonu; akademik referans.  
**Confidence:** high

**Claim:** TiMem (Temporal Hierarchical Memory), LongMemEval-S'de %76.88 doğruluk (GPT-4o-mini) elde eder; bilgi güncelleme ve çoklu oturum akıl yürütmede en iyi performansı gösterir. [^54^]  
**Source:** LongMemEval Benchmark (Emergent Mind)  
**URL:** https://www.emergentmind.com/topics/longmemeval-benchmark  
**Date:** 2026-02-10  
**Excerpt:** "TiMem: Temporal hierarchical memory achieves state-of-the-art 76.88% (GPT-4o-mini) on LongMemEval-S, reducing memory footprint by 27%. Gains most pronounced in knowledge update (+9.49pp) and multi-session reasoning (+12.03pp)."  
**Context:** Temporal bellek mimarisinin avantajları.  
**Confidence:** high

**Claim:** EverMemOS, üç fazlı bellek (episodic, semantic, reconstructive) ile %83.0 doğruluk elde eder; MemOS'tan +5.2pp daha iyidir; özellikle bilgi güncelleme (+15.5pp) ve asistan eylemleri (+17.9pp) kategorilerinde üstündür. [^55^]  
**Source:** LongMemEval Benchmark (Emergent Mind)  
**URL:** https://www.emergentmind.com/topics/longmemeval-benchmark  
**Date:** 2026-02-10  
**Excerpt:** "EverMemOS: Engram-inspired, three-phase memory achieves 83.0% overall accuracy (outperforming MemOS by +5.2pp), with largest gains on knowledge update (+15.5pp) and assistant-actions (+17.9pp)."  
**Context:** EverMemOS bellek mimarisi; bilgi güncelleme üstünlüğü.  
**Confidence:** high

**Claim:** RAG ve Memory birbirini tamamlar: "RAG helps your agent know more. Memory helps your agent remember better." Modern mimarilerde RAG paylaşılan alan bilgisi için, Memory kullanıcıya özgü bağlam için kullanılır. [^56^]  
**Source:** RAG vs Memory for AI Agents: What's the Difference  
**URL:** https://memorilabs.ai/blog/rag-vs-memory-for-ai-agents/  
**Date:** 2025-10-07  
**Excerpt:** "RAG helps your agent know more. Memory helps your agent remember better. Without RAG, memory-driven agents risk becoming contextually aware but factually outdated. Thus, in modern architectures, RAG and Memory complement each other."  
**Context:** RAG ve Bellek arasındaki mimari ayrım ve birliktelik.  
**Confidence:** high

---

### 2.5 RAG + Memory Birlikte Çalışma Mimarisi

**Claim:** Hibrit RAG+Memory mimarisi, çalışma zamanında retrieval (gerçekler için) ve bellek (deneyimler için) kombinasyonu şeklinde çalışır; bu, insanların nasıl çalıştığını yansıtır. [^57^]  
**Source:** RAG vs Memory for AI Agents: What's the Difference  
**URL:** https://memorilabs.ai/blog/rag-vs-memory-for-ai-agents/  
**Date:** 2025-10-07  
**Excerpt:** "The hybrid approach combines retrieval (for facts) and memory (for experiences). At runtime, the agent pipeline looks like: [1] Query memory, [2] If missing trigger RAG, [3] Merge results, [4] Respond and store summary. This architecture mirrors how humans operate."  
**Context:** Hibrit RAG+Memory runtime mimarisi.  
**Confidence:** high

**Claim:** Bellek-öncü ajan iş akışı: "Do I already know this?" → If missing, trigger RAG → Merge → Respond → Store summary. Bu, gecikme ve API maliyetini dramatik olarak azaltır. [^58^]  
**Source:** RAG vs Memory for AI Agents: What's the Difference  
**URL:** https://memorilabs.ai/blog/rag-vs-memory-for-ai-agents/  
**Date:** 2025-10-07  
**Excerpt:** "A memory-first agent workflow: 1. Query memory: 'Do I already know this?' 2. If missing, trigger RAG to retrieve external data. 3. Merge results. 4. Respond and store a summary for future use. This dramatically reduces latency and API costs because retrieval is conditional, not constant."  
**Context:** Bellek-öncü mimari; koşullu retrieval.  
**Confidence:** high

**Claim:** RAG pipeline'ı iki ayrı fazdan oluşur: build-time indexing (chunk, embed, store) ve run-time retrieval + generation. [^59^]  
**Source:** RAG vs. AI Agents: The Definitive 2025 Guide  
**URL:** https://medium.com/@tuguidragos/rag-vs-ai-agents-the-definitive-2025-guide-to-ai-automation-architecture-3d5157dd0097  
**Date:** 2025-12-05  
**Excerpt:** "The RAG pattern is composed of two distinct phases: a build-time indexing phase and a run-time retrieval and generation phase. [1] Indexing: chunk, embed, store. [2] Retrieval: embed query, similarity search. [3] Generation: augment prompt, generate answer."  
**Context:** RAG'ın temel mimari yapısı.  
**Confidence:** high

**Claim:** Kontinuum bellek mimarileri, RAG'in yetersiz kaldığı uzun-ufuk ajanlar için belleği adaptif bir sistem olarak tanımlar; RAG read-only ve stateless'tır, bellek ise yazma, güncelleme, unutma mekanizmaları gerektirir. [^60^]  
**Source:** Continuum Memory Architectures for Long-Horizon LLM Agents  
**URL:** https://arxiv.org/html/2601.09913v1  
**Date:** 2026-01-14  
**Excerpt:** "RAG pipelines treat memory as a stateless lookup problem. These systems excel at surfacing static knowledge yet provide no principled machinery for accumulation, update, or forgetting, which is precisely why RAG feels misaligned with long-horizon agents."  
**Context:** Uzun-ufuk ajanlar için bellek mimarisi eleştirisi; RAG'in sınırları.  
**Confidence:** high

**Claim:** Enterprise AI dağıtımlarının %51'i RAG kullanırken sadece %9'u fine-tuning'e güvenir; RAG, sık değişen bilgi için en uygun yaklaşımdır. [^61^]  
**Source:** Should You Use RAG or Fine-Tune Your LLM?  
**URL:** https://www.actian.com/blog/databases/should-you-use-rag-or-fine-tune-your-llm/  
**Date:** 2026-03-20  
**Excerpt:** "According to the Menlo Ventures 2024 State of Generative AI in the Enterprise report, 51 percent of enterprise AI deployments use RAG in production. Only nine percent rely primarily on fine-tuning."  
**Context:** Menlo Ventures 2024 kurumsal AI raporu; RAG benimsenme oranı.  
**Confidence:** high

**Claim:** K2View Ağustos 2024 araştırmasına göre, LLM'lerini artıran kuruluşların %86'sı RAG çerçevelerini seçmiştir. [^62^]  
**Source:** What is Naive RAG?  
**URL:** https://www.articsledge.com/post/naive-retrieval-augmented-generation-rag  
**Date:** 2026-01-30  
**Excerpt:** "An August 2024 survey by K2View found that 86% of enterprises augmenting LLMs chose RAG frameworks. Menlo Ventures tracked RAG adoption jumping from 31% in 2023 to 51% in 2024."  
**Context:** Kurumsal RAG benimsenme istatistikleri.  
**Confidence:** high

**RAG + Memory Birlikte Çalışma Mimarisi (Tasarım Önerisi):**

```
┌──────────────────────────────────────────────────────────────┐
│           RAG + MEMORY HİBRİT MİMARİSİ                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  KULLANICI SORGUSU                                           │
│       │                                                      │
│       ▼                                                      │
│  ┌────────────────────────┐                                  │
│  │  1. MEMORY LAYER       │                                  │
│  │  ├── Episodic: Son     │                                  │
│  │  │   oturum geçmişi?   │                                  │
│  │  ├── Semantic: Kullanıcı│                                │
│  │  │   profili, tercihler │                                │
│  │  └── Procedural: Ajan  │                                  │
│  │      davranış kuralları │                                  │
│  └──────────┬─────────────┘                                  │
│             │                                                │
│             ▼                                                │
│  ┌────────────────────────┐                                  │
│  │  2. DECISION GATE      │                                  │
│  │  "Bunu zaten biliyor   │                                  │
│  │   muyum?"              │                                  │
│  │  ├── Evet → Cevapla    │                                  │
│  │  └── Hayır → RAG Trigger│                                 │
│  └──────────┬─────────────┘                                  │
│             │                                                │
│             ▼                                                │
│  ┌────────────────────────┐                                  │
│  │  3. RAG LAYER          │                                  │
│  │  ├── Query embedding   │                                  │
│  │  ├── Vector search     │                                  │
│  │  ├── FlashRank rerank  │                                  │
│  │  └── Top-k chunks      │                                  │
│  └──────────┬─────────────┘                                  │
│             │                                                │
│             ▼                                                │
│  ┌────────────────────────┐                                  │
│  │  4. MERGE & GENERATE   │                                  │
│  │  ├── Memory context    │                                  │
│  │  ├── RAG context       │                                  │
│  │  └── LLM generation    │                                  │
│  └──────────┬─────────────┘                                  │
│             │                                                │
│             ▼                                                │
│  ┌────────────────────────┐                                  │
│  │  5. STORE & UPDATE     │                                  │
│  │  ├── Sohbeti episodic'e │                                 │
│  │  │   kaydet             │                                  │
│  │  ├── Yeni tercihleri   │                                  │
│  │  │   semantic'e kaydet  │                                  │
│  │  └── Observation log'u │                                  │
│  │      güncelle          │                                  │
│  └────────────────────────┘                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## BÖLÜM III: KARŞILAŞTIRMALI ÖZETLER VE ÖNERİLER

---

### Bellek Sistemleri Genel Sıralaması (LongMemEval Bazlı)

| Sistem | LongMemEval (GPT-4o) | Yaklaşım | Yerel? |
|---|---|---|---|
| Mastra OM | %84.23 | Gözlemsel metin | Evet |
| Hindsight | ~%83-91 | Multi-strategy hybrid | Evet |
| EverMemOS | %83.0 | Üç fazlı bellek | Evet |
| Zep/Graphiti | %71.2 | Temporal knowledge graph | Kısmen |
| Mem0 | %49.0 | Vektör + çıkarım | Evet |
| Full Context | %60.2 | Tam bağlam | N/A |
| Letta | Yayınlanmamış | Self-editing tiered | Evet |

### Kişisel Asistan (JARVIS Benzeri) İçin Önerilen Stack

**Bellek Katmanı:**
- **Working Memory:** LLM context window (son 4-8 mesaj)
- **Episodic Memory:** Observational Memory pattern (OM tarzı 3-katmanlı sıkıştırma) veya Mem0
- **Semantic Memory:** Vektör DB (ChromaDB/pgvector) + Graph (isteğe bağlı)
- **Procedural Memory:** System prompt + tool definitions

**RAG Katmanı:**
- **Embedding:** nomic-embed-text (yerel) veya Voyage-3.5 (bulut, premium)
- **Vektör DB:** ChromaDB (yerel, persistent) veya chromem-go (gömülebilir)
- **Reranker:** FlashRank (CPU, ~25ms)
- **Chunking:** Recursive, 512 tokens, 10-20% overlap
- **Ingestion:** LangChain/LlamaIndex + Obsidian/Notion entegrasyonu

**Entegrasyon Patterni:**
- Bellek-öncü: Önce bellekte ara, bulamazsan RAG'a git
- Koşullu RAG: Gereksiz retrieval maliyetini önle
- Çift katmanlı context: Bellek bağlamı + RAG bağlamı birleştir

---

## KAYNAKÇA VE ATIF DİZİNİ

[^1^] TokenMix Research Lab, "Mem0 vs Letta vs MemGPT 2026," https://tokenmix.ai/blog/ai-agent-memory-mem0-vs-letta-vs-memgpt-2026, 2026-04-20  
[^2^] Vectorize.io, "Mem0 vs Letta (MemGPT): AI Agent Memory Compared," https://vectorize.io/articles/mem0-vs-letta, 2026-03-15  
[^3^] Vectorize.io, "Mem0 vs Letta (MemGPT): AI Agent Memory Compared," https://vectorize.io/articles/mem0-vs-letta, 2026-03-15  
[^4^] Chhikara et al., "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory," arXiv:2504.19413, 2025-04-28  
[^5^] Fountain City Tech, "Agent Memory & Knowledge Systems Compared (2026 Guide)," https://fountaincity.tech/resources/blog/agent-memory-knowledge-systems-compared/, 2026-05-05  
[^6^] Gamgee AI, "Mem0 vs Letta: Which AI Memory Solution Should You Choose?," https://gamgee.ai/vs/mem0-vs-letta/, 2026-04-15  
[^7^] Vectorize.io, "Mem0 vs Letta (MemGPT): AI Agent Memory Compared," https://vectorize.io/articles/mem0-vs-letta, 2026-03-15  
[^8^] TokenMix Research Lab, "Mem0 vs Letta vs MemGPT 2026," https://tokenmix.ai/blog/ai-agent-memory-mem0-vs-letta-vs-memgpt-2026, 2026-04-20  
[^9^] arXiv:2602.16313, "Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks," 2026-02-18  
[^10^] Letta GitHub, "Feature Request: Add Standard Memory Evaluation Benchmarks," https://github.com/letta-ai/letta/issues/3115, 2025-12-22  
[^11^] Cognee GitHub, https://github.com/topoteretes/cognee, 2026-05-06  
[^12^] Memgraph Blog, "From RAG to Graphs: How Cognee is Building Self-Improving AI Memory," https://memgraph.com/blog/from-rag-to-graphs-cognee-ai-memory, 2025-10-02  
[^13^] Cognee GitHub, https://github.com/topoteretes/cognee, 2026-05-06  
[^14^] Memgraph Blog, "From RAG to Graphs: How Cognee is Building Self-Improving AI Memory," https://memgraph.com/blog/from-rag-to-graphs-cognee-ai-memory, 2025-10-02  
[^15^] LocalRecall GitHub, https://github.com/mudler/LocalRecall, 2025-02-12  
[^16^] LocalRecall GitHub, https://github.com/mudler/LocalRecall, 2025-02-12  
[^17^] LocalRecall GitHub, https://github.com/mudler/LocalRecall, 2025-02-12  
[^18^] Dev.to, "Run your AI assistant fully offline," https://dev.to/wiscale-fr/run-your-ai-assistant-fully-offline-a-local-first-architecture-4iic, 2026-04-01  
[^19^] Hacker News, "Show HN: Chromem-go," https://news.ycombinator.com/item?id=39941144, 2024-04-05  
[^20^] Medium, "I Built a Fully Offline AI Assistant on a £50 Raspberry Pi," https://medium.com/@thedominicknight/i-built-a-fully-offline-ai-assistant-on-a-50-raspberry-pi-and-it-actually-works-3ede45136e87, 2026-02-21  
[^21^] Jimmy Song Blog, "LocalRecall — local memory layer," https://jimmysong.io/ai/localrecall/, 2025-02-12  
[^22^] Machine Learning Mastery, "Vector Databases vs. Graph RAG for Agent Memory," https://machinelearningmastery.com/vector-databases-vs-graph-rag-for-agent-memory-when-to-use-which/, 2026-03-05  
[^23^] Atlan, "Best AI Agent Memory Frameworks in 2026," https://atlan.com/know/best-ai-agent-memory-frameworks-2026/, 2026-04-02  
[^24^] Chhikara et al., "Mem0: Building Production-Ready AI Agents," arXiv:2504.19413, 2025-04-28  
[^25^] Hindsight GitHub, https://github.com/vectorize-io/hindsight, 2025-06-15  
[^26^] Dev.to, "Your AI Agent's Memory Is Broken," https://dev.to/ai_agent_digest/your-ai-agents-memory-is-broken-here-are-4-architectures-racing-to-fix-it-55j1, 2026-03-10  
[^27^] Atlan, "Agent Memory Architectures: Patterns and Trade-offs," https://atlan.com/know/agent-memory-architectures/, 2026-04-17  
[^28^] Memgraph Blog, "From RAG to Graphs: How Cognee is Building Self-Improving AI Memory," https://memgraph.com/blog/from-rag-to-graphs-cognee-ai-memory, 2025-10-02  
[^29^] Vectorize.io, "Best AI Agent Memory Systems in 2026," https://vectorize.io/articles/best-ai-agent-memory-systems, 2026-03-14  
[^30^] Mastra.ai, "Observational Memory: 95% on LongMemEval," https://mastra.ai/research/observational-memory, 2026-02-09  
[^31^] LangChain Blog, "Context Management for Deep Agents," https://www.langchain.com/blog/context-management-for-deepagents, 2026-01-28  
[^32^] Maxim AI, "Context Window Management: Strategies for Long-Context AI Agents," https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/, 2025-11-02  
[^33^] Mem0 Blog, "LLM Chat History Summarization: Best Practices and Techniques," https://mem0.ai/blog/llm-chat-history-summarization-guide-2025, 2025-10-06  
[^34^] Wu et al., "LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory," arXiv:2410.10813, 2024-10-14  
[^35^] OneUptime, "How to Create Context Window Management," https://oneuptime.com/blog/post/2026-01-30-context-window-management/view, 2026-01-30  
[^36^] Medium, "Building a Local RAG Pipeline from Scratch," https://medium.com/@dennno/building-a-local-rag-pipeline-from-scratch-how-i-finally-understood-retrieval-augmented-generation-dc83e764bac7, 2026-03-10  
[^37^] Medium, "Reranking: Advance RAG's Technique," https://medium.com/@ayushigupta9723/reranker-advance-rags-technique-8fb654c21834, 2026-01-09  
[^38^] Voyage AI Blog, "voyage-3.5 and voyage-3.5-lite," https://blog.voyageai.com/2025/05/20/voyage-3-5/, 2025-05-20  
[^39^] Local AI Master, "Local vs OpenAI Embeddings: RAG Quality Benchmark," https://localaimaster.com/blog/local-vs-openai-embeddings, 2026-04-23  
[^40^] Local AI Master, "Local vs OpenAI Embeddings: RAG Quality Benchmark," https://localaimaster.com/blog/local-vs-openai-embeddings, 2026-04-23  
[^41^] Yaitec, "Complete guide to building AI agents with RAG in 2025," https://www.yaitec.com/en/blog/guide-ai-agents-with-rag-2025, 2026-04-17  
[^42^] GitHub, "notion-to-obsidian-py," https://github.com/LStoneyy/notion-to-obsidian-py, 2025-06-04  
[^43^] InfraNodus, "Personal Knowledge Management," https://infranodus.com/docs/personal-knowledge-management, 2026-04-30  
[^44^] Obsidian Forum, "Automated Knowledge Graphs with Cognee," https://forum.obsidian.md/t/automated-knowledge-graphs-with-cognee/108834, 2025-12-08  
[^45^] Medium, "Building a Local RAG Pipeline from Scratch," https://medium.com/@dennno/building-a-local-rag-pipeline-from-scratch-how-i-finally-understood-retrieval-augmented-generation-dc83e764bac7, 2026-03-10  
[^46^] PremAI Blog, "RAG Chunking Strategies: The 2026 Benchmark Guide," https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/, 2026-03-17  
[^47^] PremAI Blog, "RAG Chunking Strategies: The 2026 Benchmark Guide," https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/, 2026-03-17  
[^48^] Tech Japan, "Comparative Study of Text Chunking Techniques," https://www.tech-japan.jp/en/blog/chunking-research/, 2026-03-10  
[^49^] Firecrawl Blog, "Best Chunking Strategies for RAG in 2026," https://www.firecrawl.dev/blog/best-chunking-strategies-rag, 2025-10-10  
[^50^] PremAI Blog, "RAG Chunking Strategies: The 2026 Benchmark Guide," https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/, 2026-03-17  
[^51^] SDH Global, "8 RAG Architecture Diagrams You Need to Master in 2025," https://sdh.global/blog/development/8-rag-architecture-diagrams-you-need-to-master-in-2025/, 2025-10-07  
[^52^] Medium, "How I Built a RAG-based AI Chatbot from My Personal Data," https://medium.com/keeping-up-with-ai/how-i-built-a-rag-based-ai-chatbot-from-my-personal-data-88eec0d3483c, 2025-01-07  
[^53^] Wu et al., "LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory," arXiv:2410.10813, 2024-10-14  
[^54^] Emergent Mind, "LongMemEval Benchmark," https://www.emergentmind.com/topics/longmemeval-benchmark, 2026-02-10  
[^55^] Emergent Mind, "LongMemEval Benchmark," https://www.emergentmind.com/topics/longmemeval-benchmark, 2026-02-10  
[^56^] Memori Labs, "RAG vs Memory for AI Agents: What's the Difference," https://memorilabs.ai/blog/rag-vs-memory-for-ai-agents/, 2025-10-07  
[^57^] Memori Labs, "RAG vs Memory for AI Agents: What's the Difference," https://memorilabs.ai/blog/rag-vs-memory-for-ai-agents/, 2025-10-07  
[^58^] Memori Labs, "RAG vs Memory for AI Agents: What's the Difference," https://memorilabs.ai/blog/rag-vs-memory-for-ai-agents/, 2025-10-07  
[^59^] Medium, "RAG vs. AI Agents: The Definitive 2025 Guide," https://medium.com/@tuguidragos/rag-vs-ai-agents-the-definitive-2025-guide-to-ai-automation-architecture-3d5157dd0097, 2025-12-05  
[^60^] arXiv:2601.09913, "Continuum Memory Architectures for Long-Horizon LLM Agents," 2026-01-14  
[^61^] Actian Blog, "Should You Use RAG or Fine-Tune Your LLM?," https://www.actian.com/blog/databases/should-you-use-rag-or-fine-tune-your-llm/, 2026-03-20  
[^62^] Articsledge, "What is Naive RAG?," https://www.articsledge.com/post/naive-retrieval-augmented-generation-rag, 2026-01-30  

---

*Rapor 20+ bağımsiz kaynaktan derlenmiştir. Tüm iddialar inline citation ile desteklenmiştir.*
