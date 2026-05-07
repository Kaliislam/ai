# Facet: Ajan Frameworkleri ve Tool Calling

## Key Findings

### Ajan Framework Karşılaştırması

- **LangChain/LangGraph**, 2026 itibarıyla 1 milyardan fazla indirme ve 106K+ GitHub yıldızıyla en geniş ekosisteme sahip framework'tür. LangGraph, üretim ortamları için tavsiye edilen graph-based stateful orchestration katmanıdır. LangChain ekibi, yeni ajan implementasyonlarını LangGraph ile yapmayı önermektedir [^31^] [^40^].

- **Qwen-Agent**, Alibaba'nın resmi framework'üdür ve Qwen modelleri için native function calling, MCP entegrasyonu, Docker-sandboxed code interpreter, RAG, BrowserQwen ve parallel tool execution sunar. Apache-2.0 lisanslıdır ve vLLM, Ollama gibi yerel OpenAI-compatible sunucuları destekler [^14^] [^15^] [^16^].

- **AutoGen** (Microsoft), 43.1K+ GitHub yıldızına sahip, konuşma odaklı multi-agent orchestration framework'tür. Human-in-the-loop, asenkron task execution ve Docker sandbox ile kod çalıştırma desteği sunar [^25^] [^26^] [^31^].

- **CrewAI**, role-based multi-agent takım yapısına odaklanır ve 30K+ GitHub yıldızına sahiptir. En düşük öğrenme eğrisine sahip framework olarak değerlendirilir. Sequential, hierarchical ve hybrid process'leri destekler [^18^] [^29^] [^31^].

- **Letta** (eski adıyla MemGPT), 15.9K+ GitHub yıldızına sahip, "LLM-as-an-Operating-System" paradigması ile stateful ajanlar için geliştirilmiştir. Core Memory (Memory Blocks), self-editing memory ve heartbeat-based looping sunar. OpenAI, Anthropic, Ollama, vLLM ve diğer yerel modellerle çalışır [^98^] [^115^] [^167^].

- **LlamaIndex**, 40.9K+ GitHub yıldızıyla data indexing ve RAG odaklıdır. Event-driven workflow'lar, ToolCallEvent ve agent-based decomposition sunar. 15+ vektör veritabanı ve 30+ doküman formatı destekler [^24^] [^167^].

- **OpenAI Agents SDK**, 8.6K+ GitHub yıldızıyla OpenAI'ye özgüdür. Agents SDK, function calling, handoff pattern ve tracing ile guardrails sunar [^167^].

- Framework karşılaştırması sonucu: Çoklu ajan sistemleri, tek ajan sistemlerine göre karmaşık görevlerde %90.2 daha iyi performans göstermektedir [^31^].

- Yerel LLM desteği açısından: **vLLM**, üretim düzeyinde tam OpenAI-compatible tool/function calling desteği, paralel çağrı ve `tool_choice` parametresini sunar. **Ollama**, 2024 itibarıyla tool calling ekledi ancak streaming tool call ve `tool_choice` desteği henüz eksiktir. **LM Studio** tool calling'i deneysel olarak destekler. **LocalAI** ise %100 OpenAI API uyumlu drop-in replacement sunar [^35^] [^166^].

### Model Context Protocol (MCP)

- **MCP (Model Context Protocol)**, Anthropic tarafından 2024 sonlarında tanıtılan, AI modellerinin harici araç ve verilere standart bir şekilde bağlanmasını sağlayan açık protokoldür. JSON-RPC 2.0 üzerine kuruludur ve LSP (Language Server Protocol) benzeri bir client-server mimarisi sunar [^22^] [^123^].

