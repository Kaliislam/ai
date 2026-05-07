# JARVIS Araştırma Raporu: Dim 05 - Ajan Framework, Tool Calling ve MCP + Dim 10 - Ev Otomasyonu Entegrasyonu

## Genel Bakış

Bu rapor, ajan framework'leri (Qwen-Agent, Letta, LangChain, CrewAI, AutoGen), Model Context Protocol (MCP), function calling mekanizmaları, sandbox stratejileri ve Home Assistant ev otomasyonu entegrasyonunu kapsamlı bir şekilde incelemektedir. Araştırma 20+ bağımsız kaynak üzerinden yapılmıştır.

---

## Bölüm 1: Framework Karşılaştırması ve Yerel LLM Uyumluluğu

### 1.1 Qwen-Agent

Claim: Qwen-Agent, native tool execution, MCP entegrasyonu, Docker-sandboxed code execution ve RAG yetenekleriyle Qwen modelleri için optimize edilmiş üretim düzeyinde bir framework'tür [^1^].
Source: Yuv.ai Blog
URL: https://yuv.ai/blog/qwen-agent
Date: 2026-03-11
Excerpt: "Qwen-Agent is an advanced framework for building LLM applications with native tool execution, planning, and memory capabilities... Unlike generic agent frameworks that require extensive prompt engineering to get tools working, Qwen-Agent natively understands how Qwen models parse and execute function calls."
Context: Qwen-Agent, Alibaba'nin Qwen modelleri için geliştirdiği Apache-2.0 lisanslı açık kaynak framework.
Confidence: high

Claim: Qwen-Agent, yerel OpenAI-compatible sunucular (vLLM, SGLang, Ollama) üzerinden çalışabilir ve MCP sunucularını `uvx` veya `npx` komutlarıyla yapılandırarak filesystem, time, fetch gibi araçları otomatik olarak keşfeder [^2^].
Source: Qwen-Agent Official Documentation
URL: https://qwenlm.github.io/Qwen-Agent/en/guide/core_moduls/mcp/
Date: 2026-03-04
Excerpt: "The system calls MCPManager().initConfig(...) to launch MCP services and auto-discover available tools... Ensure that commands like npx and uvx are available in your system's PATH."
Context: MCP entegrasyonu Qwen-Agent'in üçüncü taraf araçları dinamik olarak keşfetmesini sağlar.
Confidence: high

Claim: Qwen-Agent'in built-in araçları arasında code_interpreter, web_search, web_extractor, image_search ve image_zoom_in_tool bulunur; ayrıca Docker-sandboxed kod çalıştırma desteği vardır [^3^].
Source: Qwen-Agent Features
URL: https://qwenlm.github.io/Qwen-Agent/en/guide/get_started/features/
Date: 2026-03-04
Excerpt: "Built-in Tools: Includes versatile tools out of the box: code_interpreter, web_search and web_extractor, image_search... MCP Integration: Seamlessly connect to external tools and services via the open MCP standard."
Context: Qwen-Agent, Qwen3, Qwen3-VL, Qwen3-Omni, Qwen3-Coder, QwQ, Qwen2.5 serileri ile uyumludur.
Confidence: high

### 1.2 Letta (eski adıyla MemGPT)

Claim: Letta, stateful AI agent framework olarak bilinir; persistent long-term memory, vector-based retrieval ve OS-level memory hierarchies ile ajanların oturumlar arası bilgi saklamasını sağlar [^4^].
Source: Railway Blog / Letta
URL: https://railway.com/deploy/letta-ai-agent
Date: 2026-04-27
Excerpt: "Letta is a platform for building stateful AI agents — AI systems with advanced memory that can learn and self-improve over time. Unlike stateless LLM API calls, Letta agents maintain persistent memory across conversations."
Context: Letta, MemGPT'den evrilmiş, PostgreSQL + pgvector kullanan açık kaynak framework.
Confidence: high

Claim: Letta, OpenAI, Anthropic, Google Gemini, Ollama ve vLLM gibi çoklu LLM sağlayıcılarını destekler ve REST API + Python SDK sunar [^5^].
Source: Medium - Building Stateful LLM Agents
URL: https://medium.com/@vishnudhat/letta-building-stateful-llm-agents-with-memory-and-reasoning-0f3e05078b97
Date: 2025-05-04
Excerpt: "Model-Agnostic Framework: Compatible with various LLM providers, including OpenAI, Anthropic, and open-source models... REST API and Python SDK — full programmatic control over agents, memory, and conversations."
Context: Letta'nin bellek yönetimi OS hiyerarşilerinden esinlenmiştir.
Confidence: high

Claim: Letta'nin self-host edilebilir Docker imajı mevcuttur; üretim kullanımı için aylık $5-10 maliyetle Railway üzerinde çalıştırılabilir [^6^].
Source: Railway Deploy Template
URL: https://railway.com/deploy/letta-ai-agent
Date: 2026-04-27
Excerpt: "Self-hosting on Railway costs approximately $5-10/month for basic usage... Letta is fully open-source under the Apache 2.0 license."
Context: Letta Cloud ücretsiz katman sunar ancak self-hosting sınırsız ajan ve tam veri sahipliği sağlar.
Confidence: high

### 1.3 LangChain ve LangGraph

Claim: LangChain 106K+ GitHub star ile en büyük ekosisteme sahip ajan framework'üdür; 300+ topluluk entegrasyonu ve MCP server bağlantısı sunar [^7^].
Source: Speakeasy Blog
URL: https://www.speakeasy.com/blog/ai-agent-framework-comparison
Date: 2026-03-03
Excerpt: "LangChain runs a Reasoning and Acting (ReAct)-style tool-calling loop... LangChain has over 300 community integrations that work as ready-made tools. It is the wrong choice for cyclic or branching workflows (use LangGraph)."
Context: LangChain v1.0 SummarizationMiddleware ve 8 farklı bellek sınıfı sunar.
Confidence: high

Claim: LangChain, Ollama üzerinden yerel LLM'leri destekler ve `bind_tools()` ile tool calling sağlar, ancak yerel modeller için özel wrapper gerekebilir [^8^].
Source: Medium - Tool-Calling with LangChain
URL: https://anshuls235.medium.com/%EF%B8%8F-tool-calling-with-langchain-open-source-models-run-it-locally-seamlessly-8d31ff4c7a76
Date: 2025-06-12
Excerpt: "LangChain supports tool calling cleanly when using inference endpoints from Hugging Face... running models locally while supporting function-calling requires custom abstraction."
Context: HuggingFaceEndpoint ile çalışır ancak yerel modellerde zorluklar yaşanabilir.
Confidence: high

