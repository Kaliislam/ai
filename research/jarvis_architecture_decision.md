# Mimari Karar Dokümanı: TurkishJARVIS Kişisel AI Asistanı

## Vizyon
Tony Stark'ın JARVIS'ine benzer, tamamen yerel çalışabilen, Türkçe destekli, kişiselleştirilebilir, sesli ve metin tabanlı etkileşim destekleyen bir yapay zeka asistanı.

## Karar Özeti: Sıfırdan Python Framework'ü
Mevcut çözümler (OpenJarvis, LocalAGI, Home Assistant) incelendi. En mantıklı yaklaşım: **her birinden en iyi bileşenleri seçip, Python tabanlı özel bir framework yazmak.**

- Home Assistant'ın ses pipeline'ından (Wyoming) ilham alınacak
- Letta'nın bellek mimarisinden ilham alınacak
- Qwen-Agent'ın tool calling yaklaşımından ilham alınacak
- Ama kod tamamen sıfırdan, sade ve kontrol edilebilir olacak

## Teknoloji Stack (Final Karar)

### Çekirdek Bileşenler
| Bileşen | Teknoloji | Neden |
|---------|-----------|-------|
| **LLM Engine** | Ollama | En kolay kurulum, OpenAI-compatible API, model yönetimi |
| **LLM Model** | Qwen 3.5 14B (Q4_K_M) | Türkçe + 201 dil, tool calling, 16GB VRAM'de çalışır |
| **STT** | faster-whisper (medium) | Türkçe ~%10 WER, hızlı, streaming desteği |
| **TTS** | Piper TTS (tr_TR-dfki-medium) | MIT lisans, Türkçe, CPU'da <100MB, RTF 0.008 |
| **Wakeword** | openWakeWord | Apache 2.0, "Jarvis" wakeword eğitimi <1 saat |
| **VAD** | Silero VAD | <1ms latency, ~2MB, endüstri standardı |
| **Vector DB** | ChromaDB (embedded) | Python native, gömülebilir, hafif |
| **Conv. Memory** | SQLite + JSON | Kullanıcı tercihleri, özetler, basit |
| **RAG** | LangChain + Ollama (nomic-embed-text) | Belge ingestion, kişisel bilgiler |
| **Backend** | Python FastAPI + WebSocket | Async, hızlı, OpenAI API compatible |
| **UI** | Gradio (MVP) | Hızlı prototipleme, ses desteği |
| **Tools** | Native Python functions + MCP client | Genişletilebilir |
| **Sandbox** | subprocess + timeout | Güvenli kod çalıştırma (başlangıç) |

### Ses Pipeline Mimarisi
```
[openWakeWord] --"Jarvis"--> [Silero VAD] --> [faster-whisper STT] 
--> [FastAPI Backend] --> [Ollama LLM (Qwen 3.5)] --> [Piper TTS] --> [Ses Çıkışı]
         ^                                                    |
         |------------ [ChromaDB Bellek] <---------------------|
```

### Bellek Mimarisi (4 Katmanlı - Letta'dan ilham)
1. **Working Memory**: FastAPI request context (geçici)
2. **Conversation Memory**: Son 10 mesaj + rolling summary (SQLite)
3. **Episodic Memory**: Önemli olaylar, kararlar (ChromaDB vektör)
4. **Long-term Memory**: Kullanıcı tercihleri, kişisel bilgiler (SQLite JSON)

### Araç Sistemi (MCP + Native)
Başlangıç araçları:
- `get_current_time` - Saat/tarih
- `get_weather` - Hava durumu (OpenMeteo API - ücretsiz)
- `calculator` - Hesap makinesi
- `web_search` - Web arama (DuckDuckGo - ücretsiz)
- `read_file` - Dosya okuma
- `write_file` - Dosya yazma
- `run_python` - Python kod çalıştırma (sandbox)
- `system_info` - Sistem bilgisi

İleride: Home Assistant MCP, web browser MCP, vs.

### Kişilik Tasarımı (JARVIS Tarzı)
- **Adı**: "JARVIS" (kullanıcı değiştirebilir)
- **Karakteri**: Profesyonel ama samimi, proaktif, mizahi, sadık, bilgili
- **Dili**: Türkçe (ana), İngilizce (ikincil)
- **Ses tonu**: Piper tr_TR-dfki-medium (erkek sesi, profesyonel)
- **Davranış kalıpları**: Kullanıcıyı adıyla hitap etme, tercihleri hatırlama, proaktif öneriler

### Sistem Prompt Tasarımı
- Persona tanımı
- Yetki sınırları
- Araç kullanım kuralları
- Güvenlik yönergeleri
- Kullanıcı tercihleri entegrasyonu (dinamik)

## Uygulama Yapısı (Python Modülleri)
```
turkish_jarvis/
├── main.py              # FastAPI entry point
├── config.py            # Yapılandırma
├── core/
│   ├── llm.py           # Ollama LLM entegrasyonu
│   ├── stt.py           # faster-whisper entegrasyonu
│   ├── tts.py           # Piper TTS entegrasyonu
│   ├── wakeword.py      # openWakeWord entegrasyonu
│   ├── vad.py           # Silero VAD entegrasyonu
│   └── pipeline.py      # Ses pipeline orkestrasyonu
├── memory/
│   ├── conversation.py  # Konuşma hafızası (SQLite)
│   ├── episodic.py      # Episodik hafıza (ChromaDB)
│   ├── longterm.py      # Uzun dönem hafıza (SQLite)
│   └── rag.py           # RAG pipeline (LangChain)
├── personality/
│   ├── system_prompt.py # Sistem prompt yönetimi
│   ├── preferences.py   # Kullanıcı tercih öğrenme
│   └── voice_profile.py # Ses profili yönetimi
├── tools/
│   ├── registry.py      # Araç kayıt/defteri
│   ├── builtin.py       # Yerleşik araçlar
│   ├── mcp_client.py    # MCP client
│   └── sandbox.py       # Sandbox yürütme
├── ui/
│   ├── gradio_app.py    # Gradio web arayüzü
│   └── websocket.py     # WebSocket handler
└── utils/
    ├── security.py      # Prompt injection koruması
    └── helpers.py       # Yardımcı fonksiyonlar
```

## Geliştirme Aşamaları
### Aşama 1: Çekirdek Backend
- FastAPI + Ollama LLM entegrasyonu
- Basit chat API (HTTP + WebSocket)
- Bellek katmanları (SQLite + ChromaDB)
- Sistem prompt ve kişilik

### Aşama 2: Araç Sistemi
- Yerleşik araçlar (saat, hava durumu, hesap makinesi)
- Tool calling / function calling
- RAG entegrasyonu (belge yükleme)

### Aşama 3: Sesli Etkileşim
- Piper TTS entegrasyonu
- faster-whisper STT entegrasyonu
- Ses pipeline (metin tabanlı ilk, sonra streaming)

### Aşama 4: Kişiselleştirme
- Kullanıcı tercih öğrenme
- RAG ile kişisel bilgiler entegrasyonu
- Kişilik ayarları

### Aşama 5: Gelişmiş Özellikler
- openWakeWord wakeword
- MCP entegrasyonu
- Multi-session desteği
- Docker deployment