- MCP üç temel bileşenden oluşur: **Host** (kullanıcıya bakan AI uygulaması), **Client** (LLM'nin isteklerini MCP formatına çevirir) ve **Server** (spesifik araç/veri yeteneklerini sunar). Client ve server arasında 1:1 ilişki vardır [^123^] [^124^].

- MCP üç temel ilkel tip sunar: **Resources** (salt okunur veri erişimi), **Tools** (yan etkisi olan aksiyonlar - API çağrıları, hesaplama, yazma), ve **Prompts** (tekrar kullanılabilir şablonlar) [^22^] [^123^].

- Resmi MCP referans sunucuları şunlardır: **Everything** (test/referans), **Fetch** (web içeriği çekme), **Filesystem** (güvenli dosya işlemleri), **Git** (repo okuma/arama), **Memory** (bilgi grafiği tabanlı kalıcı hafıza), **Sequential Thinking** (dinamik problem çözme), **Time** (zaman/zaman dilimi) [^122^].

- MCP Memory server, bilgi grafiği tabanlı kalıcı hafıza sunar. Varlıklar (entities), gözlemler (observations) ve ilişkiler (relations) ile çalışır. Neo4j, benzer bir Memory MCP Server implementasyonu sunmaktadır [^122^] [^169^].

- MCP, LangChain, CrewAI, AutoGen gibi framework'lerle birlikte çalışır; framework'lerin "beyin" ve "orkestrasyon" katmanını değil, "eller" katmanını (harici araç erişimi) standartlaştırır [^22^].

- MCP için iki transport mekanizması vardır: **Stdio transport** (yerel süreçler arası) ve **Streamable HTTP transport** (uzak sunucular için, SSE ile streaming desteği) [^124^].

### MCP vs A2A (Agent-to-Agent Protocol)

- **A2A**, Google tarafından Nisan 2025'te tanıtılan, ajanlar arası iletişimi standartlaştıran protokoldür. MCP'den farklı olarak, ajan-aracı değil, ajan-ajan iletişimine odaklanır [^95^] [^154^].

- Temel fark: **MCP** = ajan ↔ araç/veri bağlantısı (hub-and-spoke model). **A2A** = ajan ↔ ajan koordinasyonu (ağ modeli). Çoğu üretim sisteminde her ikisi birlikte kullanılır: MCP araç erişimini, A2A multi-agent koordinasyonunu sağlar [^154^] [^155^] [^158^].

- A2A temel yetenekleri: Agent discovery, capability sharing, task-based messaging, streaming responses, secure communication. Agent Cards ile yetenek keşfi yapılır [^154^].

- Google ayrıca **UCP** (Universal Commerce Protocol, Ocak 2026), **AP2** (Agent Payments Protocol, Eylül 2025) ve **x402** (Coinbase - HTTP üzerinden otomatik ödeme) gibi tamamlayıcı protokoller geliştirmektedir [^95^].

### Tool / Function Calling Mekanizmaları

- OpenAI function calling (tool calling), JSON Schema ile tanımlanan fonksiyonları modelin kullanmasını sağlar. Şema: `type`, `name`, `description`, `parameters` (properties + required) içerir [^17^] [^21^].

- **Chat Completions API** ve **Responses API** arasında tool schema farkı vardır. Chat Completions'ta `{"type": "function", "function": {"name": ...}}` yapısı vardır. Responses API'da `{"type": "function", "name": ...}` daha düz yapı kullanılır [^156^].

- Responses API, built-in tools sunar: web_search_preview, file_search, code_interpreter, computer_use, remote MCP servers, skills [^156^].

- `tool_choice` parametresi: `auto` (model seçsin), `required` (zorunlu tool call), `none` (tool call yasak), veya spesifik bir fonksiyon zorlaması [^17^].

- vLLM, Ollama (belirli modellerle), LM Studio ve LocalAI gibi yerel sunucular OpenAI-compatible function calling destekler. Ancak Ollama'da streaming tool call ve `tool_choice` henüz eksiktir [^35^].

- Qwen modelleri (Qwen3, QwQ-32B, Qwen2.5-Instruct), native tool calling yeteneğine sahiptir ve Qwen-Agent bu yeteneği doğrudan kullanır [^15^] [^16^].

### Otonom Ajan Mimarileri

- **AI Agent Loop** (Oracle tanımı): Algılama (Perceive) → Akıl yürütme (Reason) → Planlama (Plan) → Aksiyon (Act) → Gözlemleme (Observe) döngüsü. Bu mimari, OpenAI, Anthropic, Google, Microsoft, Meta ve LangChain tarafından farklı isimlerle aynı şekilde uygulanmaktadır [^157^].

- **ReAct** (Reasoning + Acting, Yao et al. 2022, arXiv:2210.03629): LLM'nin düşünce (thought), aksiyon (action) ve gözlem (observation) adımlarını bir araya getirdiği prompting pattern'dir. ReAct, LLM'yi bir ajan haline getiren temel çerçevedir [^157^].

- **Reflexion** (Shinn et al. 2023, arXiv:2303.11366): Aktör (Actor), Değerlendirici (Evaluator) ve Öz-yansıtma (Self-Reflection) olmak üzere üç modelden oluşan modüler yapı. Çevreden gelen binary/scalar geri bildirimi doğal dil özeti (verbal feedback) olarak dönüştürür ve bir sonraki episode'de bağlam olarak kullanır. Bu, "semantik gradyan sinyali" olarak tanımlanır [^153^].

- **BabyAGI** (Yohei Nakajima, 2023): GPT-4 + LangChain + vektör veritabanı (Pinecone) kullanarak "görev → çalıştır → depola → yeni görevler oluştur → önceliklendir → tekrarla" döngüsü çalıştırır. Eğitsel bir sandbox'tır, üretim değildir [^36^] [^37^].

- **AutoGPT**: Görev ayrıştırma, önceliklendirme, yürütme döngüsü; kısa ve uzun vadeli hafıza; hata yönetimi ve eleştiri döngüsü; internet, kod ve dosya entegrasyonu içerir. 170K+ GitHub yıldızına sahiptir [^27^].

- Multi-agent orchestration pattern'leri: **Manager pattern** (merkezi ajan sub-agent'lara delegate eder), **Orchestrator-worker pattern** (paralel keşif için worker spawn eder), **Handoff pattern** (ajanlar birbirlerine kontrolü özel yeteneklere göre devreder) [^157^].

