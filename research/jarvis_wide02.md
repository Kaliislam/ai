## Facet: Sesli Etkileşim Pipeline'ları

### Key Findings

- **Whisper ekosistemi STT standardıdır**, ancak Türkçe için "Tier 2" dil kategorisinde yer alır; temel Whisper-large-v3 WER'i %9-13 arasındadır. LoRA ile fine-tuning, Türkçe WER'i %52'ye varan oranlarda düşürebilir [^59^][^69^].
- **Nvidia Canary** İngilizce'de Whisper'dan daha düşük WER (%5.63) sunar ancak yalnızca İngilizce, Fransızca, Almanca ve İspanyolca destekler - **Türkçe desteği yoktur** [^76^][^78^][^80^].
- **faster-whisper**, CTranslate2 tabanlı implementasyonuyla OpenAI Whisper'dan **4-8x daha hızlı** çalışır, CPU ve GPU'da çalışır, streaming desteği sunar ve VAD ön-filtresi içerir [^63^][^104^].
- **whisper.cpp** kenar cihazlar için optimize edilmiş C++ portudur; batch modda hızlı ancak **streaming modda Android CPU'da gerçek zamanlıdan ~5x daha yavaş** kalır [^73^][^74^].
- **Kokoro-82M** en yüksek MOS skoru (4.2) ve en düşük gecikme (RTF 0.03, <1GB VRAM) ile öne çıkar, ancak Türkçe desteği resmi olarak listelenmemiştir; ses klonlama yeteneği yoktur [^43^][^44^][^62^].
- **Piper TTS** en hızlı CPU performansına sahiptir (RTF 0.008, <100MB), 30+ dil destekler, Raspberry Pi'da çalışır, **Türkçe ses modelleri mevcuttur** ancak uzun ünlü telaffuzunda sorunlar bildirilmiştir [^42^][^43^][^130^][^134^].
- **XTTS-v2** 17 dil arasında **Türkçe'yi de destekler**, 6 saniyelik referansla ses klonlama yapar, ancak ~4GB VRAM gerektirir ve CPML (ticari olmayan) lisanslidir [^43^][^83^][^101^].
- **FishSpeech** Apache 2.0 lisanslı, ses klonlamalı, çok dilli TTS'tir; MOS 4.1 ve ~4GB VRAM gerektirir [^43^][^107^][^109^].
- **Porcupine (Picovoice)** ticari bir çözümdür ancak ücretsiz kişisel kullanım sunar; saniyeler içinde özel wakeword eğitimi yapılabilir ve "Jarvis" dahil hazır modeller içerir [^66^][^81^].
- **openWakeWord** aktif olarak geliştirilen, Apache 2.0 lisanslı, açık kaynak alternatiftir; Porcupine ile rekabetçi doğruluk sunar, 20+ dil destekler, Raspberry Pi'da çalışır ve 1 saatten kısa sürede özel wakeword eğitimi sağlar [^75^][^136^].
- **Snowboy artık bakımsızdır (deprecated)** ve alternatif olarak openWakeWord veya Porcupine önerilir [^66^][^132^].
- **Silero VAD** endüstri standardıdır: ~2MB model, <1ms gecikme, 30ms chunk işleme, 99%+ doğruluk; LiveKit ve Pipecat'e yerleşik olarak entegredir [^49^][^52^].
- **Cobra VAD** (Picovoice) Silero'dan 12x daha az hata yapar ancak ticari bir üründür; WebRTC VAD en düşük doğruluğa sahiptir [^52^].
- **TEN VAD** yalnızca 306KB kütüphane boyutuyla, RTF 0.015 ve çoklu platform desteğiyle ultra hafif bir alternatiftir [^51^].
- **Streaming pipeline mimarisi** (VAD → STT → LLM → TTS) aşamaları örtüşerek sonuçlandırır; end-to-end gecikme <1 saniyeye indirilebilir; sequential pipeline ise 2-4 saniye gecikme yaratır [^160^][^164^].
- **Barge-in (konuşma üzerine konuşma)** desteği, kullanıcı TTS sırasında konuşmaya başladığında TTS'i anında durdurup LLM üretimini iptal ederek pipeline'ı STT'den yeniden başlatmayı gerektirir [^45^][^57^][^58^][^70^].
- **Semantic VAD / turn detection**, enerji tabanlı VAD'in aksine anlamsal tamamlanma, prosodi ve konuşma bağlamını analiz ederek daha doğal turn-taking sağlar [^153^][^155^][^157^].
- **Home Assistant Wyoming protokolü**, tamamen yerel sesli asistan bileşenlerini (VAD + wakeword + STT + LLM + TTS) standart bir TCP protokolü üzerinden birleştirmek için kullanılan açık standarttır [^72^].
- **OpenAI Realtime API** sub-300ms gecikme sunar ancak bulut bağımlıdır ve model lock-in yaratır; yerel pipeline'lar 450-750ms aralığındadır [^123^][^124^][^162^].
- **WhisperX**, faster-whisper üzerine kurulu olup kelime düzeyinde zaman damgaları (±50ms) ve konuşmacı diarizasyonu ekler; GPU'da 70x gerçek zamanlı hıza ulaşır [^104^][^110^].
- **Orpheus, Dia, Chatterbox** 2025'in yeni nesil TTS modelleri arasındadır; Dia çok konuşmacılı diyalog, Orpheus 150M-3B ölçeklenebilir mimari, Chatterbox Llama tabanlı hızlı çıkarım sunar [^43^][^102^].
- **MeloTTS** 6x gerçek zamanlı CPU performansı sunar ancak resmi destek listesinde Türkçe yoktur (EN, ES, FR, ZH, JA, KO) [^42^][^131^].