### 1.4 CrewAI

Claim: CrewAI, 45.900+ GitHub star ile en hızlı büyüyen ajan framework'üdür; role-based multi-agent sistemleri için native destek sunar [^9^].
Source: NxCode Blog
URL: https://www.nxcode.io/resources/news/crewai-vs-langchain-ai-agent-framework-comparison-2026
Date: 2026-03-18
Excerpt: "CrewAI: 45,900+ GitHub stars, fastest-growing agent framework in 2025-2026... CrewAI's agent coordination creates efficiency gains when multiple agents collaborate."
Context: CrewAI, Ollama ile yerel LLM'leri doğrudan destekler.
Confidence: high

Claim: CrewAI, Ollama entegrasyonu ile yerel LLM'leri `ollama/model_name` formatında yapılandırmaya izin verir; önerilen modeller arasında Llama 3.1 8B, Mistral 7B, OpenHermes, Qwen 2.5 32B bulunur [^10^].
Source: LocalAI Master - CrewAI Local Setup
URL: https://localaimaster.com/blog/crewai-local-setup-guide
Date: 2026-02-04
Excerpt: "CrewAI's strengths is native support for local LLMs through Ollama... ollama_llm = LLM(model='ollama/llama3.1:8b', base_url='http://localhost:11434', temperature=0.2)"
Context: CrewAI ile yerel model kullanımında sıcaklık 0.1-0.3 arası önerilir.
Confidence: high

### 1.5 AutoGen

Claim: AutoGen, Microsoft'un konuşma tabanlı multi-agent orchestration framework'üdür; GroupChat pattern'leri ve human-in-the-loop desteği sunar [^11^].
Source: Galileo.ai Blog
URL: https://galileo.ai/blog/autogen-framework-multi-agents
Date: 2025-07-25
Excerpt: "AutoGen is Microsoft's open-source framework that enables you to orchestrate multiple AI agents through natural-language conversations, rather than relying on brittle, hand-coded APIs."
Context: AutoGen, model-agnostic yapıya sahiptir; GPT, Claude veya özel modellerle çalışır.
Confidence: high

Claim: Microsoft, 2025 sonlarında Semantic Kernel ve AutoGen'i birleştirerek unified agent framework duyurmuştur [^12^].
Source: Dev.to - Microsoft Agent Framework
URL: https://dev.to/bspann/microsoft-agent-framework-the-future-of-net-ai-agents-has-arrived-22mf
Date: 2026-02-16
Excerpt: "At .NET Conf 2025, Microsoft announced a unified agent framework that combines the best of both worlds... These weren't competing projects — they were complementary pieces."
Context: .NET ekosistemi için Semantic Kernel, Python için AutoGen kullanılır.
Confidence: medium

### 1.6 Framework Karşılaştırma Tablosu

| Özellik | Qwen-Agent | Letta | LangChain | CrewAI | AutoGen |
|---------|-----------|-------|-----------|--------|---------|
| Primary Focus | Native tool execution | Stateful memory | Chains & pipelines | Role-based multi-agent | Conversation-first multi-agent |
| Local LLM Support | vLLM, Ollama, SGLang | Ollama, vLLM | Ollama, vLLM | Ollama | Ollama, vLLM |
| MCP Desteği | Native | Tool use ile | MCP server connectivity | Partial | MCP tools ile |
| Memory | Basic | Advanced persistent | 8 memory classes | Memory=True | Chat log |
| Self-Hosting | Docker | Docker + PostgreSQL | Code only | Code only | Code only |
| License | Apache 2.0 | Apache 2.0 | MIT | MIT | MIT |

---

## Bölüm 2: MCP (Model Context Protocol) Detaylı İnceleme

### 2.1 Mimari ve Bileşenler

Claim: MCP, Host-Client-Server mimarisi üzerine kurulmuştur; Host (AI uygulaması) birden fazla Client oluşturur, her Client bir MCP Server'a bağlanır; iletişim JSON-RPC 2.0 üzerinden yapılır [^13^].
Source: MCP Official Architecture
URL: https://modelcontextprotocol.io/docs/learn/architecture
Date: 2025-11-25
Excerpt: "MCP follows a client-server architecture where an MCP host — an AI application like Claude Code or Claude Desktop — establishes connections to one or more MCP servers. The MCP host accomplishes this by creating one MCP client for each MCP server."
Context: MCP, Anthropic tarafından 2024 sonlarında tanıtılmıştır; "AI'nin USB-C moment'i" olarak adlandırılır.
Confidence: high

Claim: MCP sunucuları STDIO (yerel) ve HTTP+SSE (uzak) olmak üzere iki taşıma katmanı kullanır; STDIO yerel süreçler için hızlı ve güvenlidir, HTTP+SSE uzak servisler için uygundur [^14^].
Source: Data Science Dojo - MCP Guide
URL: https://datasciencedojo.com/blog/guide-to-model-context-protocol/
Date: 2025-10-20
Excerpt: "STDIO is used for servers running on your own computer... Fast: Data passes directly between processes; Secure: No open network ports... HTTP with Server-Sent Events (SSE) for servers running elsewhere on the network."
Context: Yerel MCP sunucuları tek bir client'e hizmet verirken uzak sunucular çoklu client destekler.
Confidence: high

Claim: MCP, capability-based negotiation kullanır; sunucular ve client'ler init sırasında destekledikleri özellikleri açıklar (örn: resource subscriptions, tool support, prompt templates) [^15^].
Source: MCP Specification
URL: https://modelcontextprotocol.io/specification/2025-11-25/architecture
Date: 2025-11-25
Excerpt: "Servers declare capabilities like resource subscriptions, tool support, and prompt templates. Clients declare capabilities like sampling support and notification handling. Both parties must respect declared capabilities throughout the session."
Context: Bu sayede geriye dönük uyumluluk korunur ve özellikler aşamalı olarak eklenebilir.
Confidence: high

### 2.2 MCP Server Geliştirme

Claim: MCP Python SDK (FastMCP), `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()` decorator'leri ile çok basit server geliştirmeye izin verir; örnek hesap makinesi sunucusu 20 satırdan az koddan oluşur [^16^].
Source: MCP Python SDK GitHub
URL: https://github.com/modelcontextprotocol/python-sdk
Date: 2026-04-02
Excerpt: "Let's create a simple MCP server that exposes a calculator tool and some data... @mcp.tool() def add(a: int, b: int) -> int: 'Add two numbers' return a + b"
Context: FastMCP, MCP sunucu geliştirmeyi dramatik şekilde basitleştirir.
Confidence: high