### Sandbox Güvenliği ve Code Interpreter

- AI ajan code execution için izolasyon spektrumu: Docker konteynerler (namespace + cgroup) → gVisor (user-space kernel) → Firecracker/Kata microVMs (ayrı kernel) → ZeroBoot (CoW KVM fork, 0.79ms boot) [^114^] [^118^].

- Docker konteynerler üretimde yetersizdir çünkü host kernel'ini paylaşır. CVE-2019-5736 ve CVE-2024-21626 gibi container escape zafiyetleri kaydedilmiştir [^113^] [^114^].

- Qwen-Agent, Docker-sandboxed code interpreter sunar: izole konteynerlerde Python kodu çalıştırır, resource limit ve network restriction uygular [^15^].

- AutoGen, Docker sandbox ile kod çalıştırma döngüsü sunar [^26^].

- Docker Sandboxes (2026), Claude Code, Gemini CLI, Copilot CLI, Codex, OpenCode ve Kiro için microVM izolasyonu sunar. Her ajan kendi dedicated microVM'sinde çalışır [^34^].

- E2B, Modal ve AWS Lambda gibi platformlar Firecracker/Kata microVM kullanır. Manus ve Perplexity de microVM tercih eder [^114^].

### Browser Otomasyonu

- **Playwright**, AI ajanlar için browser otomasyonunda en popüler araçtır. Accessibility tree (ARIA rolleri ve etiketler) yaklaşımı ile sayfayı yapısal, semantik metin olarak sunar. Screenshot yerine 2-5KB accessibility snapshot gönderir (20-50x token tasarrufu). Auto-wait mekanizması flaky test sorununu çözer [^96^].

- Playwright MCP server, Microsoft tarafından Mart 2025'te yayınlanmıştır. Snapshot Mode (accessibility tree) ve Vision Mode (screenshot) sunar. Ancak ~15,000 token tool definition overhead'i vardır [^96^].