### Major Players & Sources

- **OpenAI Whisper / faster-whisper / whisper.cpp**: STT ekosisteminin belkemiği. faster-whisper CTranslate2 ile üretim çıkarımı optimize eder; whisper.cpp kenar/ mobil cihazlar için C++ portudur [^63^][^73^][^104^].
- **Nvidia Canary / Parakeet-TDT**: Nvidia'nın NeMo tabanlı ASR modelleri. Canary 1B İngilizce'de en düşük WER'i tutturur ancak dil desteği sınırlıdır. Parakeet-TDT 1.1B streaming için >2000x RTF sunar [^76^][^82^].
- **Kokoro-82M (Hexgrad)**: 82M parametre ile en yüksek MOS skorunu elde eden hafif TTS. StyleTTS2 mimarisi, 24kHz, Apache 2.0 lisanslı [^43^][^44^].
- **Piper TTS (Rhasspy)**: ONNX/VITS tabanlı, Raspberry Pi 4'te gerçek zamanlı çalışan, MIT lisanslı, en hızlı CPU TTS [^42^][^130^].
- **XTTS-v2 (Coqui)**: 17 dil destekli, zero-shot ses klonlama, CPML lisanslı. Coqui şirketi kapanmış ancak topluluk bakımı devam etmektedir [^43^][^83^][^106^].
- **FishSpeech / Fish Audio**: Apache 2.0 lisanslı, çok dilli, duygu/ton kontrolü, zero-shot ses klonlama [^107^][^109^].
- **Porcupine (Picovoice)**: Ticari wakeword motoru, anında özel wakeword eğitimi, çapraz platform [^66^][^81^].
- **openWakeWord (dscripka)**: Apache 2.0 lisanslı açık kaynak wakeword framework'ü, Home Assistant entegrasyonu, 20+ dil [^75^][^136^].
- **Silero VAD**: snakers4 tarafından geliştirilen, PyTorch/ONNX tabanlı, endüstri standardı açık kaynak VAD [^49^][^52^].
- **LiveKit Agents**: WebRTC-first sesli ajan framework'ü, VAD, STT, LLM, TTS pipeline'ini event-driven model ile yönetir [^58^][^155^].
- **Pipecat**: Frame tabanlı Python framework, explicit pipeline kontrolü, interruption handling, Smart Turn detection [^55^][^57^][^70^].
- **WhisperX (m-bain)**: faster-whisper + pyannote + forced alignment ile transkripsiyon + diarizasyon + kelime düzeyi zaman damgası [^104^][^110^].
- **Home Assistant / Wyoming Protocol**: Tamamen yerel sesli asistan için açık standart ve entegrasyon ekosistemi [^72^].

### Trends & Signals

- **TTS'te küçülme trendi**: Kokoro-82M (82M parametre) gibi modeller, XTTS-v2 (467M) ve Bark (900M) gibi daha büyük modellere kalite ve hızda üstünlük kurmaktadır. "Daha küçük, daha hızlı, daha iyi" trendi belirgindir [^42^].
- **Streaming-first mimariler baskınlaşıyor**: 2025-2026 itibarıyla üretim sesli ajanlar, sequential pipeline yerine her aşama sınırında streaming inference kullanmaktadır [^160^][^164^].
- **Semantic / AI tabanlı turn detection**: Enerji tabanlı VAD'dan, transformer tabanlı semantic turn detection'a (LiveKit EOU, Pipecat Smart Turn, Deepgram Flux) geçiş yaşanmaktadır [^153^][^155^][^157^].
- **End-to-end speech-to-speech modelleri**: OpenAI Realtime API, Gemini Live gibi tek-model çözümler, pipeline handoff gecikmelerini ortadan kaldırarak 200-300ms aralığına inmektedir [^123^][^162^].
- **Yerel/edge deployment mümkün hale geldi**: Piper, Kokoro, Silero VAD, whisper.cpp ve openWakeWord ile Raspberry Pi 4 üzerinde tamamen yerel, çevrimdışı sesli asistan kurulumları pratik hale gelmiştir [^42^][^52^][^72^].
- **Çok dilli ses klonlama**: XTTS-v2 ve FishSpeech, 6-10 saniyelik referans sesle herhangi bir dilden herhangi bir dile ses transferi (cross-lingual cloning) sunmaktadır [^83^][^107^].
- **Whisper alternatifleri çoğalıyor**: Voxtral, Canary, Parakeet-TDT, Moonshine gibi modeller, Whisper'ın İngilizce dışı dillerdeki zayıflıklarını gidermeye odaklanmaktadır [^56^][^76^].
- **2025 TTS Arena**: Topluluk odaklı ELO puanlama sistemi ile açık kaynak TTS modelleri ticari çözümlerle rekabet etmektedir; Kokoro-82M liderlik etmektedir [^55^].

### Controversies & Conflicting Claims