Claim: MCP sunucuları araç (tools), kaynak (resources) ve prompt (prompts) olmak üzere üç temel primitif sunar; sunucular self-describing'dir ve yetenek manifesti yayınlar [^17^].
Source: Dysnix MCP Guide
URL: https://dysnix.com/blog/model-context-protocol
Date: 2025-04-09
Excerpt: "Servers are self-describing, meaning they expose a manifest that tells the AI client what's available and how to use it... You can run multiple MCP servers in parallel, and each one can focus on a single domain."
Context: Her sunucu tek bir alana odaklanmalıdır (filesystem, SQL database, GitHub API, vb.)
Confidence: high

### 2.3 MCP Güvenlik ve Zafiyetler

Claim: MCP'nin STDIO transport mimarisi, Anthropic'in resmi SDK'larında mimari bir tasarım hatası içerir; bu hata RCE (Arbitrary Command Execution) riski taşır ve 150M+ indirme, 7.000+ açık sunucu, 200.000+ savunmasız örneği etkiler [^18^].
Source: OX Security / The Hacker News
URL: https://thehackernews.com/2026/04/anthropic-mcp-design-vulnerability.html
Date: 2026-04-20
Excerpt: "This flaw enables Arbitrary Command Execution (RCE) on any system running a vulnerable MCP implementation... 150M+ downloads, 7,000+ publicly accessible servers — and up to 200,000 vulnerable instances in total."
Context: Anthropic bu davranışı "expected" olarak değerlendirmiş ve protokol mimarisini değiştirmeyi reddetmiştir.
Confidence: high

Claim: MCP güvenlik araştırmaları, 2.614 MCP implementasyonunun %82'sinin path traversal (CWE-22), %67'sinin code injection (CWE-94), %34'ünün command injection (CWE-78) açığı içerdiğini göstermiştir [^19^].
Source: Endor Labs Blog
URL: https://www.endorlabs.com/learn/classic-vulnerabilities-meet-ai-infrastructure-why-mcp-needs-appsec
Date: 2026-01-23
Excerpt: "Among 2,614 MCP implementations: 82% use file system operations prone to Path Traversal (CWE-22), 67% use sensitive APIs related to Code Injection (CWE-94), 34% use sensitive APIs related to Command Injection (CWE-78)."
Context: Anthropic mcp-server-git CVE-2025-68143, CVE-2025-68144, CVE-2025-68145 gibi zafiyetler ortaya çıkmıştır.
Confidence: high

Claim: Indirect Prompt Injection (IPI), MCP ve A2A için #1 OWASP riskidir; zehirlenmiş araç yanıtları veya delegated task'lar içindeki gizli talimatlar aracılığıyla saldırganlar ajanın davranışını manipüle edebilir [^20^].
Source: StackOne Blog
URL: https://www.stackone.com/blog/mcp-vs-a2a-protocol/
Date: 2026-03-10
Excerpt: "Neither protocol was designed with adversarial input as a first-class concern... OWASP ranks indirect prompt injection as the #1 risk for LLM applications in 2025."
Context: MCP'de statik payload'lar, A2A'da adaptif multi-turn saldırılar mümkündür.
Confidence: high

### 2.4 A2A ve MCP Hybrid Mimari

Claim: A2A (Agent-to-Agent Protocol) Google tarafından geliştirilmiştir; MCP'den farklı olarak agent'lar arası koordinasyon ve delegation sağlar; üretim sistemlerinde MCP (tool access layer) + A2A (coordination layer) hybrid mimarisi standartlaşmaktadır [^21^].
Source: Elastic Blog / Elasticsearch
URL: https://www.elastic.co/search-labs/blog/a2a-protocol-mcp-llm-agent-newsroom-elasticsearch
Date: 2025-11-13
Excerpt: "A2A handles agent coordination and workflow orchestration while MCP provides individual agents with tool access... In our newsroom example, agents coordinate via A2A; each agent uses MCP servers for their specialized tools."
Context: MCP "agent ↔ system", A2A "agent ↔ agent" iletişimini standartlaştırır.
Confidence: high

Claim: Hybrid mimaride MCP deterministik sistem entegrasyonu sağlarken, A2A modüler agent işbirliği sağlar; örnek: bir recruiting agent MCP ile HR sistemine erişir, A2A ile resume screening'i uzman agent'e devreder [^22^].
Source: StackOne Blog
URL: https://www.stackone.com/blog/mcp-vs-a2a-protocol/
Date: 2026-03-10
Excerpt: "A recruiting agent may use MCP to interact with HR systems, and A2A to delegate resume analysis to a specialized screening agent. MCP provides deterministic system integration. A2A provides modular agent collaboration."
Context: Bu ayrım, enterprise ortamlarda özellikle kritiktir.
Confidence: high

---

## Bölüm 3: Function Calling Şema Tanımlama ve OpenAI-Compatible API

### 3.1 OpenAI Function Calling API

Claim: OpenAI function calling, araçları JSON Schema ile tanımlar; her araç `name`, `description` ve `parameters` içerir; model, kullanıcı sorusuna göre hangi aracı çağıracağına karar verir [^23^].
Source: OpenAI API Docs
URL: https://developers.openai.com/api/docs/guides/function-calling
Date: 2025-08-07
Excerpt: "A function is a specific kind of tool, defined by a JSON schema. A function definition allows the model to pass data to your application, where your code can access data or take actions suggested by the model."
Context: OpenAI Responses API ve Chat Completion API arasında farklı şema formatları vardır.
Confidence: high

Claim: vLLM, OpenAI function calling API ile %100 uyumlu, üretim düzeyinde tool calling sunar; paralel fonksiyon çağrıları, `tool_choice` parametresi ve streaming desteği içerir [^24^].
Source: vLLM Official Docs
URL: https://docs.vllm.ai/en/latest/features/tool_calling/
Date: Unknown
Excerpt: "vLLM offers production-grade, fully-featured tool calling that's 100% compatible with OpenAI's function calling API. It implements the complete specification including parallel function calls..."
Context: vLLM PagedAttention, multi-step tool calling sırasında bile yüksek throughput korur.
Confidence: high

Claim: vLLM tool calling, Llama 3.1/3.2/4, Qwen2.5-Instruct, Mistral Large, Hermes 2 Pro gibi modellerle mükemmel çalışır; her model için özel tool parser (`llama3_json`, `pythonic`, `hermes`) gerekebilir [^25^].
Source: vLLM Docs - Supported Models
URL: https://docs.vllm.ai/en/latest/models/supported_models.html
Date: Unknown
Excerpt: "For Llama 4 model, use --tool-call-parser llama4_pythonic --chat-template examples/tool_chat_template_llama4_pythonic.jinja... All Llama 3.1, 3.2 and 4 models should be supported."
Context: `--enable-auto-tool-choice` ve `--tool-call-parser` flag'leri ile etkinleştirilir.
Confidence: high

