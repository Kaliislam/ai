# Phase 2: Dimension Decomposition - JARVIS Tarzı Kişisel AI Asistanı

## Araştırma Boyutları (12 Dimensions)

### Dim 01: Yerel LLM Altyapısı ve Türkçe Model Ekosistemi
**Açı**: Teknik altyapı ve model seçimi
- Ollama, vLLM, llama.cpp, SGLang karşılaştırması
- Türkçe performansı en iyi açık kaynak modeller (Qwen 3.5, Llama 3.3, Mistral)
- Tool calling desteği, quantization stratejileri
- Donanım gereksinimleri (VRAM/RAM/CPU)

### Dim 02: Sesli Etkileşim Pipeline ve Gerçek Zamanlı Ses İşleme
**Açı**: Ses deneyimi ve pipeline mimarisi
- STT: Whisper, faster-whisper, whisper.cpp (Türkçe WER karşılaştırması)
- TTS: Piper (MIT, Türkçe), Kokoro-82M, XTTS-v2
- Wakeword: openWakeWord, özel wakeword eğitimi
- VAD: Silero VAD
- Pipeline optimizasyonu, streaming, barge-in

### Dim 03: Bellek Mimarisi - Hibrit Vektör-Graph-Konvansiyonel
**Açı**: AI'nin "hatırlama" yeteneği
- Vektör DB: Chroma, LanceDB, chromem-go (embedded)
- Graph memory: Mem0g, Cognee, Kuzu
- Konvansiyonel: Letta memory blocks, özetleme
- Hibrit yaklaşımlar ve context window yönetimi

### Dim 04: RAG Pipeline ve Kişisel Bilgi Entegrasyonu
**Açı**: Kişisel bilgileri LLM'e entegre etme
- Document ingestion, chunking stratejileri
- Embedding modelleri (BGE-M3, Cohere, OpenAI)
- Reranking (FlashRank, Cohere)
- RAG vs Fine-tuning karşılaştırması
- Kişisel dosyalar, notlar, geçmiş konuşmalar

### Dim 05: Ajan Framework, Tool Calling ve MCP Entegrasyonu
**Açı**: Asistanın "eylem" yeteneği
- Qwen-Agent, Letta, LangChain, CrewAI karşılaştırması
- MCP (Model Context Protocol): host-client-server mimarisi
- Function calling şemaları, JSON mode
- ReAct, Reflexion reasoning pattern'leri
- Sandbox ve güvenli yürütme

### Dim 06: Kişilik Tasarımı, Sistem Prompt ve Kişiselleştirme
**Açı**: Asistanın "karakteri" ve davranış kalıpları
- Sistem prompt mühendisliği (JARVIS tarzı kişilik)
- Few-shot prompting ile davranış kalıpları
- Kullanıcı tercih öğrenme (implicit/explicit)
- Ajan kişiliği ve tutarlılık
- Multi-user desteği ve ayrık hafıza

### Dim 07: Mevcut Açık Kaynak Çözümlerin Karşılaştırmalı Analizi
**Açı**: "Tekerleği yeniden icat etme" vs mevcut çözümleri kullanma
- OpenJarvis (Stanford, öğrenme döngüsü)
- LocalAGI (Go, Docker, kolay kurulum)
- Home Assistant + Assist (Wyoming, sesli)
- OpenVoiceOS (Mycroft çatallaması)
- AIlice (IACT mimarisi)
- Karşılaştırma: kurulum, Türkçe, genişletilebilirlik, aktif geliştirme

### Dim 08: Güvenlik, Gizlilik ve Sandbox Stratejileri
**Açı**: Yerel çalışmanın güvenlik boyutu
- Tamamen yerel çalışma (air-gapped)
- Sandbox: Docker, microVM (Firecracker), gVisor
- Prompt injection koruması
- Alet yetkilendirme ve onay mekanizmaları
- Veri gizliliği ve şifreleme

### Dim 09: Donanım Optimizasyonu ve Edge Cihaz Performansı
**Açı**: Farklı donanım profillerine uyum
- GPU (CUDA/ROCm) vs CPU-only senaryolar
- Quantization etkileri (GGUF, AWQ, GPTQ)
- Raspberry Pi / edge cihaz desteği
- Bellek (RAM) optimizasyonu
- Model offloading ve layer dağıtımı

### Dim 10: Ev Otomasyonu ve Harici Servis Entegrasyonu
**Açı**: Asistanın çevresiyle etkileşimi
- Home Assistant API entegrasyonu
- Akıllı ev cihaz kontrolü
- Takvim, e-posta, hava durumu, haberler
- Web tarayıcı otomasyonu (Playwright)
- Code interpreter / sandbox

### Dim 11: Çoklu Oturum Yönetimi ve Eşzamanlılık
**Açı**: Ölçeklenebilirlik ve çok kullanıcılı senaryolar
- WebSocket / SSE streaming
- Session state yönetimi
- Context isolation (user_id, session_id)
- Async memory writes
- Concurrent tool execution

### Dim 12: Kurulum, Dağıtım ve DevOps Pipelines
**Açı**: Kullanıcı deneyimi ve sürdürülebilirlik
- Docker Compose kurulumu
- One-click installer script'leri
- Otomatik model indirme ve yapılandırma
- Web UI (chat arayüzü)
- Güncelleme ve bakım stratejileri