- **Whisper Türkçe doğruluğu**: Eğitim verisi hacmine bağlı olarak Türkçe WER %9-13 arasındadır ve bu "kullanılabilir ancak düzenleme gerektirir" kategorisindedir [^59^]. Ancak fine-tuning ile bu değer %5-10'a düşürülebilir [^69^]. Kullanılabilirlik tartışmalıdır - bazı uygulamalar için yeterli, profesyonel transkripsiyon için yetersiz.
- **Whisper streaming performansı**: Whisper temel olarak gerçek zamanlı tasarımlanmamıştır. whisper.cpp streaming modda mobil CPU'da 5-7 saniyede 1 saniyelik ses işlemektedir [^73^]. Ancak faster-whisper + VAD chunking ile üretim ortamlarında streaming mümkündür [^60^]. whisper.cpp batch modda aynı cihazda hızlıdır - streaming yavaşlığı implementasyon/architecture kaynaklıdır.
- **openWakeWord vs Porcupine doğruluğu**: openWakeWord geliştiricisi, kendi test verisi için Porcupine'dan daha doğru olduğunu iddia etmektedir; ancak "örneklem küçük olduğu için sonuçlar dikkatle yorumlanmalıdır" notunu düşmüştür [^136^]. Picovoice ise ticari ürünü Cobra VAD'in Silero'dan 12x daha az hata yaptığını iddia etmektedir [^52^].
- **XTTS-v2 lisansı**: CPML (Coqui Public Model License) ticari kullanımı yasaklar. FishSpeech ve Kokoro Apache 2.0 lisanslıdır ve ticari kullanıma uygundur [^43^]. Birçok geliştirici CPML kısıtlamasından dolayı XTTS yerine FishSpeech'e yönelmektedir.
- **End-to-end vs pipeline mimarisi**: OpenAI Realtime API gibi end-to-end modeller daha düşük gecikme sunar ancak "transkripsiyon doğruluğu Deepgram gibi rakiplerden daha düşük olabilir" ve model lock-in yaratır [^123^]. Pipeline mimarisi modülerlik ve kontrol sunar ancak 450-750ms gecikme yaşar [^162^].
- **VAD seçimi**: Silero VAD ücretsiz ve yaygın olmasına rağmen, Cobra VAD ve TEN VAD gibi alternatifler önemli doğruluk/performans avantajları sunar; ancak bunlar ya ticaridir (Cobra) ya da daha az yaygındır (TEN) [^51^][^52^].

### Recommended Deep-Dive Areas

- **Whisper Türkçe fine-tuning ve LoRA adaptasyonu**: Whisper-large-v3'ün Türkçe METU, FLEURS, Mozilla CV veri kümeleri üzerinde LoRA ile fine-tuning sonuçları %52'ye varan WER iyileştirmesi göstermiştir [^69^]. Bu, yerel bir Türkçe sesli asistan için kritik bir optimizasyondur. Detaylı eğitim pipeline'ı ve çıkarım optimizasyonu incelenmelidir.
- **Piper TTS Türkçe ses modelleri ve telaffuz düzeltmeleri**: HuggingFace'de rhasspy/piper-voices altında Türkçe modeller mevcuttur ancak topluluk tartışmalarında "uzun ünlü telaffuzu" sorunları bildirilmektedir [^134^]. Türkçe ses kalitesini artırmak için özel eğitim veya ses düzeltme teknikleri araştırılmalıdır.
- **Tamamen yerel pipeline entegrasyonu (Wyoming/Home Assistant pattern)**: Joe Karlsson'ın Home Assistant + faster-whisper GPU + Piper + Ollama kurulumu [^72^], Wyoming protokolü üzerinden bileşenlerin ayrı ayrı container'landırılması ve pipeline fallback zinciri oluşturulması açısından zengin bir referanstır.
- **Barge-in ve echo cancellation implementasyonu**: Pipecat'in "Interruptible Frames" [^57^][^70^] ve LiveKit'in VAD tabanlı interruption event'leri [^58^] detaylı şekilde incelenmelidir. Agent'ın kendi sesinin mikrofona yansıması (echo) ile oluşan yanlış interruption'ları engellemek için AEC (Acoustic Echo Cancellation) stratejileri derinlemesine araştırılmalıdır.
- **Semantic turn detection'un yerel implementasyonu**: LiveKit EOU modeli ve Pipecat Smart Turn [^163^] açık ağırlıklı modellerdir. Tamamen yerel bir pipeline'da acoustic VAD + LLM tabanlı turn completeness kontrolü kombinasyonu incelenmelidir.
- **Kokoro-82M'e Türkçe desteği ekleme yolları**: Kokoro şu anda resmi olarak EN, FR, KO, JA, ZH desteklemektedir [^62^]. Yeni bir voicepack eğitimi veya es_phoneme kullanımı gibi yöntemlerle Türkçe desteğinin eklenip eklenemeyeceği araştırılmalıdır.
- **faster-whisper + VAD chunking ile streaming STT optimizasyonu**: Baseten'in VAD tabanlı chunking + paralel transkripsiyon yaklaşımı [^60^] ve Whisper-Streaming'in LocalAgreement algoritması [^71^][^128^] yerel pipeline'da uygulanabilir.

---

## Ayrıntılı Derinlemesine Analiz

### 1. Speech-to-Text (STT) Seçenekleri

#### 1.1 Whisper Ekosistemi

OpenAI Whisper, 99+ dil desteğiyle açık kaynak STT'in de facto standardıdır. Ancak temel implementasyonu yavaştır ve gerçek zamanlı streaming için optimize edilmemiştir.

**Model Boyutları ve Türkçe Doğruluk:**
Bir akademik çalışma, Whisper modellerinin Türkçe veri kümeleri üzerindeki performansını kapsamlı şekilde değerlendirmiştir [^69^]:

| Model | METU MS WER | TNST WER | FLEURS WER | Mozilla CV WER |
|-------|-------------|----------|------------|----------------|
| tiny | 0.36 | 0.53 | - | - |
| base | - | - | - | - |
| small | - | - | - | - |
| medium | - | - | - | - |
| large-v2 | 0.10 | 0.13 | 0.08 | 0.16 |
| large-v3 | **0.04-0.10** | İyileşme | İyileşme | İyileşme |