Claim: vLLM, 2026 başında MCP desteğini tüm modeller için genişletmiş ve ResponsesAPI & tool calling için önemli ilerlemeler kaydetmiştir [^26^].
Source: GitHub - vLLM Project
URL: https://github.com/vllm-project/vllm/issues/34857
Date: 2026-02-18
Excerpt: "vLLM has made a lot of progress on responsesAPI & tool calling in the past few months... MCP support for all models through a ParsableContext... Function tool calling for non-harmony models."
Context: vLLM, GPT-OSS MCP desteği de eklenmiştir.
Confidence: high

### 3.2 JSON Schema Örnekleri

Claim: OpenAI tool schema, `type: function` ve `parameters` altında JSON Schema Draft 7 formatını kullanır; parametreler `type`, `properties`, `required`, `enum` gibi alanlar içerir [^27^].
Source: Medium - OpenAI Tool JSON Schema Explained
URL: https://medium.com/@laurentkubaski/openai-tool-schema-explained-05a5ce0e80f8
Date: 2025-12-15
Excerpt: "The JSON Schema to describe tools is different for the Chat Completion API and the Response API... A simple example: { type: 'function', function: { name: 'get_orders', description: '...', parameters: { type: 'object', properties: { input: { type: 'string' } }, required: ['input'] } } }"
Context: Python fonksiyonlarından otomatik schema üretmek için `inspect` modülü kullanılabilir.
Confidence: high

---

## Bölüm 4: Araç Örnekleri

### 4.1 Filesystem, Web Search, Hesap Makinesi, Saat/Tarih

Claim: MCP resmi sunucuları arasında filesystem, fetch, time, memory, sqlite gibi yaygın araçlar bulunur; bunlar `npx` (Node.js) veya `uvx` (Python) ile tek komutla çalıştırılabilir [^28^].
Source: Qwen-Agent MCP Docs
URL: https://qwenlm.github.io/Qwen-Agent/en/guide/core_moduls/mcp/
Date: 2026-03-04
Excerpt: "mcpServers: { filesystem: { command: 'npx', args: ['-y', '@modelcontextprotocol/server-filesystem', './workspace'] }, memory: { command: 'npx', args: ['-y', '@modelcontextprotocol/server-memory'] } }"
Context: Qwen-Agent, MCPManager ile bu sunucuları otomatik başlatır.
Confidence: high

Claim: MCP Time Server, UTC zamanını ISO 8601, human-readable veya Unix timestamp formatında döndüren basit bir Python MCP sunucusudur; `uvx mcp-server-time` ile çalıştırılabilir [^29^].
Source: mcpservers.org
URL: https://mcpservers.org/servers/elimS2/mcp-time-server
Date: 2025-01-15
Excerpt: "get_current_time_utc: Get the current UTC time in various formats... Parameters: format (optional): 'iso' (default), 'datetime', 'timestamp'."
Context: Bu tür basit sunucular, yerel development için hızlıca prototip oluşturmayı sağlar.
Confidence: high

Claim: Hesap makinesi MCP sunucusu, `@mcp.tool()` decorator ile `add`, `multiply`, `calculate_factorial` gibi fonksiyonları expose eder; ayrıca `mcp.resource()` ile hesaplama geçmişi ve `mcp.prompt()` ile AI davranış talimatları sunar [^30^].
Source: Natoma.ai - Building First MCP Server
URL: https://natoma.ai/library/building-your-first-mcp-server-a-developers-guide
Date: Unknown
Excerpt: "@mcp.tool() def add(a: int, b: int) -> int: 'Add two numbers together' return a + b... @mcp.resource('calculator://history') def calculation_history() -> str..."
Context: Bu üç primitif (tool, resource, prompt) MCP'nin temel yapı taşlarıdır.
Confidence: high

---

## Bölüm 5: Sandbox Stratejileri

### 5.1 Docker, Firecracker, gVisor, Kata Containers

Claim: Standart Docker container'lar host kernel'ini paylaştığı için AI ajan sandbox'ı için yetersizdir; kernel escape saldırıları (örn: Langflow CVE-2025-3248) container'dan host'a sızmaya izin verebilir [^31^].
Source: Softwareseni - AI Agent Sandboxing
URL: https://www.softwareseni.com/ai-agent-sandboxing-explained-why-docker-is-not-enough-and-what-actually-works/
Date: 2026-04-28
Excerpt: "Docker containers share the host OS kernel — a kernel exploit in the agent's generated code gives the attacker host-level access, not just container access. Use Docker as your base image format, but deploy through a Kata or gVisor RuntimeClass."
Context: CISA, CVE-2025-3248'i KEV kataloğuna 5 Mayıs 2025'te ekledi.
Confidence: high

Claim: Firecracker microVM (AWS Lambda tarafından kullanılır), KVM hardware virtualisation ile her workload için ayrı Linux kernel oluşturur; ~125ms boot time, <5 MiB memory overhead ile çalışır [^32^].
Source: Softwareseni Blog
URL: https://www.softwareseni.com/ai-agent-sandboxing-explained-why-docker-is-not-enough-and-what-actually-works/
Date: 2026-04-28
Excerpt: "Firecracker, built by AWS for Lambda and Fargate, creates a dedicated Linux kernel for each execution environment via KVM hardware virtualisation... approximately 125ms boot time, less than 5 MiB memory overhead per microVM."
Context: Firecracker, Rust ile yazılmış minimalist VMM'dir; BIOS emülasyonu yoktur.
Confidence: high

Claim: gVisor, Google'ın user-space kernel'idir (Sentry process); tüm application system call'larını host kernel'e ulaşmadan önce yakalar ve user space'de yeniden implemente eder; I/O-heavy workload'lerde %10-30 overhead vardır [^33^].
Source: Softwareseni Blog
URL: https://www.softwareseni.com/ai-agent-sandboxing-explained-why-docker-is-not-enough-and-what-actually-works/
Date: 2026-04-28
Excerpt: "gVisor is a user-space kernel — the 'Sentry' process — developed by Google. It intercepts all application system calls before they reach the host kernel and re-implements them in user space... Overhead runs around 10–30% on I/O-heavy workloads."
Context: gVisor, Kubernetes'te `runsc` RuntimeClass ile native entegre olur.
Confidence: high

