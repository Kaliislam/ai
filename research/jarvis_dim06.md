
# Dim 07 & Dim 08: Mevcut Açık Kaynak Çözümlerin Karşılaştırmalı Analizi + Güvenlik ve Gizlilik

## Dim 07: Mevcut Açık Kaynak AI Asistan Çözümlerinin Detaylı İncelemesi

### 1. OpenJarvis (Stanford SAIL)

Claim: OpenJarvis, Stanford Hazy Research ve Scaling Intelligence Lab tarafından geliştirilen, tamamen cihaz üzerinde çalışan açık kaynaklı bir kişisel AI ajan çerçevesidir [^1^].
Source: scalingintelligence.stanford.edu
URL: https://scalingintelligence.stanford.edu/blogs/openjarvis/
Date: 2026-03-12
Excerpt: "OpenJarvis is an open-source framework for personal AI agents that runs entirely on-device. It provides shared primitives for building on-device agents, efficiency-aware evaluations, and a learning loop that improves models using local trace data."
Context: Stanford araştırma projesi, Apache 2.0 lisanslı
Confidence: high

Claim: OpenJarvis'in temel prensibi yerel-öncelikli (local-first) yaklaşımdır; veriler kullanıcının cihazında kalır ve yalnızca gerçekten gerekli olduğunda bulut API'lerine çağrı yapılır [^2^].
Source: GitHub - open-jarvis/OpenJarvis
URL: https://github.com/open-jarvis/OpenJarvis
Date: 2026-05-05
Excerpt: "The goal is simple: make it possible to build personal AI agents that run locally by default, calling the cloud only when truly necessary. OpenJarvis aims to be both a research platform and production foundation for local AI, in the spirit of PyTorch."
Context: Resmi GitHub reposu
Confidence: high

Claim: OpenJarvis, 30+ benchmark kapsayan bir değerlendirme aracı sunar ve enerji, FLOPs, gecikme ve maliyet gibi metrikleri birincil kısıtlar olarak ele alır [^3^].
Source: Stanford Scaling Intelligence Lab blog
URL: https://scalingintelligence.stanford.edu/blogs/openjarvis/
Date: 2026-03-12
Excerpt: "OpenJarvis provides an evaluation harness spanning 30+ benchmarks, and we would love for you to use it to measure and push progress."
Context: Enerji verimliliği odaklı değerlendirme
Confidence: high

Claim: OpenJarvis, çoklu çıkarım backend'leri (Ollama dahil) destekler ve uv ile kurulum sağlar. `jarvis init` komutu donanımı otomatik tespit edip motor önerir [^4^].
Source: Stanford blog
URL: https://scalingintelligence.stanford.edu/blogs/openjarvis/
Date: 2026-03-12
Excerpt: "The fastest way to get started: pip install openjarvis, then jarvis init."
Context: Kolay kurulum süreci
Confidence: high

**OpenJarvis Teknik Özeti:**
- **Dil:** Python
- **Kurulum:** uv sync, Docker desteği muhtemelen gelecekte
- **Lisans:** Apache 2.0
- **Türkçe desteği:** Doğrudan belgelenmemiş, ancak yerel LLM desteği sayesinde dolaylı
- **Bellek:** Yerel izleme verisiyle öğrenme döngüsü (learning loop)
- **Ses:** Belirtilmemiş (odak metin tabanlı)
- **Aktif geliştirme:** Evet, Stanford SAIL destekli

---

### 2. LocalAGI (Mudler)

Claim: LocalAGI, Go dilinde yazılmış, Docker Compose ile kolayca kurulan, OpenAI Responses API ile tam uyumlu, maksimum gizlilik odaklı bir AI ajan platformudur [^5^].
Source: GitHub - mudler/LocalAGI
URL: https://github.com/mudler/LocalAGI
Date: 2026-02-16
Excerpt: "LocalAGI is a powerful, self-hostable AI Agent platform designed for maximum privacy and flexibility. A complete drop-in replacement for OpenAI's Responses APIs with advanced agentic capabilities."
Context: Resmi GitHub reposu
Confidence: high

Claim: LocalAGI hiçbir verinin donanımı terk etmemesini garanti eder, bulut API'si anahtarı veya abonelik gerektirmez [^6^].
Source: GitHub - mudler/LocalAGI
URL: https://github.com/mudler/LocalAGI
Date: 2026-02-16
Excerpt: "LocalAGI ensures your data stays exactly where you want it—on your hardware. No API keys, no cloud subscriptions, no compromise."
Context: Gizlilik vaadi
Confidence: high

Claim: LocalAGI, kısa ve uzun vadeli bellek (RAG tabanlı), ajan ekip oluşturma (tek prompt ile çoklu ajan), periyodik görev zamanlama (cron benzeri), çok modlu destek ve Discord/Slack/Telegram/GitHub entegrasyonları sunar [^7^].
Source: GitHub - mudler/LocalAGI
URL: https://github.com/mudler/LocalAGI
Date: 2026-02-16
Excerpt: "Built-in knowledge base (RAG) for collections, file uploads, and semantic search... Advanced Agent Teaming: Instantly create cooperative agent teams from a single prompt."
Context: Özellik listesi
Confidence: high

Claim: LocalAGI, Go dilinde yorumlanan (interpreted) özel eylemler yazma imkanı sunar ve yerel MCP sunucu desteğine sahiptir [^8^].
Source: GitHub - mudler/LocalAGI releases
URL: https://github.com/mudler/LocalAGI/releases
Date: 2026-02-16
Excerpt: "feat: local MCP server support by @mudler in #61"
Context: v2.2.0 release notes
Confidence: high

**LocalAGI Teknik Özeti:**
- **Dil:** Go
- **Kurulum:** Docker Compose (CPU/NVIDIA/Intel/AMD GPU)
- **Lisans:** Belirtilmemiş (muhtemelen açık kaynak)
- **Türkçe desteği:** LLM modeline bağlı (gemma-3, qwen, vs.)
- **Bellek:** Built-in RAG, LocalRecall entegrasyonu
- **Ses:** Belirtilmemiş
- **Aktif geliştirme:** Evet, v2.3.0 (2026-02-16)

---

### 3. Home Assistant + Assist

Claim: Home Assistant Assist, Wyoming protokolü üzerinden tamamen yerel çalışan bir sesli asistan sunar; Whisper (STT), Piper (TTS) ve Ollama (LLM) entegrasyonuyla çalışır [^9^].
Source: Home Assistant Wyoming Protocol documentation
URL: https://www.home-assistant.io/integrations/wyoming/
Date: 2026-04-01
Excerpt: "The Wyoming integration connects external voice services to Home Assistant using a small protocol. This enables Assist to use a variety of local speech-to-text, text-to-speech, and wake-word-detection systems."
Context: Resmi Home Assistant dokümantasyonu
Confidence: high

Claim: Home Assistant Voice chapter 10 itibarıyla Speech-to-Phrase, 21 dili desteklemeyi hedeflemektedir ve Türkçe (Turkish) bu diller arasında yer almaktadır [^10^].
Source: Home Assistant blog - Voice Chapter 10
URL: https://www.home-assistant.io/blog/2025/06/25/voice-chapter-10/
Date: 2025-06-25
Excerpt: "Speech-to-Phrase currently supports six languages... We are now engaging with language leaders to add support for Russian, Czech, Catalan, Greek, Romanian, Portuguese, Polish, Hindi, Basque, Finnish, Mongolian, Slovenian, Swahili, Thai, and Turkish — this takes our language support to 21 languages."
Context: Resmi Home Assistant blog yazısı
Confidence: high