Whisper-large-v3, large-v2'ye göre %8.77 - %29.08 arası WER iyileştirmesi sunar [^69^]. Fine-tuning (LoRA) ile FLEURS veri kümesinde %43.37, Mozilla CV'da %49.00 WER düşüşü elde edilmiştir [^69^]. Novascribe verilerine göre Türkçe temel WER %9-13 arasındadır ve agglutinasyon nedeniyle "Tier 2" kategorisindedir [^59^].

**faster-whisper:**
CTranslate2 inference engine üzerine kuruludur ve OpenAI Whisper'dan 4-8x daha hızlı çalışır [^104^]. CPU ve GPU'da çalışır, quantizasyon (INT8) destekler, batch ve streaming transkripsiyon yeteneğine sahiptir [^63^]. AMD GPU + ROCm desteği de mevcuttur [^104^].

**whisper.cpp:**
C++ portu olup kenar cihazlar için optimize edilmiştir. Apple Silicon ve modern GPU'larda %95+ doğruluk sağlar [^56^]. Ancak **streaming modda kritik bir performans sorunu** vardır: Android ARM64 CPU'da 1 saniyelik sesi işlemek 5-7 saniye sürmektedir; batch modda aynı cihazda 5 saniyelik ses 1-2 saniyede işlenmektedir [^73^][^74^]. Bu, tekrarlanan `whisper_full` çağrılarındaki overhead kaynaklıdır.

**WhisperX:**
faster-whisper üzerine kelime düzeyinde zaman damgaları (±50ms, whisper'ın ±500ms'ine karşı) ve konuşmacı diarizasyonu (pyannote.audio 3.1) ekler [^110^]. GPU'da 70x gerçek zamanlı hıza ulaşır. Ancak diarizasyon ile birlikte faster-whisper'dan %40-60 daha yavaştır [^104^].

**Whisper-Streaming:**
Whisper'ı gerçek zamanlı streaming için uyarlayan akademik bir implementasyondur. LocalAgreement algoritması ile İngilizce'de ortalama 3.3 saniye, Almanca'da 4.4 saniye, Çekçe'de 4.8 saniye gecikme sunar [^71^][^128^]. 2025 itibarıyla SimulStreaming tarafından güncellenmektedir [^128^].

#### 1.2 Whisper Alternatifleri

**Nvidia Canary:**
FastConformer encoder + transformer decoder mimarisi. İngilizce'de %5.63 WER ile Open ASR Leaderboard'unda liderdir [^76^][^82^]. Ancak yalnızca İngilizce, Fransızca, Almanca ve İspanyolca destekler [^80^]. **Türkçe desteği yoktur**.

**Nvidia Parakeet-TDT 1.1B:**
RNN-Transducer mimarisi, >2000x RTF ile ultra hızlı streaming ASR [^76^][^82^]. Ancak yalnızca İngilizce'dir ve doğruluk açısından Whisper'ın gerisindedir.

**Distil-Whisper:**
Whisper Large V3'ün bilgi damıtmasıyla oluşturulmuş 756M parametreli versiyonu. 6x daha hızlıdır ancak yalnızca İngilizce'dir [^76^].

**Voxtral:**
Mistral tarafından geliştirilen, 13 dilde Whisper'ı geçen model. Ancak Türkçe, Tayca, Vietnamca, Lehçe, Çekçe gibi dilleri kapsamaz [^56^].

### 2. Text-to-Speech (TTS) Seçenekleri

#### 2.1 Karşılaştırmalı Performans ve Özellikler

| Model | MOS | RTF | VRAM | Parametre | Ses Klonlama | Lisans | Türkçe |
|-------|-----|-----|------|-----------|--------------|--------|--------|
| Kokoro-82M | 4.2 | 0.03 | <1 GB | 82M | Hayır (stil preset) | Apache 2.0 | ❌ Resmi değil |
| Fish Speech | 4.1 | 0.12 | ~4 GB | 500M | Evet (10-30s referans) | Apache 2.0 | Çok dilli |
| XTTS v2 | 4.0 | 0.18 | ~4 GB | 467M | Evet (6s referans) | CPML (non-commercial) | ✅ Evet |
| Dia | 4.0 | 0.15 | ~5 GB | 1.6B | Evet (audio prompt) | Apache 2.0 | Çok dilli |
| F5-TTS | 4.1 | 0.14 | ~4 GB | 336M | Evet (5-15s referans) | CC-BY-NC 4.0 | Çok dilli |
| Piper (Medium) | 3.5 | 0.008 | <100 MB (CPU) | 6-60M | Hayır (önceden eğitilmiş) | MIT | ✅ Evet |
| MeloTTS | ~3.8 | 0.16 | CPU | 162M | Gelecekte | MIT | ❌ Hayır |
| Parler-TTS Mini | 3.8 | 0.22 | ~4 GB | 880M | Hayır (metin tanımlı) | Apache 2.0 | - |
| Bark | 3.7 | 0.85 | ~6 GB | 900M | Sınırlı | MIT | - |

[^43^][^42^]

#### 2.2 Türkçe Destek Analizi

**XTTS-v2**, resmi olarak 17 dil arasında Türkçe'yi (tr) destekler [^83^]. Coqui TTS dokümantasyonunda Türkçe ses klonlama örnekleri mevcuttur [^106^].

**Piper TTS**, HuggingFace rhasspy/piper-voices deposunda Türkçe ses modelleri içerir [^134^]. Ancak topluluk tartışmalarında "uzun ünlü telaffuzu" (long vowels pronunciation) sorunları bildirilmiştir [^134^].

**MeloTTS** resmi GitHub sayfasında desteklenen diller arasında Türkçe yer almaz: English, Spanish, French, Chinese, Japanese, Korean [^131^].