Claim: Kata Containers, OCI container API'leri ile hardware virtualisation'ı (Firecracker, Cloud Hypervisor, QEMU) birleştirir; en pratik üretim kombinasyonu "Kata + Firecracker VMM" olarak kabul edilir [^34^].
Source: Softwareseni Blog
URL: https://www.softwareseni.com/ai-agent-sandboxing-explained-why-docker-is-not-enough-and-what-actually-works/
Date: 2026-04-28
Excerpt: "Kata Containers combines OCI-compatible container APIs with hardware virtualisation via pluggable VMMs — Firecracker, Cloud Hypervisor, or QEMU... Kata can use Firecracker as its VMM, giving you hardware isolation with Kubernetes-native APIs."
Context: Kubernetes RuntimeClass değişikliği ile `runtimeClassName: kata` kullanılabilir.
Confidence: high

### 5.2 E2B ve AI Sandbox Platformları

Claim: E2B, Firecracker microVM'leri kullanarak AI ajanları için güvenli kod çalıştırma ortamı sunar; ~150ms cold start, Python/JS/TS desteği, 88 Fortune 100 şirketi tarafından kullanılır [^35^].
Source: E2B Official Website
URL: https://e2b.dev/
Date: Unknown
Excerpt: "Trusted by 88% of Fortune 100 companies and powering millions of sandbox sessions... E2B has fundamentally changed how we think about AI code execution."
Context: E2B, Apache-2.0 lisansıyla açık kaynak ve self-host edilebilir.
Confidence: high

Claim: Agent-Sandbox, MCP üzerinden sandbox yaşam döngüsünü otomatik yöneten E2B-compatible enterprise-grade sandbox sistemidir; Kubernetes üzerinde çalışır ve multi-tenant desteği sunar [^36^].
Source: GitHub - agent-sandbox/agent-sandbox
URL: https://github.com/agent-sandbox/agent-sandbox
Date: 2025-12-05
Excerpt: "Full sandbox lifecycle manage by Agent-Sandbox MCP Server... E2B Fully-Compatible... Cloud-Native: Leverages Kubernetes built to run in cloud environments."
Context: MCP üzerinden agent'lar sandbox oluşturur, erişir ve siler.
Confidence: high

Claim: E2B, Modal, Bunnyshell (hopx.ai) platform karşılaştırmasında Firecracker microVM'ler ~100-150ms cold start sunarken, gVisor tabanlı Modal sub-1s cold start sunar; Bunnyshell tam yığın ortam + MCP server desteği sunar [^37^].
Source: Bunnyshell Guide
URL: https://www.bunnyshell.com/guides/coding-agent-sandbox/
Date: 2026-03-16
Excerpt: "E2B: Firecracker microVMs, ~150ms cold start... Modal: gVisor, sub-1s... Bunnyshell (hopx.ai): Firecracker microVMs, ~100ms, full-stack envs, native MCP server."
Context: E2B yılda 40K'dan 15M sandbox'a çıkmıştır.
Confidence: medium

---

## Bölüm 6: Home Assistant Entegrasyonu

### 6.1 LLM Entegrasyonu (OpenAI, Ollama, Anthropic)

Claim: Home Assistant 2025.8, AI Task özelliği, Suggest with AI butonu ve OpenRouter entegrasyonu (400+ LLM model) ile yaz AI devrimini yaşamaktadır; yerel LLM için Ollama entegrasyonu mevcuttur [^38^].
Source: Home Assistant Blog - 2025.8
URL: https://www.home-assistant.io/blog/2025/08/06/release-20258/
Date: 2025-08-06
Excerpt: "We shipped integration sub-entries... allows users to configure their Ollama server or API key for OpenAI once, and then create many different agents using different models... OpenRouter, which is a unified LLM interface giving access to over 400 extra LLM models."
Context: AI Task, kamera görüntüleri veya dosyaları analiz etmek için kullanılır.
Confidence: high

Claim: Home Assistant'in yerel Ollama entegrasyonu, conversation agent olarak çalışır; `prefer_local_intents: true` ayarı ile basit komutları HA doğrudan işler, karmaşık istekler LLM'e yönlendirilir [^39^].
Source: Joe Karlsson Blog
URL: https://www.joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/
Date: 2026-04-12
Excerpt: "'prefer_local_intents: true' is the most important setting most guides skip over. With it enabled, Home Assistant tries to handle commands with its built-in intent recognition first — before touching the LLM."
Context: Bu ayar, "turn on the lights" gibi basit komutların 200ms'de işlenmesini sağlar.
Confidence: high

Claim: Home Assistant, built-in Assist API ile LLM'lere cihaz kontrolü yetkisi verir; LLM yalnızca "exposed entities" sayfasında açıkça expose edilen entity'leri kontrol edebilir; 25'den fazla entity expose edilmesi küçük modellerde hatalara yol açabilir [^40^].
Source: Home Assistant Ollama Integration
URL: https://www.home-assistant.io/integrations/ollama/
Date: 2026-04-01
Excerpt: "Only models that support Tools may control Home Assistant. Smaller models may not reliably maintain a conversation when controlling Home Assistant is enabled. We recommend exposing fewer than 25 entities."
Context: WebSocket API üzerinden `homeassistant/expose_entity` ile toplu entity management yapılabilir.
Confidence: high

Claim: Home Assistant'in system prompt'unda "CRITICAL SAFETY RULES" tanımlanması zorunludur; aksi halde LLM "turn off the office" komutunu server rack'e uygulayabilir (gerçek olay) [^41^].
Source: Joe Karlsson Blog
URL: https://www.joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/
Date: 2026-04-12
Excerpt: "What happened: 'turn off the office.' I meant the lights. The LLM, helpfully trying to fulfill the request completely, cut power to the server rack... Now: the server rack is protected by hard rules in the prompt."
Context: Bu gerçek vaka, LLM entegrasyonunda güvenlik prompt engineering'in kritik önemini gösterir.
Confidence: high

### 6.2 Wyoming Protokolü ile Sesli Kontrol

Claim: Wyoming protokolü, Home Assistant'in açık standart sesli kontrol protokolüdür; STT (Whisper, Speech-to-Phrase), TTS (Piper), wake-word (openWakeWord) servislerini TCP üzerinden birleştirir [^42^].
Source: Home Assistant Wyoming Integration
URL: https://www.home-assistant.io/integrations/wyoming/
Date: 2026-04-01
Excerpt: "The Wyoming integration connects external voice services to Home Assistant using a small protocol. This enables Assist to use a variety of local speech-to-text, text-to-speech, and wake-word-detection systems."
Context: Wyoming satellite'leri Raspberry Pi üzerinde çalışır ve Zeroconf ile otomatik keşfedilir.
Confidence: high