Claim: Speech-to-Phrase GitHub reposu Türkçe (Turkish/Türkçe) desteğini desteklenen diller listesinde açıkça belirtmektedir [^11^].
Source: GitHub - OHF-Voice/speech-to-phrase
URL: https://github.com/OHF-voice/speech-to-phrase
Date: 2025-01-24
Excerpt: "Türkçe (Turkish)" listed under Supported languages
Context: Açık kaynak Speech-to-Phrase reposu
Confidence: high

Claim: Home Assistant ile tamamen yerel sesli asistan kurulumu için: Ollama LLM entegrasyonu, Whisper veya Speech-to-Phrase STT, Piper TTS, openWakeWord uyanma kelimesi kullanılabilir [^12^].
Source: Sanyam Chhabra's Blog
URL: https://sanyamc-blog.pages.dev/p/building-a-voice-assistant/
Date: 2025-06-20
Excerpt: "Under Settings->Voice Assistants, Add Assistant, Change the name, then under Conversation Agent, select the LLM added using the Ollama Integration... For Speech-to-Text, select faster-whisper, and for Text to Speech, select piper."
Context: Adım adım kurulum kılavuzu
Confidence: high

**Home Assistant + Assist Teknik Özeti:**
- **Dil:** Python (Home Assistant temeli)
- **Kurulum:** Home Assistant OS veya Docker, Wyoming add-on'ları
- **Lisans:** Apache 2.0
- **Türkçe desteği:** Speech-to-Phrase ile doğrudan destek; Whisper ile dolaylı
- **Bellek:** Konuşma geçmişi yerel, ancak ajan belleği sınırlı
- **Ses:** Whisper (STT), Piper (TTS), openWakeWord
- **Aktif geliştirme:** Evet, Nabu Casa/Community tarafından yoğun geliştirme

---

### 4. OpenVoiceOS (OVOS)

Claim: OpenVoiceOS Foundation, Mycroft AI Inc.'nin 2023 kapanışının ardından açık kaynak topluluğu tarafından kurulan, Hollanda hükümeti tarafından 2025'te onaylanan bir vakıftır [^13^].
Source: CNX Software
URL: https://www.cnx-software.com/2025/02/24/the-openvoiceos-foundation-aims-to-enable-open-source-privacy-and-customization-for-voice-assistants/
Date: 2025-02-24
Excerpt: "OpenVoiceOS took over the codebase of Mycroft A.I. and managed to merge lingering PR from the open-source community... Peter decided to open the OpenVoiceOS Foundation along with partners in 2024, but it's just now been approved by the Dutch government."
Context: OVOS Foundation tarihi ve yapısı
Confidence: high

Claim: OpenVoiceOS, Solver Plugin -> Persona -> Persona Pipeline katmanlı mimarisi ile AI ajan entegrasyonu sunar; bu mimari LLM olmadan da çalışabilir [^14^].
Source: OVOS Technical Manual
URL: https://openvoiceos.github.io/ovos-technical-manual/150-personas/
Date: 2025-04-15
Excerpt: "OpenVoiceOS (OVOS) introduces a flexible and modular system for integrating AI agents into voice-first environments. This is made possible through a layered architecture built around solvers, personas, and persona routing components."
Context: Resmi OVOS teknik dokümantasyonu
Confidence: high

Claim: OVOS Persona sistemi, JSON konfigürasyonu ile tanımlanır, Ollama veya OpenAI uyumlu API'lere bağlanabilir ve çoklu persona yönetimi destekler [^15^].
Source: GitHub - OpenVoiceOS/ovos-persona
URL: https://github.com/OpenVoiceOS/ovos-persona
Date: 2023-03-25
Excerpt: "Personas are configured using JSON files... Save this in ~/.config/ovos_persona/llm.json with api_url pointing to Ollama."
Context: Resmi OVOS GitHub reposu
Confidence: high

Claim: HiveMind projesi, OVOS modüllerinin ağ üzerinden birden fazla cihazda dağıtılmasına olanak tanır; bu sayede güçlü sunucu üzerinde ağır işlemler, zayıf cihazlarda yalnızca ses girişi/çıkışı çalıştırılabilir [^16^].
Source: CNX Software
URL: https://www.cnx-software.com/2025/02/24/the-openvoiceos-foundation-aims-to-enable-open-source-privacy-and-customization-for-voice-assistants/
Date: 2025-02-24
Excerpt: "This extends the message bus('s) to talk over the network with all associated security mitigations involved. This allows for instance to lift all the heavy duty over to a beefy server and have small low resource 'satellites' to talk to it."
Context: HiveMind dağıtık mimari açıklaması
Confidence: high

**OpenVoiceOS Teknik Özeti:**
- **Dil:** Python
- **Kurulum:** TUI (Terminal UI) installer, virtualenv veya konteyner
- **Lisans:** Belirtilmemiş (Mycroft mirası)
- **Türkçe desteği:** Çevir katmanı otomatik; yerel LLM ile dolaylı
- **Bellek:** Kısa vadeli konuşma, LLM solver ile uzun vadeli
- **Ses:** Yerel TTS/STS desteği, phoonnx framework
- **Aktif geliştirme:** Evet, NGI Zero Commons Fund hibesi aldı (2025-10)

---

### 5. AIlice (MyShell AI)

Claim: AIlice, IACT (Interactive Agents Call Tree) mimarisi kullanan, tamamen otonom, genel amaçlı bir AI ajandır. Görevleri dinamik ajan ağacına böler ve yüksek hata toleransıyla entegre eder [^17^].
Source: GitHub - myshell-ai/AIlice
URL: https://github.com/myshell-ai/AIlice
Date: 2025 (güncel)
Excerpt: "Ailice is a fully autonomous, general-purpose AI agent. This project aims to create a standalone artificial intelligence assistant, similar to JARVIS, based on the open-source LLM. Using its unique IACT architecture, AIlice can decompose complex tasks into dynamically constructed agents and integrate results with high fault tolerance."
Context: Resmi GitHub reposu
Confidence: high

Claim: IACT mimarisi, geleneksel fonksiyon çağrı ağacından ilham alır ancak tek seferlik çağrıları çok turlu konuşmasal etkileşime dönüştürerek düşük hata toleransı sorununu çözer [^18^].
Source: Medium - Building JARVIS article
URL: https://medium.com/@stevenlu1729/building-jarvis-from-iron-man-dreams-to-reality-6cca0eb4d210
Date: 2025-06-09
Excerpt: "The Interactive Agent Call Tree draws inspiration from traditional function call trees for complex task decomposition, while transforming the caller-callee relationship from one-time calls to multi-round conversational interactions to solve low fault-tolerance issues."
Context: AIlice kurucusu Steven Lu'nun makalesi
Confidence: high

Claim: AIlice, tematik araştırma, kodlama, sistem yönetimi, literatür taraması ve karmaşık hibit görevlerde yetkinliğe sahiptir [^19^].
Source: MyShell AIlice documentation
URL: https://docs.myshell.ai/technology/ailice
Date: 2024-12-27
Excerpt: "Currently, Ailice demonstrates proficiency in a range of tasks, including thematic research, coding, system management, literature reviews, and complex hybrid tasks."
Context: Resmi MyShell dokümantasyonu
Confidence: high