**Kokoro-82M** resmi web sitesinde "currently optimized for English" ifadesini kullanır ve Türkçe'yi listelemez [^62^].

**FishSpeech** çok dilli ve cross-lingual olarak tanımlanır ancak spesifik Türkçe desteği dokümantasyonda belirtilmemiştir [^107^][^109^].

#### 2.3 Latency Karşılaştırması

| Model | Ortalama Sentez Süresi (CPU) | RTF | Gerçek Zamanlı? |
|-------|------------------------------|-----|-----------------|
| Piper Low (5.8MB) | 0.008s | 1409x | ✅ Evet, aşırı hızlı |
| Piper Medium (62MB) | 0.014s | 2483x | ✅ Evet |
| Piper High (110MB) | 0.043s | 7603x | ✅ Evet |
| MeloTTS | 0.65s (4.28s ses için) | 0.16x | ✅ Evet (6x) |
| Kokoro-82M | 0.82s (3.85s ses için) | 0.21x | ✅ Evet (5x) |
| Parler-TTS Mini | - | 6.94x | ❌ Hayır |
| XTTS-v2 | - | N/A | ❌ GPU zorunlu |

[^42^]

### 3. Wakeword / Hotword Detection

#### 3.1 Seçenekler Karşılaştırması

| Motor | Lisans | Özel Wakeword | Hız | Bakım Durumu | Türkçe |
|-------|--------|---------------|-----|--------------|--------|
| Porcupine (Picovoice) | Ücretsiz kişisel / Ticari ücretli | Saniyeler içinde | Çok hızlı | Aktif | Evet |
| openWakeWord | Apache 2.0 | <1 saat eğitim | Hızlı | Aktif | 20+ dil |
| Snowboy | Apache 2.0 | Hayır / Sınırlı | Orta | **Bakımsız** | - |
| PocketSphinx | BSD | Hayır | Yavaş | Eski | - |

[^66^][^75^][^136^]

**Porcupine**, Python SDK'sı `pvporcupine` ile pip üzerinden kurulabilir. Hazır modeller arasında "jarvis", "alexa", "hey google", "ok google", "hey siri" bulunur [^81^]. Özel wakeword oluşturmak için Picovoice Console'a giriş yapılıp istenen ifade yazılarak "Train" düğmesine basılması yeterlidir; model saniyeler içinde oluşturulur [^66^].

**openWakeWord** ise tamamen açık kaynak ve gizlilik odaklıdır. ONNX formatında <100KB modeller üretir, Raspberry Pi'da gerçek zamanlı çalışır. Web arayüzünde "Hey Nova", "OK Jarvis" gibi ifadeler yazılıp sentetik seslerle test edilebilir [^75^]. Python entegrasyonu Home Assistant, Rhasspy ve OpenVoiceOS ile mevcuttur [^75^][^136^].

**Snowboy**, Picovoice'un resmi karşılaştırma blogunda "no longer maintained" olarak işaretlenmiştir [^66^]. Alternativeto.net'te en iyi Snowboy alternatifi olarak Jasper, OpenJarvis ve Sonus listelenmektedir [^132^].

### 4. Voice Activity Detection (VAD)

#### 4.1 VAD Motorları Karşılaştırması

| Motor | TPR @ 5% FPR | TPR @ 1% FPR | RTF (CPU) | Boyut | Maliyet |
|-------|--------------|--------------|-----------|-------|---------|
| Cobra VAD | 98.9% | 95% | 0.000399 | Minimal | Ticari |
| Silero VAD | 87.7% | 80.4% | 0.00429 | ~2MB | Ücretsiz |
| WebRTC VAD | 50% | Çok düşük | Minimal | Minimal | Ücretsiz |
| TEN VAD | Superior | - | 0.015 | 306KB | Ücretsiz |

[^52^][^51^]

**Silero VAD** endüstri standardıdır: 30ms ses chunk'larını <1ms gecikme ile işler, 99%+ doğruluk sunar, PyTorch veya ONNX Runtime ile çalışır [^49^]. LiveKit Agents ve Pipecat framework'leri varsayılan olarak Silero VAD kullanır [^49^].

**Cobra VAD** (Picovoice), Silero'dan 12x, WebRTC'den 50x daha az hata yapar. Raspberry Pi Zero'da %5 CPU kullanırken, Silero %43 CPU kullanır [^52^]. Ancak ticari bir üründür.

**TEN VAD** (TEN Framework), 306KB kütüphane boyutuyla ultra hafif bir alternatiftir. ONNX formatında, WebAssembly desteği ile tarayıcı entegrasyonu sunar [^51^].

**WebRTC VAD**, saf C implementasyonudur, runtime bağımlılığı yoktur, ancak doğruluk olarak en düşük performansı gösterir [^52^].

### 5. Tam Pipeline Mimarisi

#### 5.1 Pipeline Akışı

Standart sesli etkileşim pipeline'ı şu aşamalardan oluşur [^61^][^70^]:

```
Mikrofon (Audio Frame)
    → VAD (Ses/Sessiz tespiti)
    → Wakeword Detection (Özel kelime bekleniyor)
    → STT (Streaming Transcription)
    → LLM (Token Streaming)
    → TTS (Streaming Synthesis)
    → Hoparlör (Audio Playback)
```

#### 5.2 Streaming ve Chunking Stratejileri

**Sequential Pipeline:**
Kullanıcı konuşmayı bitirdikten sonra STT tam transkripsiyon üretir, ardından LLM tam yanıtı oluşturur, son olarak TTS tam sesi sentezler. Bu mimari **2-4 saniye gecikme** yaratır ve konuşma hissi vermez [^160^].