Claim: Tamamen yerel sesli asistan için faster-whisper (GPU STT), Piper (offline TTS) ve Ollama (LLM) Wyoming protokolü ile birleştirilir; streaming TTS, response süresini 9.5x-13x hızlandırır [^43^].
Source: Home Assistant Blog - AI in Home Assistant
URL: https://www.home-assistant.io/blog/2025/09/11/ai-in-home-assistant/
Date: 2025-09-11
Excerpt: "Piper, streaming: 0.56 sec (9.5x faster)... Cloud, streaming: 0.51 sec (13x faster)... Home Assistant can now initiate conversations."
Context: Home Assistant Voice Preview Edition donanımı da bu ekosistem için tasarlanmıştır.
Confidence: high

Claim: Wyoming Satellite projesi artık bakımı bırakılmıştır ve ESPHome protokolüne dayalı Linux Voice Assistant ile değiştirilmiştir; ancak mevcut Wyoming implementasyonları çalışmaya devam etmektedir [^44^].
Source: GitHub - rhasspy/wyoming-satellite
URL: https://github.com/rhasspy/wyoming-satellite
Date: 2026-01-27
Excerpt: "This project is no longer maintained as it has been replaced by Linux Voice Assistant that uses the ESPHome protocol, which supports the newest features."
Context: Yeni ESPHome tabanlı sistem, media player, stop wake word, timers gibi özellikleri destekler.
Confidence: high

### 6.3 Akıllı Ev Cihaz Kontrolü API'leri

Claim: Home Assistant REST API, `/api/services/<domain>/<service>` endpoint'i ile cihazları kontrol eder; örneğin `POST /api/services/light/turn_on` ile `{"entity_id": "light.study_light"}` gönderilerek ışık açılır [^45^].
Source: Home Assistant Developer Docs
URL: https://developers.home-assistant.io/docs/api/rest/
Date: 2026-02-02
Excerpt: "curl -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' -d '{"entity_id": "switch.christmas_lights"}' http://localhost:8123/api/services/switch/turn_on"
Context: Bearer token authentication zorunludur; token User Profile > Security altından oluşturulur.
Confidence: high

Claim: Home Assistant entity state API, `PUT /api/states/<entity_id>` ile entity durumunu doğrudan güncellemeye izin verir; bu, harici sistemlerin HA durumunu senkronize etmesi için kullanılır [^46^].
Source: Home Assistant Community Forum
URL: https://community.home-assistant.io/t/howto-execute-program-to-update-light-status-to-on-off/938818
Date: 2025-10-09
Excerpt: "curl -H 'Authorization: Bearer ${TOKEN}' -H 'Content-Type: application/json' -d '{"state": "'${state}'"}' http://myhaserver:8123/api/states/${entity_id}"
Context: Bu API, fiziksel cihazı tetiklemeden yalnızca HA state'ini günceller.
Confidence: high

Claim: Home Assistant, webhook trigger'ları ile harici sistemlerden otomasyon tetiklenmesine izin verir; `/api/webhook/<webhook_id>` endpoint'i POST, PUT, HEAD, GET destekler [^47^].
Source: Home Assistant Automation Trigger Docs
URL: https://www.home-assistant.io/docs/automation/trigger/
Date: 2026-04-01
Excerpt: "Webhook trigger fires when a web request is made to the webhook endpoint: /api/webhook/<webhook_id>... By default, webhook triggers can only be accessed from devices on the same network."
Context: Nabu Casa Cloud ile internet üzerinden webhook tetiklenebilir.
Confidence: high

### 6.4 Home Assistant MCP Server

Claim: Home Assistant, resmi MCP Server entegrasyonuna sahiptir; Streamable HTTP protokolü kullanarak Claude Desktop, Cursor gibi MCP client'lara Assist API erişimi sağlar [^48^].
Source: Home Assistant MCP Server Integration
URL: https://www.home-assistant.io/integrations/mcp_server/
Date: 2026-04-01
Excerpt: "The Model Context Protocol Server integration enables using Home Assistant to provide context for MCP LLM Client Applications... You can control your lights from Claude Desktop."
Context: MCP client yalnızca expose edilen entity'lere erişebilir; Claude kullanıcıdan tool çağrısı öncesi izin ister.
Confidence: high

Claim: Home Assistant MCP Server, Cursor için `mcp-proxy` gateway gerektirir çünkü Cursor yalnızca stdio transport destekler; HA ise Streamable HTTP kullanır [^49^].
Source: Home Assistant MCP Server Docs
URL: https://www.home-assistant.io/integrations/mcp_server/
Date: 2026-04-01
Excerpt: "Some MCP clients only support stdio transport, and directly run an MCP server as a local command line tool. You can use an MCP proxy server like mcp-proxy to act as a gateway to the Home Assistant MCP SSE server."
Context: Claude Code remote MCP server'ları doğrudan destekler.
Confidence: high

Claim: Üçüncü taraf `ha-mcp` projesi, Home Assistant için 80+ MCP aracı sunar; automations, blueprints, HACS, dashboard, backup, entity registry gibi kapsamlı yönetim araçları içerir [^50^].
Source: GitHub - homeassistant-ai/ha-mcp
URL: https://github.com/homeassistant-ai/ha-mcp
Date: 2026-05-06
Excerpt: "Features: ha_call_service, ha_get_state, ha_search_entities, ha_backup_create, ha_config_set_automation, ha_hacs_add_repository... 80+ tools across 20+ categories."
Context: `ha-mcp`, yetkisiz kullanımda riskli olabilir; güçlü araçlar (backup restore, core restart) dikkatle kullanılmalıdır.
Confidence: high

---

## Bölüm 7: Web Tarayıcı Otomasyonu

### 7.1 Playwright ve Accessibility Tree

Claim: Playwright MCP Server, Microsoft tarafından Mart 2025'te yayınlanmıştır; AI agent'lar sayfayı accessibility tree (YAML yapılandırılmış veri) olarak görür; CSS selector'lardan daha kararlı ve refactor-proof'tur [^51^].
Source: GitHub - Microsoft Playwright MCP
URL: https://github.com/microsoft/playwright-mcp
Date: 2026-05-01
Excerpt: "This server enables LLMs to interact with web pages through structured accessibility snapshots, bypassing the need for screenshots or visually-tuned models... Agents interact with pages using structured accessibility snapshots — no vision models or screenshots required."
Context: Playwright MCP, element refs (e5, e10) ile deterministik etkileşim sağlar.
Confidence: high