Claim: AIlice, 2025 Mart itibarıyla MCP araçlarını kullanabilir ve sesli diyalog özelliğini ChatTTS ile güncelledi [^20^].
Source: GitHub - myshell-ai/AIlice
URL: https://github.com/myshell-ai/AIlice
Date: 2025
Excerpt: "Mar 22, 2025: Ailice can now use MCP tools!... Jan 23, 2025: Updated the voice dialogue feature. Thanks to ChatTTS's excellent implementation, voice dialogue has finally moved beyond its experimental status and become practical."
Context: GitHub README güncellemeleri
Confidence: high

**AIlice Teknik Özeti:**
- **Dil:** Python
- **Kurulum:** pip install, çoklu bağımlılıklar
- **Lisans:** Belirtilmemiş
- **Türkçe desteği:** LLM modeline bağlı (GPT-4, Claude veya yerel model)
- **Bellek:** IACT ağacı içinde bağlamsal bellek
- **Ses:** ChatTTS entegrasyonu
- **Aktif geliştirme:** Evet, MCP desteği yeni eklendi

---

### 6. PyGPT

Claim: PyGPT, Python ile yazılmış, Linux/Windows/Mac için masaüstü bir AI asistanıdır. 12 çalışma modu (Chat, Vision, Agents, Computer Use, Autonomous Mode) ve çoklu model desteği (OpenAI, Claude, DeepSeek, Ollama, vb.) sunar [^21^].
Source: PyGPT official website
URL: https://pygpt.net/
Date: 2026-02-06
Excerpt: "Open Source, Personal Desktop AI Assistant for Linux, Windows, and Mac with Chat, Vision, Agents, Image and Video generation, Tools, Voice control and more."
Context: Resmi PyGPT web sitesi
Confidence: high

Claim: PyGPT, yerel dosyalarla konuşma (RAG), yerleşik Python kod yorumcusu, zamanlama (crontab), eklenti sistemi ve MCP desteği sunar [^22^].
Source: GitHub - szczyglis-dev/py-gpt
URL: https://github.com/szczyglis-dev/py-gpt
Date: 2026-02-06
Excerpt: "12 modes of operation... Chat with your own Files: integrated LlamaIndex support... Crontab / Task scheduler included... MCP support."
Context: Resmi GitHub reposu
Confidence: high

**PyGPT Teknik Özeti:**
- **Dil:** Python
- **Kurulum:** pip install pygpt-net veya snap
- **Lisans:** Belirtilmemiş (açık kaynak)
- **Türkçe desteği:** LLM modeline bağlı
- **Bellek:** LlamaIndex entegrasyonu, yerel vektör veritabanı
- **Ses:** Azure, Google, Eleven Labs, OpenAI TTS; Whisper, Google/Microsoft STT
- **Aktif geliştirme:** Evet

---

### 7. Witsy

Claim: Witsy, evrensel bir MCP (Model Context Protocol) istemcisidir ve neredeyse herhangi bir LLM sağlayıcısı ile çalışabilir. BYOK (Bring Your Own Keys) felsefesini benimser [^23^].
Source: GitHub - Kochava-Studios/witsy
URL: https://github.com/Kochava-Studios/witsy
Date: 2026-03-04
Excerpt: "Witsy is a BYOK (Bring Your Own Keys) AI application... It is the first of very few (only?) universal MCP clients: Witsy allows you to run MCP servers with virtually any LLM!"
Context: Resmi GitHub reposu
Confidence: high

Claim: Witsy, RAG (belgelerle sohbet), sesli transkripsiyon/dikte, gerçek zamanlı sesli sohbet, uzun vadeli bellek eklentisi ve "Prompt Anywhere" özelliği (herhangi bir uygulamada klavye kısayolu ile AI kullanma) sunar [^24^].
Source: GitHub - Kochava-Studios/witsy
URL: https://github.com/Kochava-Studios/witsy
Date: 2026-03-04
Excerpt: "Prompt anywhere allows to generate content directly in any application... Chat with your local files and documents (RAG)... Realtime Chat aka Voice Mode"
Context: Özellik listesi
Confidence: high

**Witsy Teknik Özeti:**
- **Dil:** Belirtilmemiş (muhtemelen TypeScript/Electron)
- **Kurulum:** macOS (brew), Windows, Linux binary
- **Lisans:** Belirtilmemiş
- **Türkçe desteği:** LLM ve STT/TTS sağlayıcıya bağlı
- **Bellek:** Uzun vadeli bellek eklentisi
- **Ses:** Çoklu STT/TTS sağlayıcı, yerel Whisper
- **Aktif geliştirme:** Evet

---

### 8. TinyClaw

Claim: TinyClaw, yerel çerçeve, küçük çekirdek ve modüler eklenti mimarisi ile tasarlanmış, kendini iyileştiren zamansal bellek (self-improving temporal memory) ve akıllı sorgu yönlendirme (smart routing) sunan hafif bir AI ajan çerçevesidir [^25^].
Source: SourceForge - TinyClaw
URL: https://sourceforge.net/projects/tinyclaw.mirror/
Date: 2026-03-02
Excerpt: "TinyClaw incorporates self-improving memory and smart routing mechanisms intended to reduce large language model costs by tiering queries intelligently."
Context: SourceForge açıklaması
Confidence: high

Claim: TinyClaw'in güvenlik modeli "SHIELD.md" adlı yerleşik bir anti-malware uygulaması içerir; bu diğer çerçevelerde bulunmayan bir özelliktir [^26^].
Source: GitHub - warengonzaga/tinyclaw
URL: https://github.com/warengonzaga/tinyclaw
Date: 2026-02-04
Excerpt: "Built-in SHIELD.md anti-malware enforcement... No native threat model (in other frameworks)"
Context: GitHub karşılaştırma tablosu
Confidence: high

**TinyClaw Teknik Özeti:**
- **Dil:** Bun-native runtime
- **Kurulum:** Self-configuring, tek binary
- **Lisans:** GPL v3
- **Türkçe desteği:** LLM sağlayıcıya bağlı (Ollama Cloud)
- **Bellek:** Zamansal bozunma ile episodic bellek, 4 katmanlı sıkıştırma
- **Ses:** Belirtilmemiş
- **Aktif geliştirme:** Evet

---

### 9. Letta (eski adıyla MemGPT)

Claim: Letta, UC Berkeley BAIR Lab'den çıkan, ajanların kendi belleğini yönetmesine olanak tanıyan, OS-tarzı katmanlı bellek mimarisi (Core/Archival/Recall) kullanan açık kaynaklı bir AI ajan çerçevesidir [^27^].
Source: Ry Walker Research
URL: https://rywalker.com/research/letta
Date: 2026-02-22
Excerpt: "Letta's core innovation is a tiered memory architecture inspired by operating system memory management. Agents have Core Memory (always in the LLM context window), Archival Memory (vector database for long-term storage), and Recall Memory (full conversation history)."
Context: Letta detaylı analiz
Confidence: high