**Streaming Pipeline:**
STT kısmi transkripsiyonları LLM'e anında aksettirir. LLM, ilk token'ları alır almaz TTS'e göndermeye başlar. TTS ise ilk cümle hazır olur olmaz ses çıkışına başlar. Bu şekilde **end-to-end gecikme <1 saniyeye** indirilebilir [^160^][^164^].

**Streaming Latency Bütçesi (Hedefler):**
| Aşama | Hedef Gecikme |
|-------|---------------|
| Audio Transport (WebRTC) | <50ms |
| STT (ilk kısmi sonuç) | 100-200ms |
| LLM TTFT (Time to First Token) | 200-400ms |
| TTS TTFB (Time to First Byte) | 100-300ms |
| **Toplam (algılanan)** | **<1 saniye** |

[^160^]

**Chunking Stratejisi:**
Baseten'in VAD tabanlı chunking yaklaşımı, sesi sessizlik periyotlarına göre 30 saniyelik konuşma segmentlerine böler, boşlukları kaldırarak GPU işlemini optimize eder [^60^]. faster-whisper'da `vad_filter=True` ile Silero VAD ön-filtresi aktive edilebilir [^104^].

#### 5.3 Barge-in (Konuşma Üzerine Konuşma) Desteği

Barge-in, kullanıcının AI ajan konuşurken konuşmaya başlayarak yanıtı kesmesi yeteneğidir [^45^][^57^][^58^].

**Pipecat Implementasyonu:**
`UserStartedSpeakingFrame` algılandığında pipeline, LLM ve TTS'teki bekleyen tüm görevleri otomatik olarak iptal eder [^70^]. Interruption handler'da `InterruptionFrame` alındığında:
1. Nesil sayacı artırılarak uçuşan ses geçersiz kılınır
2. WebSocket üzerinden `cancel` mesajı gönderilir
3. Yerel durum sıfırlanır [^67^]

**LiveKit Implementasyonu:**
VAD, ajan konuşurken kullanıcı sesi algıladığında bir interruption event'i ateşler. Bu event, aktif TTS oynatımını iptal eder ve yeni bir STT geçişi tetikler [^58^].

**Edge Cases:**
- Dolgu sesleri ("mm-hmm", "evet") her zaman tam interruption tetiklememelidir
- Ajan sesinin mikrofona yansıması (echo) yanlış interruption'a neden olabilir
- Araç çağrısı (tool call) sırasında interruption, geri alınamaz işlemler için risklidir [^58^]

#### 5.4 Turn Detection (Sıra Tespiti)

Akustik VAD, sesin anlamını anlayamaz; bir duraklama düşünme, cümlenin sonu veya dramatik duraklama olabilir [^156^].

**Semantic Turn Detection yaklaşımları:**

| Sağlayıcı | Girdi | Özellik |
|-----------|-------|---------|
| LiveKit EOU | Yalnızca metin | Transformer tabanlı |
| Pipecat Smart Turn | Yalnızca ses | Prosodi, intonasyon |
| AssemblyAI | Metin + Ses | Hibrit |
| OpenAI Realtime API | Sunucu taraflı | Sınırlı ayarlanabilirlik |

[^153^][^155^][^158^]

Pipecat Smart Turn v3.2, BSD 2-clause lisanslı, HuggingFace'de açık ağırlıkları bulunan, topluluk odaklı bir native audio turn detection modelidir [^163^].

#### 5.5 Tamamen Yerel Pipeline Örneği: Home Assistant

Joe Karlsson'ın kurulumu, Wyoming protokolü üzerinden şu bileşenleri birleştirir [^72^]:

```yaml
name: Local Voice
stt_engine: stt.faster_whisper_gpu
stt_language: en
tts_engine: tts.piper
tts_voice: en_US-libritts-high
conversation_engine: conversation.ollama_conversation
prefer_local_intents: true
```

- **faster-whisper** Docker container'da GPU passthrough ile çalışır
- **Piper** Docker container'da CPU üzerinde çalışır
- **Ollama** GPU node'da çalışır
- **Wyoming protokolü** üzerinden HA ile iletişim kurar
- `prefer_local_intents: true`, "ışıkları kapat" gibi basit komutları LLM'e gitmeden HA'nın kendi intent recognition'u ile 200ms'de işler [^72^]

**Fallback Zinciri:**
1. GPU Whisper + Piper + Ollama (tercih edilen)
2. CPU Whisper + Piper + Ollama (GPU hatası durumunda)
3. Home Assistant Cloud (tamamen yerel başarısızlık durumunda)

[^72^]

#### 5.6 Gecikme Karşılaştırması: Pipeline vs End-to-End

| Mimarisi | End-to-End Gecikme | Özellikler |
|----------|-------------------|------------|
| Sequential Pipeline (STT→LLM→TTS) | 2-4 saniye | Basit, modüler |
| Streaming Pipeline | 450-750ms | Üretim standardı |
| OpenAI Realtime API | 200-300ms | Bulut bağımlılığı |
| Yerel Optimized (Home Assistant) | 1-3 saniye | Tamamen offline |

[^123^][^160^][^162^]

Akademik bir çalışmada, streaming ASR + quantize LLM + real-time TTS pipeline'ı ortalama 0.94 saniye gecikme (TTFT 0.106s, TTFA 0.678s) elde etmiştir [^165^]. Ancak worst-case 3.154 saniyeye çıkabilmektedir.

#### 5.7 Ses Kayıt ve Format Standartları

