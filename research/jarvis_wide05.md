## Facet: Mevcut Tam Çözümler ve Entegre Platformlar

### Key Findings

- **OpenJarvis**, Stanford Üniversitesi araştırmacıları tarafından Mart 2026'da yayınlanan, yerel-first (local-first) kişisel AI ajan çerçevesidir. Beş modüler prensip (Intelligence, Engine, Agents, Tools & Memory, Learning) üzerine kuruludur ve Ollama, vLLM, SGLang, llama.cpp ve bulut API'leriyle çalışabilir [^124^][^133^].
- OpenJarvis, `jarvis init` komutuyla donanımı otomatik algılayıp uygun motor ve model yapılandırması önerir; `jarvis bench` ile enerji, gecikme ve throughput kıyaslama yapar [^140^][^146^].
- **LocalAGI** (mudler/LocalAGI), Go tabanlı, Docker Compose ile tek komutla kurulan, OpenAI Responses API uyumlu, kısa ve uzun vadeli bellek (LocalRecall), ajan ekipleri ve Discord/Slack/Telegram entegrasyonu sunan bir platformdur [^31^][^36^].
- **Home Assistant Assist**, Wyoming protokolü üzerinden Whisper (STT), Piper (TTS) ve Ollama (LLM) ile tamamen yerel sesli asistan kurulumuna olanak tanır; Speech-to-Phrase aracı 21 dilde (Türkçe dahil) Raspberry Pi 4 üzerinde <1 saniyede çalışır [^137^][^144^].
- **Mycroft AI Inc.** Şubat 2023'te patent ihlali davası nedeniyle operasyonları durdurdu; topluluk **OpenVoiceOS (OVOS)** çatallamasıyla projeyi devam ettirmektedir ve Hollanda otoriteleri tarafından 2025'te resmi vakıf statüsü aldı [^99^].
- **OpenVoiceOS**, eklenti (plugin) tabanlı mimariyle Piper, Coqui TTS/XTTS (Türkçe dahil 17 dil), Whisper, VOSK, Edge TTS gibi çok sayıda STT/TTS motorunu destekler; Raspberry Pi 3/4/5 üzerinde çalışır [^138^][^145^].
- **AIlice** (MyShell), IACT (Interactive Agents Call Tree) mimarisiyle karmaşık görevleri dinamik ajan ağacına bölen, kodlama, sistem yönetimi, literatür taraması yapabilen, ChatTTS ile sesli diyalog ve MCP araçlarını destekleyen tam otonom bir ajan çerçevesidir [^100^][^35^].
- **OpenClaw**, 2025 sonlarında Peter Steinberger tarafından "Clawdbot" adıyla başlatılan, Ocak 2026'da Anthropic marka şikayeti sonrası OpenClaw adını alan, MIT lisanslı, 355K+ GitHub star'a ulaşan, WhatsApp/Telegram/Discord üzerinden 7/24 otonom görev yürütebilen bir platformdur; ancak kabuk erişimi güvenlik riskleri taşır [^85^][^89^].
- **PyGPT**, Python tabanlı, çok modlu (chat, completion, vision, agent, image generation) masaüstü AI asistanıdır; OpenAI API'nin yanı sıra Ollama, HuggingFace, Google Gemini gibi alternatif modelleri destekler; eklenti sistemi, bağlam belleği ve sesli etkileşim içerir [^73^][^72^].
- **Witsy**, evrensel MCP (Model Context Protocol) istemcisi olarak konumlanan, 15+ AI sağlayıcısı ve Ollama'yı destekleyen, yerel belge RAG'i, gerçek zamanlı ses modu ve antropik Computer Use destekleyen BYOK masaüstü uygulamasıdır [^77^][^74^].
- **TinyClaw**, OpenClaw'a alternatif olarak geliştirilen, küçük yerel çekirdek, eklenti mimarisi, kendini iyileştiren temporal bellek, akıllı yönlendirme ve maliyet düşürme odaklı, GPL lisanslı hafif bir çerçevedir [^94^][^88^].
- Türkçe destek açısından Home Assistant Speech-to-Phrase Türkçe'yi 21 dil arasında destekler [^137^]; OVOS Coqui XTTS-v2 Türkçe'yi 17 dil arasında destekler [^138^]; OVOS MMS-TTS 1127 dili destekler [^138^]; VOSK Türkçe modeli mevcuttur [^80^].

---

## Detaylı Karşılaştırma

### 1. OpenJarvis

**Mimari ve Özellikler**
OpenJarvis, Stanford Üniversitesi Scaling Intelligence ekibi tarafından geliştirilen, kişisel cihazlarda çalışan yerel-first AI ajan altyapısıdır. Beş modüler prensip üzerine kuruludur [^124^][^133^]:

1. **Intelligence**: Birleşik model kataloğu; Qwen, GPT-OSS, Gemma, Granite, GLM, Kimi gibi aileleri otomatik olarak donanıma göre eşleştirir.
2. **Engine**: Çıkarım (inference) çalışma zamanı; Ollama, vLLM, SGLang, llama.cpp, Apple Foundation Models, Exo, Nexa, Mirai Uzu gibi motorları ortak bir arayüzle sunar.
3. **Agents**: Davranış katmanı; Orchestrator (görev bölme), Operative (hafif yinelenen iş akışları) gibi rolleri destekler.
4. **Tools & Memory**: MCP (Model Context Protocol), Google A2A (ajanlar arası iletişim), semantik indeksleme, dosya okuma/yazma, web arama, kod yorumlayıcı içerir.
5. **Learning**: Yerel etkileşim izlerinden eğitim verisi üreten kapalı döngü iyileştirme; model ağırlıkları (SFT, GRPO, DPO), prompt optimizasyonu (DSPy), ajan mantığı (GEPA) ve motor ayarları (quantization) üzerinde optimizasyon yapar [^140^].

**Kurulum Kolaylığı**
Kurulum `pip install openjarvis` ile başlar; ardından `jarvis init` donanımı otomatik algılar ve uygun motor/model önerir [^96^][^141^]. `jarvis doctor` kurulum sağlığını kontrol eder. Quick-start script ile tarayıcı tabanlı React arayüzü ve FastAPI backend tek komutla başlar (`./scripts/quickstart.sh`) [^141^]. Masaüstü uygulaması macOS, Windows ve Linux için mevcuttur. `jarvis serve` komutu OpenAI API uyumlu FastAPI sunucusu başlatır [^146^].

**Ollama/vLLM Entegrasyonu**
Ollama "Recommended" olarak işaretlenmiştir; `ollama serve` ve `ollama pull qwen3:0.6b` sonrası `jarvis model list` ile otomatik algılanır [^98^]. vLLM veri merkezi NVIDIA GPU'lar (A100, H100) için önerilir; `vllm serve` komutu otomatik olarak `http://localhost:8000`'de algılanır. llama.cpp ise CPU/GGUF odaklı kullanım için desteklenir [^98^].

**Öğrenme Döngüsü ve Kişiselleştirme**
OpenJarvis'in en ayırt edici özelliği Learning prensibidir. Yerel etkileşim izleri (interaction traces) cihazda kalır ve bu izlerden dört katmanda optimizasyon yapılır [^140^]:
- Model ağırlıkları: SFT, GRPO, DPO ile fine-tuning
- Promptlar: DSPy ile otomatik prompt optimizasyonu
- Ajan mantığı: GEPA ile görev ayrıştırma ve araç seçimi iyileştirme
- Motor: Quantization seçimi ve batch scheduling

Ayrıca, enerji, FLOPs, gecikme ve dolar maliyeti birinci sınıf kısıtlar olarak değerlendirilir; 50 ms örnekleme aralıklıyla NVIDIA (NVML), AMD ve Apple Silicon enerji tüketimi ölçülür [^136^][^140^].

---

### 2. LocalAGI (mudler)

**Go Mimarisi ve Bellek Sistemi**
LocalAGI, Ettore Di Giacinto (mudler) tarafından geliştirilen Go tabanlı bir AI ajan yönetim platformudur. LocalAI ekosisteminin bir parçasıdır (LocalAI, LocalAGI, LocalRecall, Cogito) [^31^][^40^]. Bellek sistemi iki katmandan oluşur [^31^]:
- **Kısa vadeli bellek**: Konuşma geçmişi ve bağlam
- **Uzun vadeli bellek**: LocalRecall kütüphaneleri üzerine kurulu RAG (Retrieval Augmented Generation) bilgi tabanı; koleksiyonlar, dosya yükleme ve semantik arama içerir

**Ajan Ekipleri ve Otomasyonlar**
LocalAGI, "No-Code Agents" yaklaşımıyla web arayüzünden çoklu ajan yapılandırmasına izin verir [^31^]. "Advanced Agent Teaming" özelliği tek bir prompt ile işbirlikçi ajan ekipleri oluşturur. Ajanlar planlama, muhakeme ve adapte olma yeteneklerine sahiptir. Cron benzeri sözdizimi ile periyodik görevler planlanabilir. "Skills" sistemi, web arayüzünde yeniden kullanılabilir ajan becerileri oluşturma, düzenleme, içe/dışa aktarma ve git senkronizasyonu imkanı sunar [^31^].

**OpenAI-Compatible API**
LocalAGI, OpenAI Responses API'nin tam yerine geçebilen (drop-in replacement) bir REST API sunar [^31^][^36^]. Bu, mevcut OpenAI API istemcilerinin URL ve API key değiştirilerek LocalAGI'ya yönlendirilebileceği anlamına gelir. Ayrıca kapsamlı bir REST API, Discord/Slack/Telegram/GitHub Issues/IRC bağlayıcıları (connectors) ve SSE (Server-Sent Events) stream desteği içerir [^31^].