Claim: Letta, ajanların oturumlar arası bilgi saklamasını, tercihleri hatırlamasını ve sonsuza dek öğrenmesini sağlayan kalıcı uzun vadeli bellek sunar [^28^].
Source: Railway - Deploy Letta
URL: https://railway.com/deploy/letta-ai-agent
Date: 2026-04-27
Excerpt: "Unlike stateless LLM API calls, Letta agents maintain persistent memory across conversations, enabling them to remember context, preferences, and learned information indefinitely."
Context: Letta tanıtım sayfası
Confidence: high

Claim: Letta, Apache 2.0 lisanslıdır, Docker ile self-hosted çalıştırılabilir ve PostgreSQL + pgvector ile vektör bellek deposu kullanır [^29^].
Source: Railway - Deploy Letta
URL: https://railway.com/deploy/letta-ai-agent
Date: 2026-04-27
Excerpt: "Self-host Letta on Railway with this template that pre-configures the Letta server, a PostgreSQL database with pgvector for vector embeddings, and password-protected API access."
Context: Self-hosting dokümantasyonu
Confidence: high

**Letta Teknik Özeti:**
- **Dil:** Python
- **Kurulum:** Docker Compose ile PostgreSQL + pgvector
- **Lisans:** Apache 2.0
- **Türkçe desteği:** LLM modeline bağlı
- **Bellek:** Core/Archival/Recall üç katmanlı bellek (en gelişmiş)
- **Ses:** Belirtilmemiş
- **Aktif geliştirme:** Evet, $10M seed yatırım aldı

---

## Karşılaştırma Matrisi

| Kriter | OpenJarvis | LocalAGI | Home Assistant+Assist | OpenVoiceOS | AIlice | PyGPT | Witsy | TinyClaw | Letta |
|--------|-----------|----------|------------------------|-------------|--------|-------|-------|----------|-------|
| **Dil** | Python | Go | Python | Python | Python | Python | TS/Electron | Bun/JS | Python |
| **Kurulum Kolaylığı** | uv sync | Docker Compose | HA OS + Add-ons | TUI installer | pip (karmaşık) | pip/snap | Binary | Self-config | Docker |
| **Türkçe Ses** | Yok | Yok | Speech-to-Phrase + Piper | Çeviri katmanı | LLM bağlı | LLM bağlı | LLM bağlı | LLM bağlı | LLM bağlı |
| **Yerel Çalışma** | Evet (yerel-öncelik) | Evet (tamamen) | Evet (opsiyonel) | Evet | Evet (yerel LLM) | Opsiyonel | Opsiyonel | Evet | Evet (self-hosted) |
| **Genişletilebilirlik** | Yüksek (çerçeve) | Yüksek (Go eylemler) | Orta (entegrasyon) | Yüksek (solver/persona) | Çok Yüksek (modül) | Yüksek (eklenti) | Yüksek (MCP) | Yüksek (eklenti) | Yüksek (araçlar) |
| **Bellek Sistemi** | Yerel izleme | RAG + LocalRecall | Konuşma geçmişi | Solver zinciri | IACT ağacı | LlamaIndex | Uzun vadeli bellek | Zamansal bellek | Core/Archival/Recall |
| **Ajan Ekip** | Yok | Evet | Yok | Yok | IACT (dinamik) | Agents modu | Yok | Yok | Multi-agent |
| **Ses Pipeline** | Yok | Yok | Whisper/Piper/STP | phoonnx/Piper | ChatTTS | Çoklu | Çoklu | Yok | Yok |
| **MCP Desteği** | Belirsiz | Evet (yerel) | Yok | Yok | Evet | Evet | Evet (evrensel) | Belirsiz | Belirsiz |
| **Aktif Geliştirme** | Yüksek (Stanford) | Yüksek | Çok Yüksek | Orta-Yüksek | Orta | Orta | Orta | Düşük-Orta | Yüksek |
| **Lisans** | Apache 2.0 | Açık kaynak | Apache 2.0 | Belirsiz | Belirsiz | Açık kaynak | Belirsiz | GPL v3 | Apache 2.0 |

---

## Hangi Çözüm Üzerine İnşa Etmek Daha Mantıklı?

Claim: Tamamen yerel, gizlilik-öncelikli bir AI asistanı için hiçbir tek çözüm yeterli değildir; en iyi yaklaşım bir hibrit mimari kullanmaktır [^30^].
Source: Birden fazla kaynağın sentezi
URL: N/A
Date: 2025-2026
Excerpt: Sentez analiz
Context: Karşılaştırmalı değerlendirme
Confidence: high

### Önerilen Strateji:

**"En İyi Bileşenlerin Birleşimi" - Hibrit Mimari:**

```
┌─────────────────────────────────────────────────────────────┐
│                     HİBRİT MİMARİ                            │
├─────────────────────────────────────────────────────────────┤
│  SES KATMANI          │  Home Assistant Assist + Wyoming     │
│  (Voice Interface)    │  Whisper (STT) / Piper (TTS)         │
│                       │  Speech-to-Phrase (Türkçe komutlar)  │
├───────────────────┬───┴─────────────────────────────────────┤
│  AKIL KATMANI     │   LocalAGI veya OpenJarvis            │
│  (Orchestration)  │   Ajan yönetimi, planlama, araç çağrı  │
├───────────────────┼───────────────────────────────────────────┤
│  BEYİN KATMANI    │   Ollama / vLLM / llama.cpp           │
│  (LLM Inference)  │   Yerel LLM çalıştırma                 │
├───────────────────┼───────────────────────────────────────────┤
│  BELLEK KATMANI   │   Letta (MemGPT)                       │
│  (Memory)         │   Core/Archival/Recall bellek         │
├───────────────────┼───────────────────────────────────────────┤
│  ARAÇ KATMANI     │   MCP sunucuları                       │
│  (Tools)          │   Dosya sistemi, tarayıcı, kod yürütme │
├───────────────────┼───────────────────────────────────────────┤
│  GÜVENLİK KATMANI │   Firecracker microVM sandbox          │
│  (Security)       │   Araç yetkilendirme, prompt koruması  │
└───────────────────┴───────────────────────────────────────────┘
```

Claim: Home Assistant Assist, Wyoming protokolü ile en olgun yerel ses pipeline'ını sunar ve Speech-to-Phrase Türkçe desteği ile öne çıkar [^31^].
Source: GitHub - OHF-Voice/speech-to-phrase + Home Assistant blog
URL: https://github.com/OHF-voice/speech-to-phrase
Date: 2025-01-24
Excerpt: "Türkçe (Turkish)" listed under supported languages.
Context: Türkçe ses desteği doğrulaması
Confidence: high

Claim: Letta'nın üç katmanlı bellek mimarisi (Core/Archival/Recall), mevcut açık kaynak çözümler arasında en sofistike ve üretime hazır bellek sistemidir [^32^].
Source: Ry Walker Research + Letta blog
URL: https://rywalker.com/research/letta
Date: 2026-02-22
Excerpt: "Letta occupies a unique niche: it's the most serious open-source attempt at solving LLM memory as a first-class concern."
Context: Letta bellek analizi
Confidence: high

Claim: LocalAGI, Go tabanlı hafif mimarisi ve yerel MCP sunucu desteği ile araç yönetimi ve çoklu ajan koordinasyonu için ideal bir orkestrasyon katmanıdır [^33^].
Source: GitHub - mudler/LocalAGI
URL: https://github.com/mudler/LocalAGI
Date: 2026-02-16
Excerpt: "Advanced Agent Teaming... local MCP server support... Extensible Custom Actions in Go (interpreted, no compilation!)"
Context: LocalAGI özellikleri
Confidence: high