- **Örnekleme hızı**: 16kHz (Whisper/VAD için), 24kHz (Kokoro TTS için), 22.05kHz (Piper için), 44.1kHz (MeloTTS için)
- **Format**: PCM 16-bit (Wyoming, WebRTC), float32 (whisper.cpp)
- **Chunk boyutu**: 30ms (Silero VAD), 1024 sample (whisper.cpp streaming örneği)

---

## Kaynakça

- [^42^] https://github.com/gauravvij/neural_tts/blob/main/blog/neural_tts_evolution.md - Neural TTS evolution benchmark (2026)
- [^43^] https://www.codesota.com/guides/tts-models - Best Open-Source TTS Models Compared | 2026 Guide
- [^44^] https://www.ttsinsider.com/xtts-v2-vs-kokoro/ - XTTS V2 vs Kokoro 82M comparison
- [^45^] https://www.assemblyai.com/blog/build-a-voice-assistant-app-with-voice-agent-api - AssemblyAI Voice Agent API with barge-in
- [^46^] https://inworld.ai/resources/build-stt-llm-tts-voice-pipeline - STT-LLM-TTS Voice Pipeline Python
- [^47^] https://www.reddit.com/r/LocalLLaMA/comments/1brqwun/i_compared_the_different_open_source_whisper/ - Whisper packages comparison
- [^48^] https://medium.com/@programmerraja/2025-voice-ai-guide-how-to-make-your-own-real-time-voice-agent-part-3-7ca328aaea72 - Real-time voice agent guide
- [^49^] https://agentfactory.panaversity.org/docs/Building-Realtime-Voice-Agents/voice-ai-fundamentals/voice-technology-stack - Voice AI Technology Stack
- [^50^] https://www.joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/ - Fully local voice assistant for Home Assistant
- [^51^] https://theten.ai/docs/ten_vad - TEN VAD framework
- [^52^] https://picovoice.ai/blog/best-voice-activity-detection-vad/ - Cobra vs Silero vs WebRTC VAD 2026
- [^53^] https://github.com/orgs/home-assistant/discussions/2623 - Home Assistant multimodal live APIs discussion
- [^54^] https://local-ai-models.ai/ - Local AI Model Cheat Sheet 2026
- [^55^] https://portalzine.de/text-to-speech-solutions-ranked-by-speech-quality/ - TTS Solutions Ranked by Speech Quality
- [^56^] https://weesperneonflow.ai/en/blog/2026-03-31-voxtral-whisper-open-source-speech-models-comparison-2026/ - Voxtral vs Whisper comparison
- [^57^] https://sellerity.co/blog/livekit-pipecat-web-voice-agents - LiveKit vs Pipecat building voice agents
- [^58^] https://livekit.com/blog/sequential-pipeline-architecture-voice-agents - Sequential Pipeline Architecture for Voice Agents
- [^59^] https://novascribe.ai/how-accurate-is-whisper - How Accurate Is Whisper in 2026? WER by Language
- [^60^] https://www.baseten.co/blog/the-fastest-most-accurate-and-cost-efficient-whisper-transcription/ - Baseten Whisper optimization
- [^61^] https://blog.dograh.com/ai-voice-agents-github-proven-guide-dograh-vs-livekit-vs-pipecat/ - AI Voice Agents GitHub guide
- [^62^] https://kokorottsai.com/ - Kokoro TTS official website
- [^63^] https://sourceforge.net/projects/faster-whisper.mirror/ - Faster Whisper project page
- [^64^] https://www.researchgate.net/publication/386901583_Evaluating_the_Performance_of_Turkish_Automatic_Speech_Recognition_Using_the_Generative_AI-Based_Whisper_Model - Turkish ASR Whisper evaluation
- [^65^] https://ui.adsabs.harvard.edu/abs/2024ubmk.conf...99G/abstract - Turkish ASR using Whisper model (UBMK 2024)
- [^66^] https://picovoice.ai/blog/complete-guide-to-wake-word/ - Complete Guide to Wake Word Detection 2026
- [^67^] https://github.com/pipecat-ai/nemotron-january-2026/blob/main/docs/streaming-pipeline-architecture.md - Pipecat streaming pipeline architecture
- [^68^] https://github.com/PierrunoYT/Kokoro-TTS-Local - Kokoro TTS Local implementation
- [^69^] https://www.mdpi.com/2079-9292/13/21/4227 - Whisper-based Turkish ASR with LoRA fine-tuning (MDPI Electronics 2024)
- [^70^] https://www.arunbaby.com/ai-agents/0018-voice-agent-frameworks/ - Voice Agent Frameworks: LiveKit & Pipecat
- [^71^] https://arxiv.org/html/2307.14743v2 - Turning Whisper into Real-Time Transcription System
- [^72^] https://www.joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/ - Local Voice AI Home Assistant (GPU)
- [^73^] https://github.com/ggml-org/whisper.cpp/discussions/3567 - whisper.cpp streaming performance issue on Android
- [^74^] https://www.reddit.com/r/androiddev/comments/1po663c/whispercpp_on_android_streaming_live/ - whisper.cpp Android streaming discussion
- [^75^] https://openwakeword.com/ - OpenWakeWord official website
- [^76^] https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks - Best open source STT 2026 benchmarks
- [^77^] https://aiindia.ai/asr-models-comparison/ - ASR Models Comparison Guide 2025
- [^78^] https://huggingface.co/blog/norwooodsystems/faster-whisper-vs-canary-qwen-2-5b - Faster-Whisper vs NVIDIA Canary-Qwen-2.5B
- [^79^] https://community.home-assistant.io/t/remote-voice-assist-pipeline-whisper/841968 - Home Assistant remote voice assist pipeline
- [^80^] https://arxiv.org/html/2406.19674v1 - Accurate Speech Recognition & Translation without Web-Scale Data (Canary paper)
- [^81^] https://dev.to/gracezzhang/python-wake-word-detection-tutorial-picovoice-5gm - Python Wake Word Detection Tutorial Picovoice
- [^82^] https://developer.nvidia.com/blog/nvidia-speech-and-translation-ai-models-set-records-for-speed-and-accuracy/ - NVIDIA Speech and Translation AI Models
- [^83^] https://github.com/matatonic/openedai-speech - OpenAI API compatible TTS server with XTTS/Piper
- [^84^] https://www.youtube.com/watch?v=Vp_AaXQLtac - Home Assistant local assist pipeline video
- [^101^] https://docs.pipecat.ai/api-reference/server/services/tts/xtts - XTTS in Pipecat framework
- [^102^] https://www.reddit.com/r/LocalLLaMA/comments/1f0awd6/best_local_open_source_texttospeech_and/ - Best local open source TTS list 2025
- [^103^] https://pypi.org/project/coqui-tts/ - coqui-tts PyPI
- [^104^] https://gist.github.com/danielrosehill/278b1719598093767126e52105ae076e - Whisper Variants Comparison for AMD GPU
- [^105^] https://brasstranscripts.com/blog/speaker-diarization-models-comparison - Best Speaker Diarization Models Compared 2026
- [^106^] https://localaimaster.com/models/coqui-tts - Coqui TTS Technical Analysis
- [^107^] https://arxiv.org/html/2603.08823v2 - Fish Audio S2 Technical Report
- [^108^] https://www.reddit.com/r/ChatGPTPromptGenius/comments/18r2jgt/coqui_tts_local_installation_tutorial_clone/ - Coqui TTS local installation tutorial
- [^109^] https://sourceforge.net/projects/fish-speech.mirror/ - Fish Speech project page
- [^110^] https://docs.clore.ai/guides/audio-and-voice/whisperx - WhisperX with Diarization guide
- [^111^] https://coqui-tts.readthedocs.io/en/latest/cloning.html - Coqui TTS Voice cloning documentation
- [^112^] https://brasstranscripts.com/blog/whisperx-vs-competitors-accuracy-benchmark - WhisperX vs Competitors benchmark
- [^123^] https://www.eesel.ai/blog/realtime-api-vs-whisper-vs-tts-api - Realtime API vs Whisper vs TTS API
- [^124^] https://inworld.ai/resources/best-speech-to-speech-apis - Best Speech-to-Speech APIs 2026
- [^125^] https://arxiv.org/html/2503.09905v1 - Quantization for OpenAI's Whisper Models
- [^126^] https://sdxlturbo.ai/blog-Get-crystalclear-humanlike-voices-in-seconds-with-MeloTTS-A-new-OpenSource-Local-TTS-29025 - MeloTTS review
- [^127^] https://developers.openai.com/cookbook/examples/speech_transcription_methods - Comparing Speech-to-Text Methods with OpenAI API
- [^128^] https://github.com/ufal/whisper_streaming - Whisper realtime streaming for long speech-to-text
- [^129^] https://huggingface.co/spaces/openai/whisper/discussions/76 - Whisper real-time discussion
- [^130^] https://sourceforge.net/projects/piper-tts.mirror/ - Piper TTS project page
- [^131^] https://github.com/myshell-ai/MeloTTS - MeloTTS GitHub
- [^132^] https://alternativeto.net/software/snowboy/ - Snowboy alternatives
- [^133^] https://sourceforge.net/projects/melotts.mirror/ - MeloTTS project page
- [^134^] https://huggingface.co/rhasspy/piper-voices/discussions - rhasspy/piper-voices discussions
- [^135^] https://www.scribd.com/document/869359157/2023-ijcnlp-demo-3 - Whisper-Streaming for Real-Time Transcription paper
- [^136^] https://github.com/dscripka/openWakeWord - openWakeWord GitHub
- [^153^] https://inworld.ai/resources/what-is-semantic-vad - What Is Semantic VAD?
- [^154^] https://github.com/HKUDS/nanobot/issues/3257 - Pipeline latency metrics discussion
- [^155^] https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection - Turn Detection for Voice Agents
- [^156^] https://agentfactory.panaversity.org/docs/Building-Realtime-Voice-Agents/voice-ai-fundamentals/voice-technology-stack - Voice AI Technology Stack
- [^157^] https://docs.pipecat.ai/pipecat/learn/speech-input - Pipecat Speech Input & Turn Detection
- [^158^] https://www.assemblyai.com/blog/turn-detection-endpointing-voice-agent - Intelligent turn detection comparison
- [^159^] https://docs.livekit.io/agents/logic/turns/ - LiveKit Turns overview
- [^160^] https://livekit.com/blog/voice-agent-architecture-stt-llm-tts-pipelines-explained - Voice Agent Architecture: STT, LLM, and TTS Pipelines
- [^161^] https://www.twilio.com/en-us/blog/developers/best-practices/guide-core-latency-ai-voice-agents - Core Latency in AI Voice Agents
- [^162^] https://deepgram.com/learn/unified-end-to-end-text-to-speech-architecture-cuts-latency - End-to-End Text-to-Speech: Cut Voice Latency by 50-70%
- [^163^] https://github.com/pipecat-ai/smart-turn - Pipecat Smart Turn v3.2
- [^164^] https://dev.to/cloudx/cracking-the-1-second-voice-loop-what-we-learned-after-30-stack-benchmarks-427 - Cracking the <1-second Voice Loop
- [^165^] https://arxiv.org/html/2508.04721v1 - Toward Low-Latency End-to-End Voice Agents for Telecommunications