# SPEC.md — TurkishJARVIS Kişisel AI Asistanı

## Proje Adı
TurkishJARVIS ("Jarvis" adı kullanıcı tarafından değiştirilebilir)

## Teknoloji Stack
- **Runtime**: Python 3.10+
- **Backend**: FastAPI + Uvicorn
- **LLM**: Ollama (OpenAI-compatible API)
- **LLM Model**: Qwen 3.5 14B Q4_K_M (Türkçe, tool calling)
- **Vector DB**: ChromaDB (embedded, `chromadb` Python paketi)
- **Conv. Memory**: SQLite (`sqlite3` stdlib)
- **STT**: faster-whisper (`faster-whisper` pip)
- **TTS**: Piper TTS (`piper-tts` pip veya subprocess)
- **Wakeword**: openWakeWord (`openwakeword` pip)
- **VAD**: Silero VAD (`silero-vad` veya `snakers4/silero-vad` PyTorch)
- **UI**: Gradio (`gradio` pip) + WebSocket
- **RAG**: LangChain (`langchain`, `langchain-ollama`, `langchain-chroma`)
- **Sandbox**: subprocess + timeout (başlangıç)

## Modül Yapısı

```
turkish_jarvis/
├── __init__.py
├── main.py                 # FastAPI entry point
├── config.py               # Yapılandırma sınıfı (Pydantic Settings)
├── core/
│   ├── __init__.py
│   ├── llm.py              # Ollama LLM client
│   ├── stt.py              # faster-whisper wrapper
│   ├── tts.py              # Piper TTS wrapper
│   ├── wakeword.py         # openWakeWord wrapper
│   ├── vad.py              # Silero VAD wrapper
│   └── pipeline.py         # Ses pipeline orkestratörü
├── memory/
│   ├── __init__.py
│   ├── conversation.py      # SQLite conversation store
│   ├── episodic.py        # ChromaDB episodic memory
│   ├── longterm.py        # SQLite long-term preferences
│   └── rag.py             # LangChain RAG pipeline
├── personality/
│   ├── __init__.py
│   ├── system_prompt.py   # Sistem prompt yönetimi
│   ├── preferences.py     # Kullanıcı tercih öğrenme
│   └── voice_profile.py   # Ses profili
├── tools/
│   ├── __init__.py
│   ├── registry.py        # Araç kayıt defteri
│   ├── builtin.py         # Yerleşik araçlar (8 araç)
│   ├── mcp_client.py      # MCP client (opsiyonel başlangıçta stub)
│   └── sandbox.py         # Güvenli kod yürütme
├── ui/
│   ├── __init__.py
│   ├── gradio_app.py      # Gradio web arayüzü
│   └── websocket.py       # WebSocket handler
└── utils/
    ├── __init__.py
    ├── security.py        # Input sanitization
    └── helpers.py         # Yardımcı fonksiyonlar
```

## Interface Contracts

### config.py
```python
class JARVISConfig(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"
    stt_model: str = "large-v3"
    tts_model_path: str = "./models/piper/tr_TR-dfki-medium.onnx"
    tts_config_path: str = "./models/piper/tr_TR-dfki-medium.json"
    wakeword_model: str = "./models/openwakeword/jarvis.tflite"
    chroma_persist_dir: str = "./data/chroma"
    sqlite_path: str = "./data/jarvis.db"
    voice_name: str = "Jarvis"
    personality_style: str = "professional_friendly"
```

### core/llm.py
```python
class LLMClient:
    async def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
        # Ollama chat API çağrısı, tool calling destekli
        # Returns: {"content": str, "tool_calls": list|None}
    
    async def stream_chat(self, messages: list[dict]) -> AsyncIterator[str]:
        # Streaming response
```

### memory/conversation.py
```python
class ConversationStore:
    def add_message(self, session_id: str, role: str, content: str, tool_calls: list = None)
    def get_history(self, session_id: str, limit: int = 20) -> list[dict]
    def create_summary(self, session_id: str) -> str
```

### memory/episodic.py
```python
class EpisodicMemory:
    def add(self, text: str, metadata: dict)
    def search(self, query: str, k: int = 5) -> list[dict]
```

### memory/longterm.py
```python
class LongTermMemory:
    def set_preference(self, user_id: str, key: str, value: any)
    def get_preference(self, user_id: str, key: str) -> any
    def get_all_preferences(self, user_id: str) -> dict
```

### tools/registry.py
```python
class ToolRegistry:
    def register(self, name: str, func: callable, schema: dict)
    def get(self, name: str) -> callable
    def get_schemas(self) -> list[dict]
    def execute(self, name: str, arguments: dict) -> any
```

### tools/builtin.py
8 yerleşik araç fonksiyonu:
- `get_current_time()` -> str
- `get_weather(location: str)` -> str
- `calculator(expression: str)` -> float
- `web_search(query: str, max_results: int = 5)` -> list[dict]
- `read_file(path: str, max_lines: int = 100)` -> str
- `write_file(path: str, content: str)` -> bool
- `run_python(code: str)` -> str
- `system_info()` -> dict

### personality/system_prompt.py
```python
class SystemPromptBuilder:
    def build(self, user_preferences: dict, memory_context: str, tool_schemas: list) -> str
```

### ui/gradio_app.py
```python
class GradioUI:
    def build(self) -> gr.Blocks
    # ChatInterface + Audio input/output
```

## Data Flow

1. Kullanıcı mesajı (metin veya ses) → FastAPI endpoint
2. Ses ise: STT → metin
3. Session ID belirle / mevcut session'ı getir
4. Konuşma geçmişini getir (ConversationStore)
5. Episodic memory'de ara (ilgili geçmiş olaylar)
6. Long-term memory'den kullanıcı tercihlerini getir
7. Sistem prompt oluştur (personality + tercihler + araç şemaları)
8. LLM'e gönder (messages + tools)
9. LLM yanıtı: metin veya tool_call
10. Tool_call ise: araç çalıştır, sonucu LLM'e geri gönder
11. Final yanıtı: metin ise TTS'e gönder (ses modundaysa)
12. Yanıtı kaydet (ConversationStore)
13. Kullanıcıya gönder (metin + ses)

## Gereksinimler (requirements.txt)
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
pydantic-settings>=2.6.0
gradio>=5.8.0
websockets>=14.0
faster-whisper>=1.1.0
piper-tts>=1.2.0
openwakeword>=0.6.0
chromadb>=0.6.0
langchain>=0.3.0
langchain-ollama>=0.2.0
langchain-chroma>=0.1.0
sentence-transformers>=3.3.0
numpy>=2.0.0
aiohttp>=3.11.0
requests>=2.32.0
httpx>=0.27.0
```

## Kurulum
```bash
# 1. Ollama kurulumu (sistem seviyesinde)
# https://ollama.com/download

# 2. Model indirme
ollama pull qwen2.5:14b

# 3. Piper TTS model indirme
mkdir -p models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx.json

# 4. Python bağımlılıkları
pip install -r requirements.txt

# 5. Çalıştırma
python main.py
```