---

## Dim 08: Güvenlik ve Gizlilik

### 1. Tamamen Yerel Çalışma Stratejisi (Air-Gapped)

Claim: Air-gapped (ağdan tamamen izole) AI dağıtımı, savunma sanayi, hükümet sınıflı ağları ve kritik altyapı için gereklidir; veri sızıntısı riskini sıfıra indirir [^34^].
Source: Digital Applied - Local LLM Privacy Guide
URL: https://www.digitalapplied.com/blog/local-llm-deployment-privacy-guide-2025
Date: 2025-12-26
Excerpt: "For maximum security, some organizations require completely network-isolated AI deployments... Zero data leaves your network. No third-party API provider access."
Context: Air-gapped dağıtım rehberi
Confidence: high

Claim: Ollama ve llama.cpp, air-gapped ortamlar için "Excellent" derecelendirmesi alır; tamamen offline çalışabilir, minimal bağımlılık içerir ve kaynak kodundan derlenebilir [^35^].
Source: Digital Applied Privacy Scorecard
URL: https://www.digitalapplied.com/blog/local-llm-deployment-privacy-guide-2025
Date: 2025-12-26
Excerpt: "Air-Gapped Support: Ollama - Excellent, Full offline operation after initial model download... llama.cpp - Excellent, Minimal dependencies, compile from source."
Context: Privacy karşılaştırma matrisi
Confidence: high

Claim: Air-gapped kurulum için: modelleri ağ bağlantılı sistemde indirin, sağlama toplamını (checksum) doğrulayın, şifreli USB/optik medya ile transfer edin, ağ kartlarını devre dışı bırakın, HSM kullanın ve fiziksel erişim kontrolü sağlayın [^36^].
Source: Digital Applied
URL: https://www.digitalapplied.com/blog/local-llm-deployment-privacy-guide-2025
Date: 2025-12-26
Excerpt: "Download models on a connected system. Verify checksums for integrity. Transfer via encrypted USB or optical media. Remove or disable network cards. Use hardware security module (HSM) for keys."
Context: Air-gapped kurulum adımları
Confidence: high

Claim: Yerel LLM dağıtımı, bulut API'lerine kıyasla daha düşük gecikme (100-300ms vs 500-1000ms), sabit maliyet, rate limit olmaması ve günde 100K+ token kullanımında ROI sağlar [^37^].
Source: Digital Applied
URL: https://www.digitalapplied.com/blog/local-llm-deployment-privacy-guide-2025
Date: 2025-12-26
Excerpt: "Lower latency (100-300ms vs 500-1000ms). Fixed costs vs pay-per-token. No rate limits or quotas. ROI at 100K+ tokens/day."
Context: Yerel dağıtım avantajları
Confidence: high

---

### 2. Sandbox: Docker Container Güvenliği ve Firecracker microVM

Claim: AI ajanları sandbox gerektirir çünkü gözden geçirilmemiş AI üretimi kod yürütür, prompt injection saldırıları ajan davranışını manipüle edebilir ve başarılı istismarlar veri sızdırmasına yol açabilir [^38^].
Source: Northflank Blog
URL: https://northflank.com/blog/how-to-sandbox-ai-agents
Date: 2026-02-02
Excerpt: "AI agents generate code you haven't reviewed or audited. Prompt injection attacks manipulate agent behavior to execute malicious actions. Compromised agents abuse APIs and system access beyond intended scope."
Context: Sandbox ihtiyacı
Confidence: high

Claim: Docker konteynerleri paylaşılan çekirdek (shared kernel) kullandığı için AI ajan sandbox'ı için tek başına yetersizdir; çekirdek güvenlik açıkları konteyner kaçışına (container escape) yol açabilir [^39^].
Source: Northflank Blog
URL: https://northflank.com/blog/how-to-sandbox-ai-agents
Date: 2026-02-02
Excerpt: "Docker containers share the host kernel. A kernel vulnerability or misconfiguration can allow container escape, giving attackers host access. AI agents generate unpredictable code that might exploit these vulnerabilities."
Context: Docker sınırlılıkları
Confidence: high

Claim: Firecracker microVM, AWS Lambda için geliştirilen, her sandbox'a kendi Linux çekirdeğini atayan, 125ms'de başlayan, başına ~5MB ek yük getiren donanım düzeyinde izolasyon sunar [^40^].
Source: Northflank Blog
URL: https://northflank.com/blog/how-to-sandbox-ai-agents
Date: 2026-02-02
Excerpt: "Firecracker creates lightweight virtual machines... Boots in ~125ms, less than 5 MiB overhead per VM... Hardware-level isolation. Each workload has a dedicated kernel completely separated from the host."
Context: Firecracker teknik detaylar
Confidence: high

Claim: E2B, Firecracker microVM üzerine kurulu, açık kaynaklı (Apache 2.0), AI ajanlar için kod yürütme sandbox'ıdır; 200ms'de başlar ve 24 saate kadar çalışabilir [^41^].
Source: E2B resmi web sitesi
URL: https://e2b.dev/
Date: 2026
Excerpt: "Secure, isolated cloud sandboxes for executing AI-generated code. Each sandbox runs in a Firecracker microVM, starts in ~80ms, and can run up to 24 hours."
Context: E2B sandbox özellikleri
Confidence: high

Claim: vmsan toolkit, Firecracker kullanarak komut satırından izole microVM oluşturmayı sağlar; Docker ile kıyaslandığında donanım düzeyinde izolasyon sunar [^42^].
Source: vmsan documentation
URL: https://mintlify.com/angelorc/vmsan/introduction
Date: 2026-03-04
Excerpt: "vmsan is a Firecracker microVM sandbox toolkit that lets you create, manage, and connect to isolated microVMs from the command line... With vmsan, you can boot a sandboxed VM in under 200ms."
Context: vmsan tanıtım
Confidence: high

Claim: Üretim ortamındaki AI ajan sandbox'ı için karar verme kriteri şudur: sandbox ihlal edilirse en kötü senaryo nedir? Etki yalnızca mevcut göreve sınırlıysa konteyner yeterlidir; diğer kullanıcıların verilerine etki edebilirse microVM gerekir [^43^].
Source: Medium - AI Agent Code Execution Sandboxes
URL: https://addozhang.medium.com/ai-agent-code-execution-sandboxes-isolation-from-containers-to-microvms-e80848effea5
Date: 2026-03-30
Excerpt: "Impact limited to the current task only → containers are sufficient. Could affect other users' data on the same host → microVM required. Publicly exposed, with motivated attackers → microVM, and seriously evaluate ZeroBoot's maturity."
Context: Sandbox seçim kriteri
Confidence: high

**Sandbox Teknolojileri Karşılaştırması:**