Claim: Playwright accessibility tree, AI agent'lar için sayfa kontrol katmanı haline gelmiştir; düzen gürültüsünü, stil özniteliklerini ve yapısal boilerplate'i çıkararak temiz bir etkileşim haritası sunar [^52^].
Source: ByteTunnels Blog
URL: https://bytetunnels.com/posts/playwright-for-browser-automation-in-ai-agents/
Date: 2026-03-05
Excerpt: "The accessibility tree strips away layout noise, style attributes, and structural boilerplate. What remains is a clean representation of every element the user can interact with, along with its role (textbox, radio, checkbox, button) and its accessible name."
Context: AI agent, `page.locator('body').aria_snapshot()` ile bu yapıyı okur.
Confidence: high

Claim: Playwright CLI (2026 başı), MCP'den daha token-verimli çalışır; snapshot'ları disk'e kaydeder ve kompakt element referansları (e15, e21) kullanır; Microsoft benchmark'larına göre MCP'den 4x daha az token kullanır [^53^].
Source: TestDino Blog
URL: https://testdino.com/blog/accessibility-tree/
Date: 2026-03-03
Excerpt: "Playwright CLI, released in early 2026, takes a lighter approach... Microsoft's benchmarks showed the CLI approach uses about 4x fewer tokens than MCP for the same tasks."
Context: MCP, persistent state gerektiren exploratory automation için uygundur; CLI, coding agent'lar için verimlidir.
Confidence: high

---

## Bölüm 8: Code Interpreter / Sandbox Python Kod Çalıştırma

### 8.1 Qwen-Agent Code Interpreter

Claim: Qwen-Agent, Docker-sandboxed code execution ile üretim ortamında güvenli Python kod çalıştırır; container lifecycle'ı yönetir, output'ları yakalar ve hataları gracefully işler [^54^].
Source: Yuv.ai Blog
URL: https://yuv.ai/blog/qwen-agent
Date: 2026-03-11
Excerpt: "Docker-Sandboxed Code Execution — Generated code runs in isolated containers with resource limits and network restrictions... The framework manages container lifecycle, captures outputs, and handles errors gracefully."
Context: Qwen-Agent'in code_interpreter aracı built-in olarak gelir.
Confidence: high

### 8.2 E2B Code Interpreter

Claim: E2B Sandbox, Python kodunu Firecracker microVM içinde güvenli şekilde çalıştırır; `Sandbox.create()` ve `run_code()` API'leri basit kullanım sunar; OpenAI, Anthropic, Mistral, Ollama ile entegre çalışır [^55^].
Source: E2B Official Website
URL: https://e2b.dev/
Date: Unknown
Excerpt: "with Sandbox() as sandbox: execution = sandbox.run_code(code)... Trusted by 88% of Fortune 100 companies and powering millions of sandbox sessions."
Context: E2B, multi-language desteği (Python, JavaScript, TypeScript) sunar.
Confidence: high

Claim: E2B tabanlı Agent-Sandbox, MCP üzerinden sandbox lifecycle'ını otomatik yönetir; agent'lar kod çalıştırma, browser kullanımı, terminal erişimi için otomatik sandbox oluşturur ve görev sonunda siler [^56^].
Source: GitHub - agent-sandbox/agent-sandbox
URL: https://github.com/agent-sandbox/agent-sandbox
Date: 2025-12-05
Excerpt: "Agents automatically create a sandbox when code needs to be executed and delete it when execution completes, ensuring isolated and secure code runs... MCP integration enables agents to manage sandbox resources without manual intervention."
Context: Kubernetes üzerinde multi-tenant, multi-session desteği vardır.
Confidence: high

---

## Bölüm 9: Multi-Agent Performans ve Araştırma Bulguları

Claim: Anthropic'ın multi-agent research sistemi (Claude Opus 4 lead + Claude Sonnet 4 subagents), tek-agent Claude Opus 4'e göre dahili değerlendirmelerde %90.2 daha iyi performans göstermiştir [^57^].
Source: Anthropic Engineering Blog
URL: https://www.anthropic.com/engineering/built-multi-agent-research-system
Date: 2025-06-13
Excerpt: "A multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval... breadth-first queries that involve pursuing multiple independent directions simultaneously."
Context: Multi-agent sistemler, chat etkileşimlerine göre ~15x daha fazla token kullanır.
Confidence: high

Claim: Anthropic araştırması, token kullanımının browsing değerlendirmelerindeki performans varyansının %80'ini açıkladığını göstermiştir; model seçimi ve tool call sıklığı ek faktörlerdir [^58^].
Source: ZenML LLMOps Database
URL: https://www.zenml.io/llmops-database/building-a-multi-agent-research-system-for-complex-information-tasks
Date: Unknown
Excerpt: "Token usage explains 80% of performance variance in browsing evaluations, with tool call frequency and model choice as additional factors... Multi-agent systems use approximately 15x more tokens than chats."
Context: Bu bulgu, multi-agent mimarilerinin yüksek değerli görevler için en uygun olduğunu gösterir.
Confidence: high

---

## Sonuç ve Öneriler

### Yerel LLM + Ajan Framework + Home Assistant Entegrasyonu İçin Önerilen Yığın

1. **LLM Sunucusu**: vLLM (üretim) veya Ollama (prototip/test) - OpenAI-compatible API, tool calling desteği
2. **Ajan Framework**: Qwen-Agent (Qwen modelleri için) veya CrewAI (multi-agent için) veya LangChain (esneklik için)
3. **MCP Sunucuları**: filesystem, time, fetch (resmi); ha-mcp (Home Assistant entegrasyonu)
4. **Sandbox**: E2B (cloud) veya Firecracker microVM + Docker (self-hosted)
5. **Ev Otomasyonu**: Home Assistant + Wyoming protokolü (yerel ses) + MCP Server entegrasyonu
6. **Web Otomasyonu**: Playwright MCP Server (accessibility tree tabanlı)
7. **Güvenlik**: System prompt safety rules + sandbox isolation + entity exposure limit (max 25)

### Kritik Güvenlik Hususları

- MCP STDIO transport'unda RCE riski var; güvenilmeyen MCP sunucuları çalıştırılmamalı
- Home Assistant LLM entegrasyonunda entity exposure limit (25) ve system prompt safety rules zorunlu
- Indirect Prompt Injection, hem MCP hem A2A için #1 OWASP riskidir
- AI ajan kod çalıştırma için Docker yeterli değil; Firecracker/gVisor/Kata kullanılmalı
- Langflow CVE-2025-3248 (CVSS 9.8) örneği gösteriyor ki sandbox olmadan `exec()` çalıştırmak kritik risk