**Kurulum**
Docker Compose ile tek komut kurulumu vardır; CPU, NVIDIA GPU, Intel GPU ve AMD GPU için ayrı docker-compose dosyaları sunulur [^31^]:
```bash
docker compose up                    # CPU
MODEL_NAME=gemma-3-12b-it docker compose -f docker-compose.nvidia.yaml up  # GPU
```
Ön derlenmiş binary'ler de mevcuttur. Kaynak derlemesi için Go 1.20+, Git ve Bun 1.2+ gerekir [^31^].

---

### 3. Home Assistant + Assist

**Yerel Sesli Komut ve Wyoming Protokolü**
Home Assistant, Wyoming protokolü üzerinden harici ses hizmetlerini bağlayan açık bir standart kullanır [^32^]. Bu protokol sayesinde STT (Speech-to-Text), TTS (Text-to-Speech) ve wake-word algılama sistemleri TCP üzerinden ayrı makinelerde bile çalışabilir [^29^]. Yerel ses pipeline'ı üç bileşenden oluşur [^29^][^72^]:
1. **STT**: faster-whisper (GPU ile hızlandırılmış) veya Speech-to-Phrase (sınırlı komut seti, Raspberry Pi 4'te <1 saniye)
2. **TTS**: Piper (tamamen çevrimdışı, CPU'da çalışır, doğal sesli)
3. **LLM**: Ollama üzerinden yerel LLM (örn. llama3.2:3b)

**LLM Entegrasyonu**
Home Assistant, resmi Ollama entegrasyonu ile yerel LLM'leri konuşma ajanı olarak kullanabilir [^125^]. `configuration.yaml` üzerinden veya UI'dan yapılandırılabilir; model otomatik olarak indirilir. "Control Home Assistant" özelliği (deneysel) sayesinde LLM, Home Assistant varlıklarını ve cihazlarını kontrol edebilir [^125^]. Ayrıca topluluk tarafından geliştirilen `hass_local_openai_llm` entegrasyonu, llama.cpp, vLLM, LM Studio gibi OpenAI API uyumlu yerel sunucuları destekler ve TTS streaming, paralel araç çağrısı, Weaviate RAG gibi gelişmiş özellikler sunar [^127^].

**Ev Otomasyonu Odaklılığı**
Home Assistant'ın en güçlü yönü, doğal olarak ev otomasyonu ekosistemiyle entegre olmasıdır. `prefer_local_intents: true` ayarı ile "ışıkları aç" gibi basit komutlar yerel intent tanıma ile 200 ms'de işlenir; LLM yalnızca karmaşık veya anlaşılamayan istekler için devreye girer [^29^]. Home Assistant ayrıca AI-powered otomasyon önerileri sunar (isim, açıklama, kategori önerisi) [^129^].

**Kurulum Kolaylığı**
Home Assistant OS (HAOS) ile tek imaj kurulumu yapılabilir. Whisper ve Piper için resmi add-on'lar (eklentiler) mevcuttur; Wyoming protokolü ile otomatik keşif (auto-discovery) desteklenir [^32^]. Raspberry Pi 4/5, Intel NUC, eski PC'ler ve sanal makinelerde çalışır. Ses donanımı olarak Home Assistant Voice Preview Edition gibi hazır cihazlar satılır [^129^].

---

### 4. OpenVoiceOS / Mycroft

**Ses Odaklı Açık Kaynak Asistan**
Mycroft, 2015'te kurulan, gizlilik odaklı, Python tabanlı açık kaynak sesli asistan platformuydu. Ancak Mycroft AI Inc. Şubat 2023'te Voice Tech Corporation tarafından açılan 2020 patent ihlali davasının mali yükü nedeniyle operasyonları durdurdu ve ~20 çalışandan sadece 4 kişilik iskelet kadro ile kapatma sürecine girdi [^99^].

**OpenVoiceOS (OVOS) Durumu ve Geleceği**
Mycroft kapanmadan hemen sonra (Mart 2023) topluluk kod tabanını çatalladı ve 2020'lerin başından beri var olan **OpenVoiceOS (OVOS)** projesi resmi devamı haline geldi [^99^][^86^]. OVOS, 2025'te Hollanda otoriteleri tarafından resmi vakıf statüsü aldı ve Ekim 2025'te NGI Zero Commons Fund'dan hibe aldı [^99^]. Son sürümler (ovos-core 2.1.1+) aktif olarak sürdürülmektedir [^99^].

OVOS, etkinlik tabanlı (event bus) MessageBus mimarisiyle asenkron servisler arası iletişim sağlar; ses, beceri ve yapılandırma servisleri gevşek bağlı (loosely coupled) şekilde çalışır [^99^].

**Skill Sistemi ve Plugin Mimarisi**
OVOS, Mycroft'ın "skill" kavramını sürdürür; ancak modern yaklaşımda eklenti (plugin) tabanlı mimariye geçilmiştir [^142^][^130^]:
- **STT Plugin'leri**: faster-whisper, VOSK, Citrinet, NeMo, Meta MMS, wav2vec2, Chromium, Azure, Google Cloud, Whisper-LM, Nòs (Galician), HiTZ (Basque) [^139^][^151^]
- **TTS Plugin'leri**: Piper (yerel, CPU'da hızlı), Coqui TTS/XTTS (17 dil, ses klonlama), Edge-TTS (internet gerekli), Mimic (hafif robotik), ESpeak-NG, MaryTTS, Azure, Polly [^145^][^138^][^152^]
- **Wake Word Plugin'leri**: Precise-ONNX, Precise-Lite, VOSK [^130^]
- **Çözüm (Solver) Plugin'leri**: DuckDuckGo, Wikipedia, Wolfram Alpha, OpenAI persona [^130^]

**Kurulum ve Donanım**
OVOS, Docker, Python kurulum script'i (`ovos-installer`) ve Raspberry Pi için ön derlenmiş imajlar (`raspOVOS`) sunar [^97^][^100^].
- `lite`: STT/TTS kamuya açık sunuculara devreder (Pi 3 uyumlu olabilir)
- `hybrid`: STT sunucuya, TTS cihazda çalışır (Pi 4 önerilir)
- `offline`: Tamamen çevrimdışı, en az 4GB RAM (tercihen 8GB) [^100^]

---

### 5. AIlice

**Yerel Görev Yürütme Yetenekleri**
AIlice (MyShell.ai), JARVIS'ten ilham alan, tam otonom, genel amaçlı bir AI ajandır. IACT (Interactive Agents Call Tree) mimarisi kullanır; kullanıcı komutları bir "program" gibi çalıştırılır ve dinamik olarak alt ajanlara (subprograms) bölünür [^100^]. AIlice şu görevleri yerine getirebilir [^35^][^100^]:
- Tematik araştırma ve derinlemesine analiz
- Programlama görevleri ve script çalıştırma
- Sistem yönetimi (AI destekli işletim)
- Kapsamlı literatür taramaları
- Karmaşık, dinamik çoklu ajan işbirliği gerektiren görevler

**Mimari Özellikleri**
- **IACT**: Ajanlar birbiriyle etkileşime girebilir, hata durumunda üst ajanlarına yardım isteyebilir
- **Sesli diyalog**: ChatTTS entegrasyonu ile pratik sesli etkileşim (Ocak 2025 güncellemesi) [^100^]
- **MCP araçları**: Mart 2025 itibarıyla MCP (Model Context Protocol) araçlarını kullanabilir [^100^]
- **Çok modlu**: Görsel modelleri destekler; ekran görüntüsü üzerinden bilgisayar kontrolü ve fare/klavye simülasyonu geliştirme aşamasındadır [^100^]
- **Kendi kendini genişletme**: Ajanların yeni modül/agent türleri kodlayıp dinamik yüklemesi hedeflenir (AIliceEVO) [^100^]

**Model Desteği**
Hem açık kaynak modelleri hem de GPT-4 gibi ticari modelleri destekler [^35^]. Yerel LLM (Llama, DeepSeek vb.) ile çalışabilir.

---

### 6. Diğer Çözümler

#### OpenClaw
OpenClaw (eski adlarıyla Clawdbot, Moltbot), 2025 sonlarında PSPDFKit kurucusu Peter Steinberger tarafından "hafta sonu projesi" olarak başlatılan, en hızlı büyüyen açık kaynak projelerden biridir (355K+ GitHub star) [^85^][^89^]. MIT lisanslıdır ve 501(c)(3) vakıf tarafından yönetilir. Temel özellikleri [^89^][^93^]:
- 10+ mesajlaşma platformuna (WhatsApp, Telegram, Discord, Slack, iMessage, Signal) entegrasyon
- Kalıcı bellek (markdown dosyaları), cron benzeri zamanlanmış görevler (proactive assistance)
- Model-agnostic: Claude, GPT, Gemini, Ollama (yerel)
- 5.700+ topluluk becerisi (ClawHub)
- Kabuk komutları, dosya yönetimi, tarayıcı otomasyonu, API çağrıları, takvim yönetimi

**Güvenlik endişeleri**: OpenClaw, kullanıcı makinesinde kabuk erişimi ve dosya yönetimi yetkisi talep eder; yanlış yapılandırılmış örneklerde kimlik bilgileri sızdırma riskleri tespit edilmiştir [^89^][^93^]. Steinberger Şubat 2026'da OpenAI'a katılmıştır [^85^][^93^].

#### PyGPT
Python tabanlı masaüstü AI asistanıdır. OpenAI API'nin yanı sıra Ollama, HuggingFace, Langchain, Google Gemini, Anthropic Claude, xAI Grok gibi çok sayıda modeli destekler [^73^][^72^]. Özellikleri:
- 6+ çalışma modu: Chat, Assistant, Vision, Completion, Image Generation, Langchain
- Dosya sistemi erişimi, Python kod çalıştırma, sistem komutları, web arama (DuckDuckGo, Google, Bing)
- Bağlam belleği (kısa ve uzun vadeli), context geçmişi, ön ayar (preset) sistemi
- Ses tanıma (Whisper, Google, Bing), ses sentezi (Azure, Google, ElevenLabs, OpenAI TTS)
- Eklenti desteği (Files I/O, Code Interpreter, Web Search, MCP, Telegram, Slack, GitHub)
- Node tabanlı Agents Builder, crontab/görev zamanlayıcı, gerçek zamanlı kamera görüntüsü

Kurulum: `pip install pygpt-net` veya derlenmiş Windows/Linux/macOS sürümleri [^84^][^82^].

#### Witsy
"Universal MCP Client" olarak konumlanan BYOK masaüstü uygulamasıdır. Windows, macOS (Intel+Apple Silicon) ve Linux'ta çalışır [^77^][^79^]. Özellikleri:
- 15+ sağlayıcı: OpenAI, Anthropic, Google, xAI, Meta, Ollama, LM Studio, MistralAI, DeepSeek, OpenRouter, Groq, Cerebras, Azure
- MCP sunucularını neredeyse her LLM ile çalıştırma (evrensel MCP istemcisi iddiası)
- Yerel dosya RAG, scratchpad, "Prompt Anywhere" (herhangi bir uygulamada AI kullanma)
- Gerçek zamanlı ses modu, Anthropic Computer Use, uzun vadeli bellek eklentisi
- CLI arayüzü dahil (`witsy` komutu)

#### TinyClaw
OpenClaw'a alternatif, bağımsız bir projedir (GPLv3). "Karınca" (🐜) maskotuyla OpenClaw'ın "ıstakoz" (🦞) temasına karşıt olarak konumlanır [^94^].
- Yerel çekirdek + eklenti mimarisi; her şey eklenti olarak yüklenir
- Kendini iyileştiren temporal bellek (zamansal unutma/decay ile)
- Akıllı yönlendirme: Sorguları model/provider bazında katmanlara ayırarak maliyeti düşürür
- Ollama Cloud (ücretsiz kayıt, cömert limitler) dahili sağlayıcı
- 4 katmanlı context compaction ile context maliyetini düşürür
- SHIELD.md yerleşik anti-kötü amaçlı yazılım modeli
- Discord benzeri web arayüzü; kendi kişiliği vardır (kullanıcı tarafından değiştirilemez) [^94^]

---

## 7. Değerlendirme Kriterleri Karşılaştırması

| Kriter | OpenJarvis | LocalAGI | Home Assistant + Assist | OpenVoiceOS | AIlice | OpenClaw | PyGPT | Witsy | TinyClaw |
|---|---|---|---|---|---|---|---|---|---|
| **Tam Yerel Çalışabilirlik** | ⭐⭐⭐⭐⭐ (Tamamen yerel; bulut opsiyonel) [^133^] | ⭐⭐⭐⭐⭐ (Hiçbir veri dışarı çıkmaz) [^31^] | ⭐⭐⭐⭐⭐ (Tüm pipeline yerel) [^29^] | ⭐⭐⭐⭐⭐ (offline imaj ile tam yerel) [^100^] | ⭐⭐⭐⭐☆ (Yerel modellerle çalışır; ticari model de kullanılabilir) [^35^] | ⭐⭐⭐☆☆ (Yerel model Ollama ile; API key gerekebilir) [^89^] | ⭐⭐⭐☆☆ (Ollama desteği var ama API key odaklı) [^73^] | ⭐⭐⭐☆☆ (Ollama destekli ama BYOK odaklı) [^77^] | ⭐⭐⭐⭐☆ (Ollama Cloud dahili; yerel çalışır) [^94^] |
| **Türkçe Desteği** | ⭐⭐⭐☆☆ (Model bağlı; framework dili-agnostik) | ⭐⭐⭐☆☆ (Model bağlı; framework dili-agnostik) | ⭐⭐⭐⭐☆ (Speech-to-Phrase Türkçe destekliyor [^137^]; Whisper Türkçe destekler) | ⭐⭐⭐⭐☆ (XTTS-v2 Türkçe'yi destekler [^138^]; MMS 1127 dil; GlowTTS Türkçe [^138^]) | ⭐⭐⭐☆☆ (Model bağlı; sesli diyalog ChatTTS ile) | ⭐⭐⭐☆☆ (Model bağlı; mesajlaşma odaklı) | ⭐⭐⭐☆☆ (Çoklu dil desteği var; model bağlı) | ⭐⭐⭐☆☆ (Çoklu dil; model bağlı) | ⭐⭐⭐☆☆ (Model bağlı) |
| **Kurulum Kolaylığı** | ⭐⭐⭐⭐☆ (`pip install` + `jarvis init`; auto-detect) [^96^] | ⭐⭐⭐⭐⭐ (Docker Compose tek komut) [^31^] | ⭐⭐⭐⭐⭐ (HAOS tek imaj; add-on'lar) [^32^] | ⭐⭐⭐⭐☆ (Installer script veya Docker; Pi imajı var) [^97^] | ⭐⭐⭐☆☆ (Git clone; Python ortamı; teknik) [^100^] | ⭐⭐⭐☆☆ (`curl | bash`; Node.js 22+; 10-15 dk) [^89^] | ⭐⭐⭐⭐☆ (`pip install` veya derlenmiş binary) [^84^] | ⭐⭐⭐⭐☆ (Download & run; API key gerekli) [^79^] | ⭐⭐⭐⭐☆ (`bun dev`; web arayüzü ile self-config) [^94^] |
| **Genişletilebilirlik** | ⭐⭐⭐⭐⭐ (MCP, A2A, eklenti; Python SDK) [^124^] | ⭐⭐⭐⭐⭐ (Custom Actions Go kodu; Skills; MCP) [^31^] | ⭐⭐⭐⭐⭐ (Wyoming protokolü; geniş entegrasyon; HACS; n8n; MCP) [^38^][^127^] | ⭐⭐⭐⭐⭐ (Plugin tabanlı; STT/TTS/skill eklenti sistemi) [^145^] | ⭐⭐⭐⭐⭐ (MCP araçları; kendi kendini genişletme yol haritası) [^100^] | ⭐⭐⭐⭐⭐ (5.700+ ClawHub skill; eklenti mimarisi) [^87^] | ⭐⭐⭐⭐☆ (Eklenti sistemi; MCP desteği) [^73^] | ⭐⭐⭐⭐⭐ (Evrensel MCP; LLM plugin'leri) [^77^] | ⭐⭐⭐⭐☆ (Plugin tabanlı; eklenti geliştirme rehberi) [^94^] |
| **Bellek / Kişiselleştirme** | ⭐⭐⭐⭐⭐ (Kapalı döngü öğrenme; 4 katmanlı optimizasyon; semantik indeks) [^140^] | ⭐⭐⭐⭐⭐ (Kısa/uzun vadeli bellek; LocalRecall RAG) [^31^] | ⭐⭐⭐⭐☆ (Konuşma geçmişi; context penceresi; Weaviate RAG opsiyonel) [^127^] | ⭐⭐⭐☆☆ (Beceri bağlamı; kişisel ayarlar; LLM belleği model bağlı) | ⭐⭐⭐⭐☆ (Kalıcı bellek; interaktif ajan ağacı) [^100^] | ⭐⭐⭐⭐⭐ (Kalıcı markdown bellek; tercih öğrenimi; çoklu oturum) [^89^] | ⭐⭐⭐⭐☆ (Bağlam belleği; context geçmişi; uzun/kısa vadeli) [^73^] | ⭐⭐⭐⭐☆ (Uzun vadeli bellek eklentisi; konuşma geçmişi) [^77^] | ⭐⭐⭐⭐⭐ (Kendini iyileştiren temporal bellek; 4 katmanlı compaction) [^94^] |
| **Sesli Etkileşim Kalitesi** | ⭐⭐⭐☆☆ (Metin odaklı; sesli özellikler sınırlı) | ⭐⭐☆☆☆ (Metin odaklı; çok modlu destek geliştirme aşamasında) [^31^] | ⭐⭐⭐⭐⭐ (Piper TTS doğal ses; Whisper STT; Voice Preview Edition donanımı) [^29^] | ⭐⭐⭐⭐☆ (Piper, XTTS, Edge-TTS ile yüksek kalite; plugin seçenekleri geniş) [^145^] | ⭐⭐⭐⭐☆ (ChatTTS sesli diyalog; pratik sesli etkileşim) [^100^] | ⭐⭐⭐☆☆ (Ses modu var ama mesajlaşma odaklı) | ⭐⭐⭐⭐☆ (Çoklu TTS: Azure, ElevenLabs, OpenAI; Whisper STT) [^73^] | ⭐⭐⭐⭐☆ (TTS/STT çoklu sağlayıcı; gerçek zamanlı ses modu) [^77^] | ⭐⭐⭐☆☆ (Ses modu var; metin odaklı) |
| **Aktif Geliştirme / Topluluk** | ⭐⭐⭐⭐☆ (Stanford araştırma projesi; 2026 Mart yeni; aktif) [^124^] | ⭐⭐⭐⭐⭐ (LocalAI ekosistemi; düzenli güncellemeler; 770+ stars) [^31^][^40^] | ⭐⭐⭐⭐⭐ (En büyük DIY smart home topluluğu; sürekli güncelleme) [^129^] | ⭐⭐⭐⭐☆ (Vakıf yönetimi; NGI hibesi; aktif plugin geliştirme) [^99^][^130^] | ⭐⭐⭐⭐☆ (MyShell.ai desteği; MCP güncellemesi Mart 2025) [^100^] | ⭐⭐⭐⭐⭐ (En hızlı büyüyen repo; 600+ contributor; 15K Discord) [^89^] | ⭐⭐⭐⭐☆ (Aktif; MIT lisanslı; SourceForge/PyPI mevcut) [^82^] | ⭐⭐⭐⭐☆ (Aktif; multi-platform) [^77^] | ⭐⭐⭐☆☆ (Ağır geliştirme aşamasında; ilk resmi sürüm bekleniyor) [^94^] |

---

### Trends & Signals

1. **Yerel-first (Local-first) paradigma hakim oluyor**: 2025 "Yerel Büyük Modeller Yılı" olarak adlandırıldı ve 2026 itibarıyla kullanıcılar yalnızca sohbet etmek değil, "gerçekten iş yapan" ajanlar istiyor [^37^]. OpenJarvis, LocalAGI ve Home Assistant'ın yerel LLM entegrasyonları bu trendin öncüleri.
2. **MCP (Model Context Protocol) standartlaşıyor**: OpenJarvis, AIlice, PyGPT, Witsy ve LocalAGI'nın (Ekim 2024 [^40^]) MCP desteği sunması, ajanların harici araçlarla iletişiminde ortak bir protokolün belirdiğini gösteriyor.
3. **Sesli etkileşimde "açık uçlu" vs "sınırlı komut" ayrışması**: Home Assistant Speech-to-Phrase, Raspberry Pi'de <1 saniyede çalışan ama sınırlı komut setine sahip; Whisper ise açık uçlu ama GPU gerektirir [^29^][^144^]. Bu ikili yaklaşım, donanım kısıtlarına göre sesli asistan tasarımının evrimini gösteriyor.
4. **Masaüstü AI asistanları çok sağlayıcılı hale geliyor**: PyGPT ve Witsy, tek bir sağlayıcıya bağlı kalmadan 10+ LLM sağlayıcısını destekleyen BYOK (Bring Your Own Key) modeline geçiyor.
5. **Otonom ajan güvenliği tartışma konusu**: OpenClaw'ın kabuk erişimi talebi ve yanlış yapılandırılmış örneklerde kimlik bilgisi sızıntıları, "yapabilen" ajanların güvenlik risklerini gündeme getirmiştir [^93^][^89^].
6. **Türkçe desteği genişliyor ama hâlâ model-bağımlı**: Home Assistant Speech-to-Phrase ve OVOS XTTS Türkçe'yi resmen desteklerken, çoğu framework'un Türkçe yeteneği kullanılan temel modelin (Whisper, LLM) Türkçe performansına bağlıdır.
7. **Mycroft'ın çöküşü ve topluluk kurtuluşu**: Şirket tabanlı açık kaynak projelerin hukuki/finansal risklere karşı savunmasız olduğunu; ancak topluluk çatallamasıyla (OVOS) projelerin hayatta kalabileceğini gösteren bir vaka çalışmasıdır [^99^].

---

### Controversies & Conflicting Claims

1. **OpenClaw GitHub Star Sayısı**: Bazı kaynaklar 355K [^85^], bazıları 233K [^89^], bazıları 250K+ [^86^] star rakamı vermektedir. Bu farklı zaman dilimlerindeki sayılar olabilir ancak tüm kaynaklar olağanüstü büyüme hızı konusunda hemfikirdir.
2. **OpenClaw Güvenliği**: Bir taraftan "tamamen yerel, verileriniz kontrolünüzde" [^89^] vaadi var; diğer taraftan "açık örneklerde kimlik bilgileri sızdırma" ve "kurmamanız gereken en sıcak AI aracı" iddiası [^93^] gibi güvenlik uyarıları bulunmaktadır.
3. **Mycroft vs OpenVoiceOS vs Neon AI**: Üç proje de Mycroft kod tabanından çatallanmıştır ve birbiriyle uyumlu olmaya çalışır; ancak hangisinin "asıl devamı" olduğu konusunda topluluk içinde farklı görüşler vardır [^86^]. Neon AI, OVOS üzerine ek özellikler kurarken; OVOS "Mycroft Topluluk Sürümü" olarak konumlanır [^86^].
4. **Home Assistant'ın AI "deneyimselliği"**: Home Assistant'ın yerel LLM entegrasyonu "deneysel" olarak işaretlenmiştir [^125^]; bu, üretim ortamında kritik görevler için hâlâ olgunlaşmadığını gösterir. Ayrıca LLM'lerin cihaz kontrolünde yanlış anlamalar yapabileceği belirtilmiştir [^125^].
5. **AIlice'nin "JARVIS benzeri" iddiası**: AIlice ve OpenJarvis her ikisi de JARVIS benzerliği iddia eder; ancak AIlice daha çok otonom görev yürütme ve kodlamaya odaklanırken, OpenJarvis kişisel cihazlarda verimli çıkarım ve öğrenme döngüsüne odaklanır.

---

### Recommended Deep-Dive Areas

1. **OpenJarvis Learning Prensiplinin Pratik Uygulanabilirliği**: DSPy ve GEPA optimizasyonlarının gerçek kullanıcı senaryolarında ne kadar etkili olduğu, eğitim verisi üretiminin gizlilik etkileri ve kapalı döngü fine-tuning'in donanım gereksinimleri derinlemesine incelenmelidir.
2. **Home Assistant + Ollama + Whisper + Piper Tam Yerel Pipeline'ının Türkçe Performansı**: Speech-to-Phrase'ın Türkçe desteği yeni [^137^] ve Whisper'ın Türkçe modelinin Raspberry Pi üzerindeki performansı pratik testlerle doğrulanmalıdır.
3. **OpenVoiceOS Plugin Ekosisteminin Bakımı**: OVOS'un çok sayıda eklenti (STT/TTS/skill) sunması avantajdır, ancak bu eklentilerin ne kadarının aktif sürdürüldüğü ve Türkçe'ye özel plugin'lerin mevcudiyeti araştırılmalıdır.
4. **LocalAGI'nin Go Mimarisi ve Ölçeklenebilirliği**: Go tabanlı custom actions (interpreted, derleme gerekmez) özelliğinin güvenlik ve performans etkileri; ajan ekiplerinin koordinasyon mekanizmaları detaylı incelenmelidir.
5. **AIlice IACT Mimarisinin Karmaşık Görev Başarımı**: AIlice'in "literatür taraması" ve "sistem yönetimi" iddialarının belirli karmaşıklık seviyelerindeki gerçek başarım oranı; ajan ağacının döngüsel çağrılarından kaynaklanan hata birikimi potansiyeli değerlendirilmelidir.
6. **TinyClaw'ın OpenClaw'a Karşı Hafiflik ve Güvenlik Vaadi**: "SHIELD.md anti-malware enforcement" vaadinin teknik detayları ve "kendi kişiliği var (değiştirilemez)" yaklaşımının kullanıcı kabulü derinlemesine incelenmelidir.
7. **Türkçe TTS/STT Kalitesi Karşılaştırması**: OVOS XTTS-v2, MMS-TTS, Home Assistant Piper ve VOSK Türkçe modellerinin nesnel kalite karşılaştırması (MOS skoru vb.) yapılmalıdır.

---

### Major Players & Sources

| Kaynak | Rol / Önem |
|---|---|
| [^31^] mudler/LocalAGI GitHub | LocalAGI'nin resmi repo; Go mimarisi, Docker kurulumu, özellik listesi |
| [^133^] scalingintelligence.stanford.edu | Stanford OpenJarvis teknik blogu; 5 prensip mimarisi |
| [^96^] scalingintelligence.stanford.edu/blogs/openjarvis | OpenJarvis'e katkıda bulunma ve kurulum rehberi |
| [^98^] open-jarvis.github.io/OpenJarvis | OpenJarvis resmi dokümantasyon; Ollama/vLLM/llama.cpp kurulumu |
| [^32^] home-assistant.io/integrations/wyoming | Wyoming Protokolü resmi dokümanı |
| [^29^] joekarlsson.com | Pratik Home Assistant yerel sesli asistan kurulum rehberi (GPU, Proxmox) |
| [^125^] home-assistant.io/integrations/ollama | Home Assistant Ollama entegrasyonu resmi dokümanı |
| [^137^] github.com/OHF-voice/speech-to-phrase | Speech-to-Phrase repo; 21 dil desteği (Türkçe dahil) |
| [^99^] grokipedia.com/Mycroft_(software) | Mycroft tarihçesi ve topluluk geçişi (OVOS, Neon AI) |
| [^97^] openvoiceos.org | OpenVoiceOS resmi web sitesi; kurulum ve indirme |
| [^100^] github.com/myshell-ai/AIlice | AIlice resmi repo; IACT mimarisi, yol haritası |
| [^138^] github.com/OpenVoiceOS/ovos-tts-plugin-coqui | OVOS Coqui TTS plugin; XTTS-v2 Türkçe desteği |
| [^145^] blog.graywind.org/posts/tts-options-ovos/ | OVOS TTS plugin karşılaştırması (Mike Gray) |
| [^89^] buildmvpfast.com/openclaw-guide-2026 | OpenClaw kurulum ve güvenlik rehberi |
| [^85^] medium.com/data-science-collective | OpenClaw 2026 tam kılavuz; mimari ve güvenlik |
| [^73^] github.com/szczyglis-dev/py-gpt | PyGPT resmi GitHub repo |
| [^77^] github.com/Kochava-Studios/witsy | Witsy resmi GitHub repo |
| [^94^] github.com/warengonzaga/tinyclaw | TinyClaw resmi repo; mimari karşılaştırması |
| [^80^] medium.com/@sirvanksc | Yerel Türkçe sesli AI asistanı nasıl kurulur (Vosk + llama.cpp) |
| [^83^] github.com/Rumeysakeskin/free-turkish-tts-models | Türkçe TTS modelleri karşılaştırması (XTTS v2, MMS-TTS) |

---

*Araştırma tarihi: Haziran 2026*  
*Toplam bağımsız arama sayısı: 14*  
*Kapsanan platformlar: OpenJarvis, LocalAGI, Home Assistant + Assist, OpenVoiceOS, Mycroft, AIlice, OpenClaw, PyGPT, Witsy, TinyClaw*