| Teknoloji | İzolasyon Seviyesi | Başlangıç Süresi | Güvenlik Gücü | En İyi Kullanım |
|-----------|-------------------|------------------|---------------|-----------------|
| Docker | Süreç (paylaşılan çekirdek) | Milisaniye | Süreç düzeyi | Güvenilir iş yükleri |
| gVisor | Sistem çağrısı engelleme | Milisaniye | Sistem çağrısı düzeyi | Çok kiracılı SaaS |
| Firecracker | Donanım (özel çekirdek) | ~125ms | Donanım zorlamalı | Sunucusuz, AI çıkarımı, güvensiz kod |
| Kata Containers | Donanım (VMM aracılığı) | ~200ms | Donanım zorlamalı | Kubernetes, düzenlenmiş endüstriler |

---

### 3. Prompt Injection Saldırıları ve Korunma Yöntemleri

Claim: Prompt injection, LLM uygulamaları için birincil tehdit olarak 2025 OWASP Top 10 listesinde (LLM01:2025) yer almaktadır [^44^].
Source: OWASP Top 10 for LLM Applications
URL: https://owasp.org/www-project-top-10-for-large-language-model-applications/
Date: 2025
Excerpt: "LLM01:2025—Prompt Injection. Manipulating LLMs via crafted inputs can lead to unauthorized access, data breaches, and compromised decision-making."
Context: OWASP resmi listesi
Confidence: high

Claim: Microsoft Research'ün Spotlighting teknikleri, güvenilir komutlar ile güvenilir olmayan veri arasındaki sınırları belirginleştirir: Delimiting, Datamarking ve Encoding [^45^].
Source: CyberDesserts Blog
URL: https://blog.cyberdesserts.com/prompt-injection-attacks/
Date: 2025-12-22
Excerpt: "Microsoft has published a three-layer framework... Prevention Through Spotlighting: Delimiting (clearly mark where instructions end), Datamarking (tag untrusted content), Encoding (Base64 encode external inputs)."
Context: Prompt injection savunma stratejileri
Confidence: high

Claim: Anthropic, takviyeli öğrenme (reinforcement learning) ile Claude'u prompt injection'a karşı eğitmiş ve Opus 4.5 ile tarayıcı ajanlarındaki saldırı başarı oranını çift haneli rakamlardan ~%1'e düşürmüştür [^46^].
Source: CyberDesserts Blog
URL: https://blog.cyberdesserts.com/prompt-injection-attacks/
Date: 2025-12-22
Excerpt: "Anthropic uses reinforcement learning during model training... This approach reduced attack success rates for browser agents from double digits to approximately 1% with Opus 4.5."
Context: Model düzeyinde güvenlik eğitimi
Confidence: high

Claim: Google DeepMind'in CaMeL çerçevesi, LLM'i "asla güvenilmeyen bir bileşen" olarak ele alır; Privileged LLM (P-LLM) kontrol akışını, Quarantined LLM (Q-LLM) güvenilir olmayan veriyi işler; yetenek tabanlı (capability-based) güvenlik politikaları uygular [^47^].
Source: Google DeepMind - CaMeL paper
URL: https://arxiv.org/abs/2503.18813
Date: 2025-03-24
Excerpt: "CaMeL creates a protective system layer around the LLM, securing it even when underlying models are susceptible to attacks. To operate, CaMeL explicitly extracts the control and data flows from the (trusted) query; therefore, the untrusted data retrieved by the LLM can never impact the program flow."
Context: CaMeL akademik makalesi
Confidence: high

Claim: CaMeL, AgentDojo güvenlik benchmark'ında %77 oranında görevi "kanıtlanabilir güvenlik" ile çözer; savunmasız sistem %84 başarı oranına sahiptir ancak güvenlik garantisi yoktur [^48^].
Source: arXiv - Defeating Prompt Injections by Design
URL: https://arxiv.org/abs/2503.18813
Date: 2025-03-24
Excerpt: "We demonstrate effectiveness of CaMeL by solving 77% of tasks with provable security (compared to 84% with an undefended system) in AgentDojo."
Context: CaMeL performans sonuçları
Confidence: high

Claim: Simon Willison (prompt injection terimini bulan kişi), CaMeL'i "güçlü garantiler sağladığını iddia eden ilk önleme" olarak nitelendirmiştir [^49^].
Source: Simon Willison's blog
URL: https://simonwillison.net/2025/Apr/11/camel/
Date: 2025-04-11
Excerpt: "In the two and a half years that we've been talking about prompt injection attacks I've seen alarmingly little progress towards a robust solution. The new paper from Google DeepMind finally bucks that trend."
Context: CaMeL değerlendirmesi
Confidence: high

Claim: Meta'nın "Agents Rule of Two" ilkesi: Bir ajan özel veriye erişimi varsa ve harici olarak iletişim kurabiliyorsa, insan onayı olmadan durum değiştirememelidir [^50^].
Source: CyberDesserts Blog
URL: https://blog.cyberdesserts.com/prompt-injection-attacks/
Date: 2025-12-22
Excerpt: "Meta's 'Agents Rule of Two' principle: if an agent has access to private data and can communicate externally, it must not be able to change state without human approval."
Context: Meta güvenlik prensibi
Confidence: high

---

### 4. Araç Yetkilendirme (Tool Authorization)

Claim: MCP (Model Context Protocol), 150M+ indirme, 7,000+ halka açık sunucu ve tahmini 200,000 savunmasız örnekle kritik bir mimari güvenlik açığı içerir [^51^].
Source: OX Security Research
URL: https://www.ox.security/blog/the-mother-of-all-ai-supply-chains-critical-systemic-vulnerability-at-the-core-of-the-mcp/
Date: 2026-04-15
Excerpt: "The OX Security Research team has uncovered a critical, systemic vulnerability at the core of MCP... 150M+ downloads, 7,000+ publicly accessible servers — and up to 200,000 vulnerable instances in total."
Context: MCP güvenlik araştırması
Confidence: high

Claim: MCP'nin STDIO taşıma modu, işletim sistemi komutlarını herhangi bir sanitize işlemi olmaksızın yürütür; bu, yetkisiz komut yürütme (RCE) riski oluşturur [^52^].
Source: VentureBeat
URL: https://venturebeat.com/security/mcp-stdio-flaw-200000-ai-agent-servers-exposed-ox-security-audit
Date: 2026-05-02
Excerpt: "MCP's STDIO transport, the default for connecting an AI agent to a local tool, executes any operating system command it receives. No sanitization. No execution boundary between configuration and command."
Context: MCP STDIO güvenlik açığı
Confidence: high

Claim: OWASP MCP Top 10 (2025) listesi, MCP ekosistemindeki 10 kritik riski tanımlar: Token Mismanagement, Privilege Escalation, Tool Poisoning, Supply Chain, Command Injection, Prompt Injection, Authentication/Authorization, Audit/Telemetry, Shadow MCP Servers, Context Injection [^53^].
Source: OWASP MCP Top 10
URL: https://owasp.org/www-project-mcp-top-10/
Date: 2025
Excerpt: "MCP1:2025 – Token Mismanagement & Secret Exposure... MCP2:2025 – Privilege Escalation via Scope Creep... MCP3:2025 – Tool Poisoning... MCP4:2025 – Supply Chain..."
Context: OWASP MCP güvenlik listesi
Confidence: high

Claim: Araç yetkilendirmede "en az yetki" prensibi uygulanmalıdır; ajanların yalnızca görev için gerekli olan araçlara erişimi olmalı ve hassas eylemler (e-posta gönderme, kod yürütme, kimlik bilgilerine erişim) insan onayı gerektirmelidir [^54^].
Source: CyberDesserts Blog
URL: https://blog.cyberdesserts.com/prompt-injection-attacks/
Date: 2025-12-22
Excerpt: "Enforce least privilege: LLM connections to other systems should have minimal permissions... Require human approval: Sensitive actions should require explicit user confirmation."
Context: Araç yetkilendirme prensipleri
Confidence: high

