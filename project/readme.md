TurkishJARVIS v3.1 — "Kapsamlı Kişisel Asistan"
> "Merhaba efendim. Bugün hangi projenizde çalışalım? Son sohbetimizden öğrendiklerimi hatırlıyorum."
TurkishJARVIS v3.1 — Artık sadece bir asistan değil; projelerinizi yöneten, görevlerinizi takip eden, internetten gerçek zamanlı bilgi arayan, bütün sohbetlerinizi hatırlayan, GitHub'daki binlerce ajan skill'ini kullanabilen, kapsamlı bir kişisel AI sistemidir.
---
🆕 v3.1 Yenilikleri
📦 Kapsamlı Skill Framework
SKILL.md Parser — GitHub awesome-agent-skills repolarındaki skill'leri otomatik parse eder
Skill Loader — SKILL.md'den Python fonksiyonuna dönüştürür, dinamik yükler
Skill Registry V2 — 6 kategoride (web, dev, data, system, media, comm) organize eder
Auto-Discovery — GitHub'dan yeni skill'leri keşfeder ve yükler
Skill Templates — Yeni skill oluşturma şablonları
🌐 Gelişmiş İnternet Arama
DuckDuckGo Search — API key'siz arama
Brave Search — Hızlı sonuçlar
Google Scholar — Akademik arama
arXiv — Bilimsel makaleler
Wikipedia — Bilgi maddeleme
Haber Siteleri — Hürriyet, CNN Türk, BBC Türkçe, Webrazzi
🔄 Bilgi Tazeleme
Otomatik Web Tarama — Güncel bilgiyi RAG'e indeksler
RSS Reader — Feed'leri takip et, özetle
Topic Refresh — Belirli konularda periyodik güncelleme
Fresh Info API — "Bugün dünyada neler oldu?"
📋 Proje Yönetimi
Project Manager — Projeler oluştur, durum takibi, deadline
Todo Manager — Görev ekle, tamamla, önceliklendir, hatırlatma
Instruction Manager — Asistanın verdiği talimatları kaydet, takip et
Daily Brief — Günlük proje özetleri
Next Action — Sonraki aksiyon önerileri
💬 Sohbet Geçmişi + Bellek
Chat History — BÜTÜN sohbetler SQLite + FTS5'te kayıtlı
Full-Text Search — "Geçen hafta ne konuşmuştuk?" → anında bulur
Conversation Indexer — Semantic search (anlamsal arama)
Fact Extraction — "Kullanıcı İstanbul'da yaşıyor", "Mavi renk seviyor"
Preference Learning — Tercihleri otomatik çıkarır, profil oluşturur
Session Export — JSON/Markdown olarak dışa aktar
---
📊 v3.1 Modül Haritası (68 Modül)
```
turkish_jarvis/                          68 modül | 18,592 satır
├── main.py                  # FastAPI + TÜM entegrasyonlar
├── config.py                # Mevcut modelleri tanıyan yapılandırma
│
├── core/                    # Çekirdek sistem
│   ├── llm.py               # Ollama + fallback + model öğrenme
│   ├── stt.py, tts.py, streaming.py, pipeline.py
│   └── vad.py, wakeword.py
│
├── memory/                  # Bellek katmanları
│   ├── conversation.py, episodic.py, longterm.py
│   ├── graph.py             # Kişi-ilişki ağı
│   └── rag.py               # Kaynaklı RAG v2.0
│
├── personality/             # Karakter ve kişiselleştirme
│   ├── system_prompt.py     # JARVIS karakteri v2.0
│   ├── proactive.py         # Proaktif motor
│   ├── preferences.py
│   └── voice_profile.py     # 6 ses profili
│
├── tools/                   # Yerleşik araçlar
│   ├── builtin.py           # 8 yerleşik araç
│   └── registry.py          # Araç kayıt
│
├── skills/                  # 🆕 v3.1 — Kapsamlı Skill Framework
│   ├── skill_parser.py      # SKILL.md parse etme (380 satır)
│   ├── skill_loader.py      # Dinamik yükleme (376 satır)
│   ├── skill_registry_v2.py # Kategori bazlı registry (414 satır)
│   ├── skill_templates.py   # Şablonlar (590 satır)
│   │
│   ├── web/                 # 🆕 Web skill'leri
│   │   ├── web_search_advanced.py   # Arama motorları (649 satır)
│   │   ├── info_refresh.py          # Bilgi tazeleme (269 satır)
│   │   └── rss_reader.py            # RSS takibi (284 satır)
│   │
│   ├── dev/                 # Development skill'leri (yer tutucu)
│   ├── data/                # Data skill'leri (yer tutucu)
│   ├── system/              # 🆕 Sistem skill'leri
│   │   ├── project_manager.py      # Proje yönetimi (391 satır)
│   │   ├── todo_manager.py         # Görev takibi (343 satır)
│   │   ├── instruction_manager.py  # Talimat sistemi (329 satır)
│   │   ├── chat_history.py         # Sohbet geçmişi (684 satır)
│   │   └── conversation_indexer.py # Semantic index (521 satır)
│   ├── media/               # Media skill'leri (yer tutucu)
│   └── comm/                # Communication skill'leri (yer tutucu)
│
├── autonomy/                # 🆕 v3.0 — Kendi kendine öğrenme
│   ├── planner.py           # Çok adımlı planlama (754 satır)
│   ├── auto_skill.py        # Otomatik yetenek edinme (840 satır)
│   ├── meta_learning.py     # Meta-öğrenme (770 satır)
│   ├── self_healing.py      # Hata düzeltme (673 satır)
│   ├── knowledge_miner.py   # Bilgi kazıma (686 satır)
│   └── reflection.py        # Düşünce + değerlendirme (390 satır)
│
├── integrations/            # Entegrasyonlar
│   ├── mcp_client.py      # MCP protokolü
│   ├── home_assistant.py  # Home Assistant
│   └── browser.py         # Playwright otomasyonu
│
├── api/                     # HTTP API v2
│   └── endpoints.py         # 10+ endpoint
│
├── ui/                      # Kullanıcı arayüzü
│   ├── gradio_app.py        # Web UI
│   └── websocket.py         # WebSocket
│
├── tests/                   # Test suite
│   ├── test_config.py, test_tools.py, test_memory.py
│   ├── test_api.py, test_security.py
│   ├── test_meta_learning.py
│   └── test_self_healing.py
│
└── utils/                   # Yardımcılar
    ├── security.py, helpers.py
```
---
⚡ Hızlı Başlangıç (WSL/Linux)
```bash
cd turkish-jarvis
chmod +x scripts/setup.sh
./setup.sh  # Mevcut 7 Ollama modelinizi otomatik tespit eder

source .venv/bin/activate
python turkish_jarvis/main.py

# http://localhost:8000/ui
```
---
🚀 Kullanım Örnekleri (v3.1)
Sohbet Geçmişi Arama
```text
Kullanıcı: "Geçen hafta ne konuşmuştuk?"
Jarvis: "Geçen hafta şu konuları konuşmuştuk efendim:
         1. WSL kurulumu ve model yapılandırması
         2. llama3.1:70b'nin ağır olduğunu, qwen3-coder:30b önerisini
         3. Projelerinizi yönetecek asistan özelliklerini istemiştiniz."

Kullanıcı: "Mavi renk sevdiğimi söylemiş miydim?"
Jarvis: "Evet efendim, 3 gün önce 'en sevdiğim renk mavi' demiştiniz.
         Profilinize kaydettim."
```
Proje Yönetimi
```text
Kullanıcı: "Yeni proje: TurkishJARVIS geliştirme"
Jarvis: "Proje oluşturuldu efendim. 'TurkishJARVIS geliştirme' — aktif."

Kullanıcı: "Bu projeye görev ekle: main.py'yi optimize et, öncelik: yüksek, deadline: yarın"
Jarvis: "Görev eklendi efendim. Yarın 23:59'a kadar main.py optimizasyonu."

Kullanıcı: "Bugün ne yapmam lazım?"
Jarvis: "Bugün 3 göreviniz var efendim:
         1. [Yüksek] main.py optimizasyonu — deadline: yarın
         2. [Orta] README güncelleme
         3. [Düşük] Yeni skill testi"
```
İnternet Arama
```text
Kullanıcı: "Bugün teknoloji dünyasında neler oldu?"
Jarvis: "Araştırıyorum efendim..."
      (→ Web search yapar)
      (→ RSS feed'lerini kontrol eder)
      (→ Özetler)
      
Jarvis: "Bugünün öne çıkan teknoloji haberleri:
         1. OpenAI yeni model duyurdu [TechCrunch]
         2. Google AI güncellemesi [The Verge]
         3. Yeni açık kaynak LLM [GitHub]"
```
Skill Keşif
```text
Kullanıcı: "GitHub'daki ajan skill'lerini keşfet"
Jarvis: "Awesome-agent-skills reposunu tarıyorum efendim..."
      (→ heilcheng/awesome-agent-skills SKILL.md'leri parse eder)
      (→ VoltAgent/awesome-agent-skills'i tarar)
      
Jarvis: "1000+ skill keşfedildi efendim. Kategoriler:
         - Web: 150+ skill (search, scrape, RSS)
         - Dev: 200+ skill (deploy, test, CI/CD)
         - Data: 100+ skill (analyze, viz)
         - System: 180+ skill (file, system)
         - Media: 120+ skill (image, video)
         - Comm: 250+ skill (email, slack)"
```
---
🖥️ Mevcut Modelleriniz (Otomatik)
Model	v3.1'de Kullanımı
`qwen3-coder:30b`	🏆 Default — Planlama, kod, skill exec
`gemma4:latest`	Hızlı yanıt, düşük kaynak
`llama3.1:70b`	Premium analiz, çok karmaşık
`mistral:latest`	Basit sohbet, hafif
`deepseek-r1:8b`	Matematik, mantık
`qwen3:4b` / `gemma3:4b`	Test, ultra hafif
---
🧪 Test
```bash
pytest turkish_jarvis/tests/ -v
```
---
📚 Dokümantasyon
`docs/KURULUM.md` — WSL & Linux detaylı kurulum
`docs/v3_architecture.md` — v3.0 mimari tasarım
`data/user_profile.md` — Kullanıcı profili
---
> *"Her zaman hizmetinizdeyim efendim. Bütün sohbetlerimizi, projelerinizi, ve öğrendiklerimi hatırlıyorum."* — TurkishJARVIS v3.1