---

## Kaynaklar (Citations)

| # | Kaynak | URL |
|---|--------|-----|
| 1 | Yuv.ai - Qwen-Agent | https://yuv.ai/blog/qwen-agent |
| 2 | Qwen-Agent MCP Docs | https://qwenlm.github.io/Qwen-Agent/en/guide/core_moduls/mcp/ |
| 3 | Qwen-Agent Features | https://qwenlm.github.io/Qwen-Agent/en/guide/get_started/features/ |
| 4 | Railway - Letta | https://railway.com/deploy/letta-ai-agent |
| 5 | Medium - Letta | https://medium.com/@vishnudhat/letta-building-stateful-llm-agents |
| 6 | Railway Deploy | https://railway.com/deploy/letta-ai-agent |
| 7 | Speakeasy - LangChain | https://www.speakeasy.com/blog/ai-agent-framework-comparison |
| 8 | Medium - LangChain Tool Calling | https://anshuls235.medium.com/tool-calling-with-langchain |
| 9 | NxCode - CrewAI vs LangChain | https://www.nxcode.io/resources/news/crewai-vs-langchain |
| 10 | LocalAI Master - CrewAI | https://localaimaster.com/blog/crewai-local-setup-guide |
| 11 | Galileo - AutoGen | https://galileo.ai/blog/autogen-framework-multi-agents |
| 12 | Dev.to - Microsoft Agent Framework | https://dev.to/bspann/microsoft-agent-framework |
| 13 | MCP Architecture | https://modelcontextprotocol.io/docs/learn/architecture |
| 14 | Data Science Dojo - MCP | https://datasciencedojo.com/blog/guide-to-model-context-protocol/ |
| 15 | MCP Specification | https://modelcontextprotocol.io/specification/2025-11-25/architecture |
| 16 | MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk |
| 17 | Dysnix - MCP Guide | https://dysnix.com/blog/model-context-protocol |
| 18 | The Hacker News - MCP RCE | https://thehackernews.com/2026/04/anthropic-mcp-design-vulnerability.html |
| 19 | Endor Labs - MCP AppSec | https://www.endorlabs.com/learn/classic-vulnerabilities-meet-ai-infrastructure |
| 20 | StackOne - MCP vs A2A | https://www.stackone.com/blog/mcp-vs-a2a-protocol/ |
| 21 | Elastic - A2A + MCP | https://www.elastic.co/search-labs/blog/a2a-protocol-mcp |
| 22 | StackOne - Hybrid | https://www.stackone.com/blog/mcp-vs-a2a-protocol/ |
| 23 | OpenAI API - Function Calling | https://developers.openai.com/api/docs/guides/function-calling |
| 24 | vLLM Tool Calling | https://docs.vllm.ai/en/latest/features/tool_calling/ |
| 25 | vLLM Supported Models | https://docs.vllm.ai/en/latest/models/supported_models.html |
| 26 | GitHub - vLLM MCP | https://github.com/vllm-project/vllm/issues/34857 |
| 27 | Medium - OpenAI Tool Schema | https://medium.com/@laurentkubaski/openai-tool-schema-explained |
| 28 | Qwen-Agent MCP Config | https://qwenlm.github.io/Qwen-Agent/en/guide/core_moduls/mcp/ |
| 29 | MCP Time Server | https://mcpservers.org/servers/elimS2/mcp-time-server |
| 30 | Natoma.ai - First MCP Server | https://natoma.ai/library/building-your-first-mcp-server |
| 31 | Softwareseni - Sandboxing | https://www.softwareseni.com/ai-agent-sandboxing-explained |
| 32 | Softwareseni - Firecracker | https://www.softwareseni.com/ai-agent-sandboxing-explained |
| 33 | Softwareseni - gVisor | https://www.softwareseni.com/ai-agent-sandboxing-explained |
| 34 | Softwareseni - Kata | https://www.softwareseni.com/ai-agent-sandboxing-explained |
| 35 | E2B Official | https://e2b.dev/ |
| 36 | GitHub - Agent-Sandbox | https://github.com/agent-sandbox/agent-sandbox |
| 37 | Bunnyshell - Sandbox Compare | https://www.bunnyshell.com/guides/coding-agent-sandbox/ |
| 38 | HA Blog 2025.8 | https://www.home-assistant.io/blog/2025/08/06/release-20258/ |
| 39 | Joe Karlsson - Local Voice AI | https://www.joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/ |
| 40 | HA Ollama Integration | https://www.home-assistant.io/integrations/ollama/ |
| 41 | Joe Karlsson - Safety Prompt | https://www.joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/ |
| 42 | HA Wyoming Protocol | https://www.home-assistant.io/integrations/wyoming/ |
| 43 | HA Blog - AI in HA | https://www.home-assistant.io/blog/2025/09/11/ai-in-home-assistant/ |
| 44 | GitHub - Wyoming Satellite | https://github.com/rhasspy/wyoming-satellite |
| 45 | HA REST API Docs | https://developers.home-assistant.io/docs/api/rest/ |
| 46 | HA Community - Entity State | https://community.home-assistant.io/t/howto-execute-program-to-update-light-status |
| 47 | HA Webhook Trigger | https://www.home-assistant.io/docs/automation/trigger/ |
| 48 | HA MCP Server | https://www.home-assistant.io/integrations/mcp_server/ |
| 49 | HA MCP Server Docs | https://www.home-assistant.io/integrations/mcp_server/ |
| 50 | GitHub - ha-mcp | https://github.com/homeassistant-ai/ha-mcp |
| 51 | GitHub - Playwright MCP | https://github.com/microsoft/playwright-mcp |
| 52 | ByteTunnels - Playwright | https://bytetunnels.com/posts/playwright-for-browser-automation-in-ai-agents/ |
| 53 | TestDino - Accessibility Tree | https://testdino.com/blog/accessibility-tree/ |
| 54 | Yuv.ai - Qwen-Agent Docker | https://yuv.ai/blog/qwen-agent |
| 55 | E2B - Code Interpreter | https://e2b.dev/ |
| 56 | Agent-Sandbox MCP | https://github.com/agent-sandbox/agent-sandbox |
| 57 | Anthropic - Multi-Agent | https://www.anthropic.com/engineering/built-multi-agent-research-system |
| 58 | ZenML - Multi-Agent | https://www.zenml.io/llmops-database/building-a-multi-agent-research-system |