Claim: Human-in-the-loop (HITL) için LangGraph `interrupt()` fonksiyonu, CrewAI `human_input` bayrağı, HumanLayer `@require_approval()` dekoratörü ve Permit.io yetkilendirme motoru kullanılabilir [^55^].
Source: Permit.io Blog
URL: https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo
Date: 2025-06-04
Excerpt: "LangGraph: interrupt() pauses the graph for human input. CrewAI: human_input flag and HumanTool support. HumanLayer: @require_approval() decorator."
Context: HITL entegrasyon araçları
Confidence: high

**Önerilen Araç Yetkilendirme Matrisi:**

| Eylem Kategorisi | Otomatik Çalıştırma | İnsan Onayı Gerekli | Açıklama |
|------------------|--------------------|---------------------|----------|
| Dosya okuma (sadece okuma) | Evet | Hayır | Sadece izin verilen dizinler |
| Dosya yazma | Hayır | Evet | Veri kaybı riski |
| Kod yürütme (sandbox) | Evet | Hayır | Firecracker microVM içinde |
| Kod yürütme (host) | Hayır | Evet | Sistem güvenliği riski |
| Web tarama | Evet | Hayır | Read-only içerik |
| E-posta gönderme | Hayır | Evet | İletişim güvenliği |
| Sistem komutu çalıştırma | Hayır | Evet | Yüksek risk |
| API çağrısı (read-only) | Evet | Hayır | Okuma erişimli API'ler |
| API çağrısı (write) | Hayır | Evet | Veri değiştirme riski |
| Bellek güncelleme | Evet | Hayır | Ajan kendi belleğini yönetir |

---

### 5. Veri Gizliliği: Kullanıcı Verilerinin Saklanması ve Şifrelenmesi

Claim: Yerel AI dağıtımında veri şifreleme üç durumda uygulanmalıdır: dinlenme halinde (at-rest), iletim sırasında (in-transit) ve kullanım sırasında (in-use) [^56^].
Source: Go Abacus
URL: https://goabacus.co/technology/local-llm
Date: Belirsiz
Excerpt: "FIPS 140-2 compliant encryption for local LLM data at rest and in transit."
Context: Yerel LLM güvenlik gereksinimleri
Confidence: high

Claim: AI ajan veri saklama için: AES-256 veya eşdeğer şifreleme, müşteri tarafından yönetilen anahtarlar (CMK) HSM'lerde saklanmalı, TLS 1.2+ iletim şifrelemesi kullanılmalıdır [^57^].
Source: Medium - Securing On-Prem LLM
URL: https://medium.com/@tatielefreitas/securing-on-prem-llm-platforms-key-requirements-for-air-gapped-deployments-8eb9f280448b
Date: 2025-09-17
Excerpt: "At rest: Encrypt all data stores, logs, and backups with AES-256 or equivalent. Use customer-managed keys (CMKs) stored in HSMs. In transit: Require TLS 1.2+ and enable Perfect Forward Secrecy."
Context: On-prem LLM güvenlik gereksinimleri
Confidence: high

Claim: Fast.io gibi çözümler, AI ajanları için uçtan uca şifreleme (E2EE), sıfır bilgi mimarisi ve katı erişim kontrolleri sunar; ajan verilerini izole çalışma alanlarında (workspace) saklar [^58^].
Source: Fast.io - Privacy-Focused Storage
URL: https://fast.io/resources/best-privacy-focused-storage-ai-agents/
Date: 2026-02-13
Excerpt: "Privacy-focused storage for AI agents provides end-to-end encryption, zero-knowledge architecture, or strict access controls... 65% of enterprises now require privacy-preserving storage for their AI deployments."
Context: AI ajan veri depolama güvenliği
Confidence: medium

Claim: Letta'nın self-hosted versiyonunda, PostgreSQL + pgvector veritabanı ajan durumu, konuşma geçmişi ve vektör bellek embeddings'leri saklar; SECURE=true ve LETTA_SERVER_PASSWORD ile API erişimi korunur [^59^].
Source: Railway - Deploy Letta
URL: https://railway.com/deploy/letta-ai-agent
Date: 2026-04-27
Excerpt: "The template deploys two services: the Letta application server and a PostgreSQL database with pgvector extension... SECURE=true, LETTA_SERVER_PASSWORD=your-secure-password."
Context: Letta veri güvenliği yapılandırması
Confidence: high

**Önerilen Veri Gizlilik Stratejisi:**

```
1. KONUŞMA GEÇMİŞİ:
   - SQLite/PostgreSQL yerel veritabanında saklanır
   - AES-256 ile şifrelenir
   - CMK (Customer Managed Key) kullanılır
   - Otomatik temizleme politikası (retention policy)

2. BELLEK EMBEDDINGS:
   - pgvector ile vektör veritabanında saklanır
   - Aynı şifreleme anahtarı ile korunur
   - Kullanıcı bazlı izolasyon (row-level security)

3. AYARLAR VE KİMLİK BİLGİLERİ:
   - Anahtar zinciri/keyring kullanılır
   - API anahtarları asla düz metin olarak saklanmaz
   - Sistem ortam değişkenlerinden okunur

4. SES VERİSİ:
   - Mikrofon kayıtları geçici dosyalarda tutulur
   - İşlemden sonra hemen silinir
   - STT sonucu metin olarak saklanır

5. DOSYA ERİŞİMİ:
   - Chroot/sandbox ile izole dizinler
   - Ajan yalnızca izin verilen dizinlere erişir
   - Filtrelenmiş dosya türleri (sadece .txt, .pdf, vs.)
```

---

## Sentez ve Öneriler

### Mimari Önerisi: "JARVIS Hibrit Stack"

```
┌────────────────────────────────────────────────────────────┐
│  🎙️ SES Arayüzü                                          │
│  Home Assistant Assist + Wyoming Protocol                 │
│  STT: Whisper (genel) / Speech-to-Phrase (Türkçe komut) │
│  TTS: Piper (Türkçe ses modeli)                           │
├────────────────────────────────────────────────────────────┤
│  🧠 Orkestrasyon Katmanı                                   │
│  OpenJarvis veya LocalAGI (ajana karar verilmeli)        │
│  - Ajan planlama ve akıl yürütme                           │
│  - Araç çağrı yönetimi                                    │
│  - MCP sunucu entegrasyonu                                │
├────────────────────────────────────────────────────────────┤
│  🧬 LLM Çıkarım Katmanı                                    │
│  Ollama / vLLM / llama.cpp                                 │
│  - Gemma-3-12B veya Qwen-32B gibi çok dilli modeller       │
│  - Tamamen yerel, API anahtarı yok                         │
├────────────────────────────────────────────────────────────┤
│  💾 Bellek Katmanı                                         │
│  Letta (Core/Archival/Recall)                             │
│  - PostgreSQL + pgvector                                   │
│  - Kullanıcı tercihleri, konuşma geçmişi                   │
│  - SQLite yedekli yerel bellek                             │
├────────────────────────────────────────────────────────────┤
│  🛡️ Güvenlik Katmanı                                       │
│  A. Sandbox: Firecracker microVM (kod yürütme)           │
│  B. Prompt Injection: Input/output filtreleme              │
│  C. Araç Yetkilendirme: HITL + en az yetki prensibi       │
│  D. Veri Şifreleme: AES-256, TLS 1.3                      │
│  E. Ağ İzolasyonu: Air-gapped opsiyonu                    │
└────────────────────────────────────────────────────────────┘
```