- **Stagehand** (Browserbase), Playwright üzerine AI katmanı ekler: `act()`, `extract()`, `agent()`. v3 sürümünde CDP-native oldu (Playwright dependency'si kalktı). Caching sistemi ile ilk çalıştırmadan sonraki tüm çalıştırmalar sub-100ms ve zero LLM token cost ile çalışır [^96^].

- **dev-browser**, AI ajanlar için özel tasarlanmış sandboxed browser otomasyonudur. QuickJS WASM sandbox içinde çalışır (host filesystem/network erişimi yok). Playwright MCP'ye göre %30 daha hızlı ve %40 daha ucuzdur [^96^].

- **Scrapling**, anti-bot özellikli Python scraping framework'üdür. TLS fingerprint spoofing, adaptive element tracking ve built-in MCP server sunar [^96^].

### Ev Otomasyonu (Home Assistant)

- Home Assistant, Wyoming protocol üzerinden STT (faster-whisper), TTS (Piper) ve Conversation Agent (Ollama/local LLM) entegrasyonu sunar. Tamamen yerel ve offline çalışabilir [^72^].

- Home Assistant Assist API, AI ajanların cihazları kontrol etmesine ve bilgi almasına olanak tanır. OpenAI integration'ı resmi olarak sunulur, ancak OpenRouter veya yerel LLM'ler de kullanılabilir [^30^].

- Home Assistant conversation pipeline, local LLM'ler (Luna vb.) ile konfigüre edilebilir. Assist API, exposed entities üzerinden hangi cihazlara erişileceğini kontrol eder [^173^].

### OpenClaw

- OpenClaw, messaging-first, persistent memory'e sahip, kişisel kullanım için tasarlanmış otonom bir ajan işletim sistemidir. AutoGPT'den farklı olarak günlük kişisel asistan görevlerine odaklanır. 18 adımda kendi ajanınızı inşa etme rehberi sunar (chat loop → tools → skills → persistence → web tools → event-driven → multi-agent → production scale) [^97^] [^160^].

## Major Players & Sources

| Kaynak | Rol / Önem |
|---|---|
| **Anthropic** | MCP (Model Context Protocol) protokolünün yaratıcısı ve bakımcısı. Ajanlar için tool integration standardını belirledi [^22^] [^123^]. |
| **OpenAI** | Function calling / tool calling API'sının mucidi. Chat Completions API ve Responses API (agent-oriented) ile evrimleşti. Codex SDK ve Agents SDK yayınladı [^23^] [^156^]. |
| **Microsoft** | AutoGen framework'ünün geliştiricisi. Conversation-driven multi-agent orchestration. HuggingGPT/JARVIS araştırma projesi [^25^] [^26^]. |
| **Google** | A2A (Agent-to-Agent) protokolünün yaratıcısı. ReAct pattern'inin ortak mucidi. UCP, AP2 protokolleri ile ajan ticareti ekosistemini genişletiyor [^95^] [^157^]. |
| **Qwen/Alibaba** | Qwen-Agent framework'ü, BrowserQwen, Code Interpreter ve MCP entegrasyonu. Qwen modelleri (Qwen3, QwQ-32B) native tool calling ile güçlü [^14^] [^16^]. |
| **LangChain** | En popüler Python agent framework'ü (106K+ stars). LangGraph (stateful graph), LangSmith (observability) ile ekosistem oluşturdu [^31^] [^40^]. |
| **CrewAI** | Role-based multi-agent framework (30K+ stars). İş süreçleri otomasyonu için optimize [^18^] [^31^]. |
| **Letta** | Stateful memory framework (15.9K+ stars). MemGPT'den evrimleşti. "LLM-as-OS" paradigması [^98^] [^115^]. |
| **LlamaIndex** | Data indexing ve RAG odaklı framework (40.9K+ stars). Meta ile ilişkili [^24^] [^167^]. |
| **Oracle** | AI Agent Loop mimarisini "Perceive-Reason-Plan-Act-Observe" olarak formalize etti. Büyük şirketlerin aynı mimariyi farklı isimlerle kullandığını gösterdi [^157^]. |

## Trends & Signals

1. **MCP hızlı benimseme**: Anthropic, OpenAI, Microsoft, Google DeepMind gibi büyük oyuncular MCP'i destekliyor. MCP, AI agent'lerin "USB-C moment'i" olarak tanımlanıyor - tek, güvenilir bağlayıcı [^22^] [^39^].

2. **Protocol convergence (MCP + A2A)**: Üretim sistemlerinde MCP (tool access katmanı) ve A2A (agent coordination katmanı) birlikte kullanılıyor. Bu iki protokol tamamlayıcıdır, rekabet eden değil [^155^] [^158^].

3. **Yerel LLM ekosistemi olgunlaşıyor**: vLLM, Ollama, LM Studio ve LocalAI hepsi OpenAI-compatible API sunuyor. Tool calling, MCP ve function calling desteği 2025-2026'da standart hale geldi [^35^] [^166^].

4. **Sandbox isolation evolution**: Docker'dan microVM'lere (Firecracker/Kata) geçiş. AI ajanların kod çalıştırması için "container yetersizdir" konsensusu oluşuyor. Docker Sandboxes, E2B, Modal ve ZeroBoot yeni oyuncular [^113^] [^114^] [^118^].

5. **Framework'lerin graph-based evrimi**: LangGraph, stateful cyclic workflow'lar için tercih edilen framework haline geldi. LangChain ekibi yeni agent implementasyonlarını LangGraph ile yapmayı öneriyor [^40^].

6. **Multi-agent > Single-agent**: Karmaşık görevlerde multi-agent sistemleri %90.2 daha iyi performans gösteriyor. 2026 itibarıyla kuruluşların %57'si üretimde AI agent kullanıyor [^31^].

7. **Browser automation'da accessibility tree**: Playwright'ın accessibility tree yaklaşımı, AI ajanlar için DOM parsing ve screenshot yaklaşımlarına üstün çıktı. Token verimliliği 20-50x daha iyi [^96^].

8. **Memory yönetimi kritik**: Letta/MemGPT, persistent memory ve stateful agent paradigmaları ile öne çıktı. MCP Memory server ve Neo4j Memory MCP Server, bilgi grafiği tabanlı kalıcı hafıza sunuyor [^98^] [^169^].

9. **OpenAI API standard'ı evrensel**: vLLM, Ollama, LocalAI, LM Studio, OpenLLM - hepsi OpenAI-compatible endpoint sunuyor. Bu, framework bağımsızlığını artırıyor [^166^].

10. **Ajan ticareti (A2A Commerce)**: Google'ın UCP, AP2, x402 protokolleri ile agent-to-agent ticaret altyapısı kuruluyor. AI'yi öneri sisteminden ekonomik aktöre dönüştürme [^95^].

## Controversies & Conflicting Claims

1. **Container vs MicroVM tartışması**: Docker konteynerlerin AI agent sandbox'ı olarak yeterli olup olmadığı tartışmalıdır. Bir kesim (Augment, E2B, Modal) "container yetersizdir, microVM gerekli" derken; PatchPal, Scrapling gibi araçlar Docker ile çalışmaya devam ediyor. Pratikte tehdit modeline bağlı: tek kiracılı iç ortamda Docker yeterli, çok kiracılı üretimde microVM gerekli [^113^] [^114^].

2. **MCP'nin overhead'i**: Playwright MCP server'ın ~15,000 token tool definition overhead'i, doğrudan Playwright kodu yazmayı tercih eden geliştiriciler için bir sorun. MCP'nin her kullanım senaryosu için optimal olup olmadığı tartışmalı [^96^].

3. **Framework aşırı soyutlama**: LangChain'in "heavy for simple tasks" olması ve "steeper learning curve" eleştirileri yaygın. Bazı geliştiriciler raw API çağrılarını tercih ediyor. Qwen-Agent, bu sorunu "Qwen-first, Pythonic" yaklaşımıyla çözmeye çalışıyor [^14^] [^41^].

4. **Otonom ajanların güvenilirliği**: BabyAGI, AutoGPT gibi erken otonom ajanlar "experimental" ve "not production-ready" olarak etiketleniyor. AutoGPT'nin 170K+ star'a sahip olmasına rağmen günlük kullanım için pratik olmadığı iddia ediliyor [^27^] [^36^].

5. **OpenAI vs model-agnostic framework**: OpenAI Agents SDK, OpenAI modellerine bağımlıdır. LangChain, CrewAI, AutoGen model-agnostic'tir ancak en iyi performansı genellikle belirli modellerle gösterir [^29^] [^31^].

6. **N8N gibi low-code platformların agent yetenekleri**: N8N'in AI integration'ı "stateless" ve "no autonomous planning" olarak tanımlanıyor. Gerçek ajan mimarisi için yetersiz olduğu iddia ediliyor [^99^].

## Recommended Deep-Dive Areas

1. **MCP Server Development**: Kendi MCP sunucularını yazma (TypeScript/Node.js veya Python/uvx), özel araçları standartlaştırma ve yerel/uzak transport mekanizmaları. MCP SDK kullanımı ve yetenek keşfi (capability negotiation) mekanizmaları derinlemesine incelenmeli [^122^] [^123^].

2. **vLLM ile Üretim Düzeyinde Tool Calling**: vLLM'in PagedAttention teknolojisi, paralel function calling ve OpenAI-compatible API'si, yüksek eşzamanlılıkta ajan sistemleri için kritik. Qwen2.5-Instruct, Llama 3.1/3.3, Mistral Large gibi function calling-optimize modellerle test edilmeli [^35^].

3. **Letta Memory Architecture**: Core Memory Blocks, self-editing memory, heartbeat-based looping ve "LLM-as-OS" paradigması. Letta'nın PostgreSQL + pgvector backend'i ile üretim deployment'ı. Memory tier'ları (core, archival, recall) ve context window yönetimi [^98^] [^115^].

4. **ReAct + Reflexion Pattern'lerinin Birleştirilmesi**: ReAct (real-time reasoning + acting) ile Reflexion (episode-based self-reflection) birleştirilerek daha güçlü otonom döngüler oluşturulabilir. LATS (Language Agent Tree Search) gibi ileri teknikler [^153^] [^157^].

5. **Firecracker/Kata MicroVM ile Ajan Sandbox'ı**: Docker'dan microVM'e geçişin pratik implementasyonu. E2B, Modal, AWS Lambda örnekleri. ZeroBoot'un 0.79ms boot süresi ve CoW fork yaklaşımı. Kendi sandbox altyapısını kurma rehberi [^114^] [^118^].

6. **Home Assistant + Yerel LLM Entegrasyonu**: Wyoming protocol, Assist pipeline, faster-whisper + Piper + Ollama stack. Exposed entities üzerinden güvenlik kontrolü. Conversation agent custom prompting ve context management [^72^] [^173^].

7. **Playwright MCP vs Direct Code Generation**: Accessibility tree yaklaşımının token verimliliği avantajı (~2-5KB vs 100KB+ screenshot). Stagehand caching sistemi ile maliyet optimizasyonu. dev-browser ile sandboxed automation [^96^].

8. **A2A + MCP Hybrid Mimari**: Planner agent A2A ile delegate eder, specialist agent'lar MCP ile araç çağırır. Google'ın A2A, UCP, AP2 protokol stack'i. Agent Cards ve capability discovery implementasyonu [^154^] [^158^].

9. **Qwen-Agent MCP + Code Interpreter**: Docker-sandboxed code execution, RAG with 1M+ tokens, BrowserQwen web browsing, parallel tool execution. Qwen3 ve QwQ-32B'nin native tool calling yetenekleri [^14^] [^16^].

10. **LangGraph State Management**: Graph-based state machines, checkpointing with time-travel debugging, human-in-the-loop interrupts, streaming support. Supervisor, Swarm, Trustcall ve LangMem pattern'leri [^39^] [^40^].

---

## Kaynakça

- [^14^] scrapingbee.com/blog/qwen-agent-framework/ (2026-05-06) - Qwen-Agent Guide
- [^15^] yuv.ai/blog/qwen-agent (2026-03-11) - Qwen-Agent: Native Tool Execution
- [^16^] qwenlm.github.io/Qwen-Agent/en/guide/get_started/features/ (2026-03-04) - Qwen-Agent Features
- [^17^] docs.sambanova.ai/docs/en/features/function-calling (2026-05-01) - Function Calling Implementation
- [^18^] docs.crewai.com/ (2026-01-23) - CrewAI Documentation
- [^20^] qwenlm.github.io/Qwen-Agent/en/guide/core_moduls/mcp/ (2026-03-04) - MCP in Qwen-Agent
- [^21^] medium.com/@laurentkubaski/openai-tool-schema-explained (2025-12-15) - OpenAI Tool JSON Schema
- [^22^] backslash.security/blog/what-is-mcp-model-context-protocol (2025-09-05) - What is MCP
- [^23^] developers.openai.com/api/docs/guides/function-calling (2025-08-07) - OpenAI Function Calling
- [^24^] medium.com/mitb-for-all/part-iii-lets-explore-llamaindex-events-workflows-and-agents (2025-09-09) - LlamaIndex Agents
- [^25^] galileo.ai/blog/autogen-framework-multi-agents (2025-07-25) - AutoGen Framework
- [^26^] tribe.ai/applied-ai/microsoft-autogen-orchestrating-multi-agent-llm-systems (2025-07-08) - Microsoft AutoGen
- [^27^] builtin.com/artificial-intelligence/autogpt (2025-07-23) - AutoGPT Explained
- [^28^] github.com/letta-ai/ai-memory-sdk (2025-11-04) - Letta AI Memory SDK
- [^29^] gurusup.com/blog/best-multi-agent-frameworks-2026 (2026-05-03) - Best Multi-Agent Frameworks 2026
- [^30^] home-assistant.io/integrations/openai_conversation/ (2026-04-01) - Home Assistant OpenAI
- [^31^] daily.dev/blog/complete-guide-ai-agents-developers-langchain-crewai (2026-03-23) - Complete Guide to AI Agents
- [^32^] openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared (2026-02-23) - CrewAI vs LangGraph vs AutoGen
- [^34^] docker.com/products/docker-sandboxes/ (2026-04-28) - Docker Sandboxes
- [^35^] glukhov.org/llm-hosting/comparisons/hosting-llms-ollama-localai-jan-lmstudio-vllm-comparison/ (2025-11-29) - Local LLM Comparison
- [^36^] docs.kanaries.net/articles/babyagi-chatgpt (2025-11-11) - BabyAGI Introduction
- [^37^] ibm.com/think/topics/babyagi (2025-10-20) - IBM: What is BabyAGI
- [^39^] medium.com/@yhocotw31016/building-practical-ai-agents-part-1-hands-on-langchain-2025-guide (2025-10-13) - LangChain Ecosystem 2025
- [^40^] digitalapplied.com/blog/langchain-ai-agents-guide-2025 (2025-10-22) - LangChain AI Agents 2025
- [^41^] codecademy.com/article/top-ai-agent-frameworks-in-2025 (2025-09-29) - Top AI Agent Frameworks 2025
- [^72^] joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/ (2026-04-12) - Local Voice AI for Home Assistant
- [^95^] phemex.com/academy/what-is-agent-to-agent-commerce (2026-05-05) - A2A Commerce
- [^96^] dev.to/stevengonsalvez/browser-tools-for-ai-agents-part-1-playwright-puppeteer (2026-04-26) - Browser Tools for AI Agents
- [^97^] github.com/czl9707/build-your-own-openclaw (2026-03-11) - OpenClaw Build Guide
- [^98^] medium.com/@piyush.jhamb4u/stateful-ai-agents-a-deep-dive-into-letta-memgpt-memory-models (2026-02-16) - Letta Memory Models
- [^99^] latenode.com/blog/n8n-ai-agents-2025-complete-capabilities-review (2026-02-12) - N8N AI Agents Review
- [^113^] augmentcode.com/guides/agent-execution-sandbox (2026-05-04) - Agent Execution Sandbox
- [^114^] addozhang.medium.com/ai-agent-code-execution-sandboxes-isolation-from-containers-to-microvms (2026-03-30) - Sandboxes: Containers to MicroVMs
- [^115^] railway.com/deploy/letta-ai-agent (2026-04-27) - Deploy Letta
- [^116^] team400.ai/blog/2026-03-openai-assistants-function-calling-guide (2026-03-20) - OpenAI Function Calling Migration
- [^117^] blaxel.ai/blog/code-execution-sandboxes-for-ai-agents (2026-05-01) - Code Execution Sandboxes 2026
- [^118^] northflank.com/blog/how-to-sandbox-ai-agents (2026-02-02) - Sandbox AI Agents 2026
- [^120^] arxiv.org/pdf/2405.06682 - Self-Reflection in LLM Agents
- [^122^] modelcontextprotocol.io/examples (2026-01-28) - MCP Example Servers
- [^123^] modelcontextprotocol.io/specification/2025-11-25/architecture (2025-11-25) - MCP Architecture
- [^124^] modelcontextprotocol.io/docs/learn/architecture (2025-11-25) - MCP Architecture Overview
- [^127^] sparkco.ai/blog/mastering-openai-function-calling-agents-a-2025-deep-dive (2025-10-21) - OpenAI Function Calling Deep Dive
- [^153^] arxiv.org/pdf/2303.11366 - Reflexion: Language Agents with Verbal Reinforcement
- [^154^] k21academy.com/agentic-ai/agentic-ai-protocols-comparison/ (2026-04-23) - MCP vs A2A vs ACP vs ANP
- [^155^] intuz.com/blog/mcp-vs-a2a (2026-04-13) - MCP vs A2A Comparison
- [^156^] dev.to/dev-in-progress/chat-completions-vs-openai-responses-api (2026-03-18) - Chat Completions vs Responses API
- [^157^] blogs.oracle.com/developers/what-is-the-ai-agent-loop (2026-03-16) - AI Agent Loop Architecture
- [^158^] digitalocean.com/community/tutorials/a2a-vs-mcp-ai-agent-protocols (2026-03-06) - A2A vs MCP Protocols
- [^160^] mindstudio.ai/blog/what-is-openclaw-ai-agent/ (2026-02-23) - What is OpenClaw
- [^166^] karthikeyanrathinam.medium.com/no-internet-no-problem-create-your-own-ai-assistant-with-local-llm-20-frameworks-2026 (2026-03-25) - 20 Local LLM Frameworks
- [^167^] brightdata.com/blog/ai/best-ai-agent-frameworks (2026-04-19) - Top 14 AI Agent Frameworks
- [^168^] mcpservers.org/servers/deanacus/knowledge-graph-mcp - Knowledge Graph Memory Server
- [^169^] medium.com/@_jalakoo_/neo4js-memory-mcp-server-for-persistent-ai-chat-memory (2025-08-06) - Neo4j Memory MCP Server
- [^170^] github.com/kaushikb11/awesome-llm-agents (2026-05-04) - Awesome LLM Agents
- [^171^] fast.io/resources/best-local-llm-runners-agents/ (2026-02-18) - Best Local LLM Runners
- [^173^] theawesomegarage.com/blog/configure-a-local-llm-to-control-home-assistant-instead-of-chatgpt (2024-05-26) - Home Assistant Local LLM