### Güvenlik Checklist:

- [ ] Tüm bileşenler yerel ağda çalışıyor, bulut API'si isteğe bağlı
- [ ] Kod yürütme Firecracker microVM içinde izole
- [ ] Hassas eylemler (e-posta, silme, yazma) insan onayı gerektiriyor
- [ ] Kullanıcı verileri AES-256 ile şifrelenmiş
- [ ] API anahtarları HSM/keyring'de saklanıyor
- [ ] Konuşma kayıtları otomatik olarak belirli süre sonra siliniyor
- [ ] MCP sunucuları yetkilendirme ve denetim ile çalışıyor
- [ ] OWASP LLM Top 10 2025 ve MCP Top 10 riskleri değerlendirildi
- [ ] Prompt injection koruması için Spotlighting veya CaMeL benzeri mimari
- [ ] Düzenli adversarial test ve güvenlik denetimi yapılıyor

---

## Kaynakça

[^1^]: https://scalingintelligence.stanford.edu/blogs/openjarvis/ (2026-03-12)
[^2^]: https://github.com/open-jarvis/OpenJarvis (2026-05-05)
[^3^]: https://scalingintelligence.stanford.edu/blogs/openjarvis/ (2026-03-12)
[^4^]: https://scalingintelligence.stanford.edu/blogs/openjarvis/ (2026-03-12)
[^5^]: https://github.com/mudler/LocalAGI (2026-02-16)
[^6^]: https://github.com/mudler/LocalAGI (2026-02-16)
[^7^]: https://github.com/mudler/LocalAGI (2026-02-16)
[^8^]: https://github.com/mudler/LocalAGI/releases (2026-02-16)
[^9^]: https://www.home-assistant.io/integrations/wyoming/ (2026-04-01)
[^10^]: https://www.home-assistant.io/blog/2025/06/25/voice-chapter-10/ (2025-06-25)
[^11^]: https://github.com/OHF-voice/speech-to-phrase (2025-01-24)
[^12^]: https://sanyamc-blog.pages.dev/p/building-a-voice-assistant/ (2025-06-20)
[^13^]: https://www.cnx-software.com/2025/02/24/the-openvoiceos-foundation-aims-to-enable-open-source-privacy-and-customization-for-voice-assistants/ (2025-02-24)
[^14^]: https://openvoiceos.github.io/ovos-technical-manual/150-personas/ (2025-04-15)
[^15^]: https://github.com/OpenVoiceOS/ovos-persona (2023-03-25)
[^16^]: https://www.cnx-software.com/2025/02/24/the-openvoiceos-foundation-aims-to-enable-open-source-privacy-and-customization-for-voice-assistants/ (2025-02-24)
[^17^]: https://github.com/myshell-ai/AIlice (2025)
[^18^]: https://medium.com/@stevenlu1729/building-jarvis-from-iron-man-dreams-to-reality-6cca0eb4d210 (2025-06-09)
[^19^]: https://docs.myshell.ai/technology/ailice (2024-12-27)
[^20^]: https://github.com/myshell-ai/AIlice (2025)
[^21^]: https://pygpt.net/ (2026-02-06)
[^22^]: https://github.com/szczyglis-dev/py-gpt (2026-02-06)
[^23^]: https://github.com/Kochava-Studios/witsy (2026-03-04)
[^24^]: https://github.com/Kochava-Studios/witsy (2026-03-04)
[^25^]: https://sourceforge.net/projects/tinyclaw.mirror/ (2026-03-02)
[^26^]: https://github.com/warengonzaga/tinyclaw (2026-02-04)
[^27^]: https://rywalker.com/research/letta (2026-02-22)
[^28^]: https://railway.com/deploy/letta-ai-agent (2026-04-27)
[^29^]: https://railway.com/deploy/letta-ai-agent (2026-04-27)
[^30^]: Sentez analiz (2026)
[^31^]: https://github.com/OHF-voice/speech-to-phrase (2025-01-24)
[^32^]: https://rywalker.com/research/letta (2026-02-22)
[^33^]: https://github.com/mudler/LocalAGI (2026-02-16)
[^34^]: https://www.digitalapplied.com/blog/local-llm-deployment-privacy-guide-2025 (2025-12-26)
[^35^]: https://www.digitalapplied.com/blog/local-llm-deployment-privacy-guide-2025 (2025-12-26)
[^36^]: https://www.digitalapplied.com/blog/local-llm-deployment-privacy-guide-2025 (2025-12-26)
[^37^]: https://www.digitalapplied.com/blog/local-llm-deployment-privacy-guide-2025 (2025-12-26)
[^38^]: https://northflank.com/blog/how-to-sandbox-ai-agents (2026-02-02)
[^39^]: https://northflank.com/blog/how-to-sandbox-ai-agents (2026-02-02)
[^40^]: https://northflank.com/blog/how-to-sandbox-ai-agents (2026-02-02)
[^41^]: https://e2b.dev/ (2026)
[^42^]: https://mintlify.com/angelorc/vmsan/introduction (2026-03-04)
[^43^]: https://addozhang.medium.com/ai-agent-code-execution-sandboxes-isolation-from-containers-to-microvms-e80848effea5 (2026-03-30)
[^44^]: https://owasp.org/www-project-top-10-for-large-language-model-applications/ (2025)
[^45^]: https://blog.cyberdesserts.com/prompt-injection-attacks/ (2025-12-22)
[^46^]: https://blog.cyberdesserts.com/prompt-injection-attacks/ (2025-12-22)
[^47^]: https://arxiv.org/abs/2503.18813 (2025-03-24)
[^48^]: https://arxiv.org/abs/2503.18813 (2025-03-24)
[^49^]: https://simonwillison.net/2025/Apr/11/camel/ (2025-04-11)
[^50^]: https://blog.cyberdesserts.com/prompt-injection-attacks/ (2025-12-22)
[^51^]: https://www.ox.security/blog/the-mother-of-all-ai-supply-chains-critical-systemic-vulnerability-at-the-core-of-the-mcp/ (2026-04-15)
[^52^]: https://venturebeat.com/security/mcp-stdio-flaw-200000-ai-agent-servers-exposed-ox-security-audit (2026-05-02)
[^53^]: https://owasp.org/www-project-mcp-top-10/ (2025)
[^54^]: https://blog.cyberdesserts.com/prompt-injection-attacks/ (2025-12-22)
[^55^]: https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo (2025-06-04)
[^56^]: https://goabacus.co/technology/local-llm (Belirsiz)
[^57^]: https://medium.com/@tatielefreitas/securing-on-prem-llm-platforms-key-requirements-for-air-gapped-deployments-8eb9f280448b (2025-09-17)
[^58^]: https://fast.io/resources/best-privacy-focused-storage-ai-agents/ (2026-02-13)
[^59^]: https://railway.com/deploy/letta-ai-agent (2026-04-27)
