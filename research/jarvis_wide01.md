## Facet: Yerel LLM Altyapilari ve Model Secimi

**Research Date:** 2026-05
**Sources Searched:** 13+ independent queries across GitHub repos, technical blogs, benchmark reports, academic papers, and official documentation

---

### Key Findings

- **Ollama**, 2026'da 100.000+ GitHub star ve ayda 52 milyon indirme ile en yaygin yerel LLM runtime'dir; tek kullanicilik senaryolarda vLLM'e yakin performans saglar ama 5+ eszamanli kullanici oldugunda throughput ~6x duser [^32^](https://theaiengineer.substack.com/p/vllm-vs-ollama-vs-sglang-vs-tensorrt) [^37^](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/)

- **vLLM** uretim ortaminda varsayilan secimdir; PagedAttention ile GPU bellek fragmentasyonunu cozer, 50 eszamanli kullanicida ~920 tok/s throughput saglarken Ollama ~155 tok/s'de kalir [^37^](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/)

- **SGLang**, vLLM'e gore 8B modellerde ~29% daha yuksek throughput (16.200 vs 12.500 tok/s) saglar; RadixAttention ile multi-turn chat ve RAG is yuklerinde 3-5x prefill hizlanmasi saglar [^41^](https://turion.ai/blog/vllm-vs-sglang-inference-comparison-2026/) [^42^](https://techsy.io/en/blog/vllm-vs-sglang)

- **llama.cpp** 2026 Subat'inda OpenAI-uyumlu tool calling destegi kazandi; 8+ model ailesinin native formatini destekler (Llama 3.x, Qwen 2.5, Mistral Nemo, DeepSeek R1, Functionary 3, Hermes 2/3, Firefunction 2) [^112^](https://www.reddit.com/r/LocalLLaMA/comments/1if8x64/llamacpp_now_supports_tool_calling/)

- **TabbyAPI** ExLlamaV2/V3 icin resmi API sunucusudur; OpenAI-uyumlu API, tool/function calling, speculative decoding, multi-LoRA ve paged attention destegi saglar; ancak uretim ortami icin degil, hobi projesi olarak isaretlenmistir [^60^](https://github.com/theroyallab/tabbyAPI/)

- **ktransformers**, DeepSeek-V3 (671B) gibi buyuk MoE modelleri 24GB VRAM + 128GB RAM ile yerel olarak calistirmayi saglayan CPU-GPU hybrid inference sistemidir; llama.cpp'e gore 1.25-4.09x decoding hizlanmasi saglar [^51^](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf) [^58^](https://github.com/kvcache-ai/ktransformers/blob/main/README_ZH.md)

- **ExLlamaV3** (Nisan 2025'te baslatildi) yeni EXL3 quantization formati ve Flash Linear Attention destegiyle Qwen 3.5 ve Gemma 4 modelleri icin optimize edilmistir; TabbyAPI ile OpenAI-uyumlu sunucu saglar [^121^](https://github.com/turboderp-org/exllamav3)

- **Qwen 3.5 122B-A10B**, MMMLU'da GPT-5-mini'yi gecerek (86.7 vs 86.2) en guclu acik kaynak MoE model olarak konumlanmistir; 201 dil destegi vardir ve Turkce dahildir [^88^](https://www.digitalapplied.com/blog/qwen-3-5-medium-model-series-benchmarks-pricing-guide) [^93^](https://blog.mean.ceo/qwen-3-5-small-model-series-release/)

- **CETVEL** (Turkce NLP benchmark) sonuclarina gore **Llama-3.3-70B-Instruct** acik kaynak modeller arasinda en iyi genel performansi gosterir; **Qwen2.5 72B** ise Turkce anlama (TUMLU) benchmark'inda en iyi acik kaynak modeldir (Turkce'de 73.9) [^107^](https://arxiv.org/pdf/2508.16431) [^108^](https://aclanthology.org/2025.acl-long.1112.pdf)

- **Q4_K_M**, GGUF quantization icin genel olarak kabul goren "sweet spot"tur; ~40GB dosya boyutu ile 70B modeli ~95% kalite korunarak calistirir; Q6_K ise uretim icin ~98% kalite saglayan alternatiftir [^34^](https://ai.rs/ai-developer/quantization-methods-compared) [^43^](https://www.sitepoint.com/definitive-guide-local-llms-2026-privacy-tools-hardware/)

- Tool calling destegi olan en iyi yerel modeller (2025-2026): **Qwen3 8B/14B**, **Llama 3.1 8B/70B** (ve Llama 4), **Mistral 7B v0.3+**, **Gemma 4**, **Command R+** [^31^](https://llmhardware.io/guides/local-llm-function-calling-guide/) [^116^](https://collabnix.com/best-ollama-models-for-function-calling-tools-complete-guide-2025/)

- Llama 3.3 ve Llama 4 resmi kartlarinda Turkce destegi listelenmemis olsa da (Llama 3.3: 8 dil; Llama 4: 12 dil), her iki model de genis multilingual pretraining ile Turkce anlama ve uretim yetenegi gosterir [^50^](https://dev.to/nodeshiftcloud/step-by-step-guide-to-run-llama-4-locally-with-tool-calling-enabled-jg7) [^105^](https://galileo.ai/model-hub/llama-3.3-70b-overview)

---

### 1. Yerel LLM Inference Altyapilari Karsilastirmasi

#### 1.1 Genel Bakis Tablosu

| Altyapi | Cekirdek Teknoloji | En Iyi Oldugu Alan | Batching | Quantization | Tool Calling | Donanim Destegi |
|---|---|---|---|---|---|---|
| **Ollama** | llama.cpp wrapper | Hizli prototipleme, tek kullanici | Statik, sirali | GGUF (Q2-Q8) | Native (2026) | NVIDIA, AMD, Apple, CPU |
| **vLLM** | PagedAttention | Uretim, genel amacli | Surekli, dinamik | AWQ, GPTQ, FP4/FP8/Int4 | ToolParserManager | NVIDIA, AMD, Intel, TPU, Trainium |
| **SGLang** | RadixAttention | Multi-turn, RAG, agent | Surekli, dinamik | FP4/FP8/Int4/AWQ/GPTQ | Structured output optimize | NVIDIA, AMD |
| **llama.cpp** | C++ GGUF engine | CPU/GPU esnek, edge | Sirali, sinirli batching | GGUF (Q2-Q8) | Native (Subat 2026) | NVIDIA, AMD, Apple, CPU, GPU |
| **TabbyAPI** | ExLlamaV2/V3 | Hizli GGUF/EXL2 consumer GPU | Dinamik, paged attention | EXL2, EXL3 | OAI style | NVIDIA |
| **ktransformers** | CPU-GPU hybrid offloading | Buyuk MoE (DeepSeek V3) | Asenkron CPU-GPU | BF16, AMX-Int8 | HuggingFace arayuzu | NVIDIA + CPU (AMX/AVX-512) |
| **TensorRT-LLM** | NVIDIA optimize edilmis | Maksimum throughput, tek model | Optimize edilmis | FP8, FP4 | Var | NVIDIA only |
| **LMDeploy** | TurboMind (C++) | Hizli quantized inference | Surekli | AWQ, GPTQ, Int4 | Var | NVIDIA |
| **LocalAI** | Multi-backend proxy | Esnek backend secimi | Backend'e bagli | GGUF + diger | llama.cpp, vLLM, MLX | Coklu |

#### 1.2 Ollama

Ollama, Docker benzeri Modelfile sistemi ile tek komut kurulum (`ollama run llama3.1`) saglayan en populer yerel LLM runtime'dir. 2026'da native agentic tool calling destegi eklenmistir [^38^](https://www.decodesfuture.com/articles/llama-cpp-vs-ollama-vs-vllm-local-llm-stack-guide). llama.cpp uzerine insa edilmis olup, 10-15% (bazen 30%) throughput overhead'i vardir [^38^](https://www.decodesfuture.com/articles/llama-cpp-vs-ollama-vs-vllm-local-llm-stack-guide). Tek kullanici senaryolarinda Ollama (Q4_K_M) ~62 tok/s, vLLM (FP16) ~71 tok/s verirken; 50 eszamanli kullanicida Ollama ~155 tok/s'de kalirken vLLM ~920 tok/s saglar [^37^](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/). Otomatik model degistirme (unload/load) destegi vardir.

**Artilari:** En kolay kurulum, en genis model ekosistemi (Ollama Hub), her yerde calisir, OpenAI-uyumlu API, ucretsiz.
**Eksileri:** Eszamanli istek optimizasyonu yok, yuk altinda ITL (Inter-Token Latency) tutarsiz, uretim olceginde sinirli.

#### 1.3 vLLM

HuggingFace'in TGI'yi Aralik 2025'te bakim moduna almasinin ardindan, vLLM uretim ortaminda en yaygin varsayilan secim haline gelmistir [^42^](https://techsy.io/en/blog/vllm-vs-sglang). PagedAttention teknolojisi GPU bellek fragmentasyonunu ortadan kaldirir. En genis donanim destegine sahiptir: NVIDIA, AMD, Intel, AWS Trainium, Google TPU [^42^](https://techsy.io/en/blog/vllm-vs-sglang). Tool calling icin ToolParserManager mimarisi ile `llama3_json`, `llama4_pythonic`, `hermes`, `mistral`, `qwen3_xml`, `deepseek_v3` gibi cok sayida parser saglar [^61^](https://docs.vllm.ai/en/latest/features/tool_calling/).

**Artilari:** En genis donanim destegi, en buyuk topluluk (17k+ GitHub star), coklu LoRA adapter destegi, speculative decoding, disaggregated prefill/decode.
**Eksileri:** SGLang'e gore 8B modellerde ~29% daha dusuk throughput, prefix-heavy is yuklerinde RadixAttention kadar verimli degil.

#### 1.4 SGLang

SGLang, 2026'da RadixArk olarak 400M$ degerleme ile spinout olan projedir [^41^](https://turion.ai/blog/vllm-vs-sglang-inference-comparison-2026/). RadixAttention teknolojisi, token seviyesinde radix tree kullanarak paylasilan prefix'leri otomatik kesfeder ve yeniden kullanir. Multi-turn sohbetlerde 95%+ cache hit rate saglar. DeepSeek V3/V4 icin resmi onerilen inference engine'dir; 3.1x daha hizli inference saglar [^44^](https://particula.tech/blog/sglang-vs-vllm-inference-engine-comparison). Structured output (JSON/regex) icin maske uretimini GPU inference ile ust uste bindirerek vLLM'e gore 3x daha hizli constrained decoding saglar [^44^](https://particula.tech/blog/sglang-vs-vllm-inference-engine-comparison).

**Artilari:** En yuksek throughput (8B'de 29% ustunluk), multi-turn/RAG'de 6.4x hizlanma, en iyi structured output performansi, DeepSeek optimizasyonu.
**Eksileri:** Daha kucuk ekosistem (15k star), yuksek eszamanlilikta Python GIL darbogazi potansiyeli [^46^](https://github.com/sgl-project/sglang/issues/21061), sadece NVIDIA ve AMD destegi.

#### 1.5 llama.cpp

C++ ile yazilmis, en hafif ve en yaygin desteklenen GGUF inference motorudur. 2026 Subat'inda OpenAI-uyumlu tool calling destegi kazanmistir; hem generic JSON-schema tabanli hem de 8+ modelin native formatini destekler [^112^](https://www.reddit.com/r/LocalLLaMA/comments/1if8x64/llamacpp_now_supports_tool_calling/). llama.cpp server, Anthropic Messages API'yi de destekler [^113^](https://huggingface.co/blog/ggml-org/anthropic-messages-api-in-llamacpp). Raspberry Pi 5 dahil her yerde calisir.

**Artilari:** En genis cihaz destegi, en hafif, en iyi GGUF optimizasyonu, yeni formatlara hizli adaptasyon.
**Eksileri:** Ollama/vLLM kadar zengin API ozellikleri yok, batching siniri.

#### 1.6 TabbyAPI + ExLlamaV2/V3

TabbyAPI, ExLlamaV2/V3 icin FastAPI tabanli resmi sunucudur. ExLlamaV2 artik arsivlenmis, gelisim ExLlamaV3 uzerinden surmektedir [^57^](https://github.com/turboderp-org/exllamav2). ExLlamaV3, yeni EXL3 quantization formati, tensor-parallel ve expert-parallel inference, Flash Linear Attention, multimodal destegi ve speculative decoding saglar [^121^](https://github.com/turboderp-org/exllamav3). TabbyAPI tool calling, embedding modelleri, JSON schema/Regex/EBNF, paged attention ve multi-LoRA destegi saglar [^60^](https://github.com/theroyallab/tabbyAPI/). Ancak proje "hobi projesi" olarak isaretlenmis, uretim icin degil [^60^](https://github.com/theroyallab/tabbyAPI/).

**Artilari:** En hizli consumer GPU inference (EXL2/EXL3), per-layer bit ayari, cok esnek quantization.
**Eksileri:** Sadece ExLlamaV2/V3 runtime, uretim icin onerilmiyor, ROCm destegi eksik.

#### 1.7 ktransformers

ktransformers, buyuk MoE modellerin (DeepSeek-V3 671B, Qwen2.5-57B) CPU-GPU hybrid inference icin tasarlanmistir. GPU'de sadece paylasilan expert'ler (17B) tutulur, yonlendirilmis expert'ler (654B) CPU RAM'e offload edilir [^51^](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf). AMX/AVX-512 CPU kernel optimizasyonlari, NUMA-aware tensor parallelism ve Expert Deferral teknikleri ile llama.cpp'e gore 1.25-4.09x decoding hizlanmasi saglar [^51^](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf). DeepSeek V3 24GB VRAM + 128GB RAM ile calisir; 5-6 tok/s decode saglar [^58^](https://github.com/kvcache-ai/ktransformers/blob/main/README_ZH.md). 2025 Ekim'den itibaren SGLang'e entegre edilmistir [^58^](https://github.com/kvcache-ai/ktransformers/blob/main/README_ZH.md).

**Artilari:** 671B MoE modelleri consumer donanimda calistirir, FlashInfer attention, Marlin quantization.
**Eksileri:** Sadece MoE modeller icin optimize, yuksek sistem RAM gereksinimi, karma kurulum.

---

### 2. Turkce Performansi En Iyi Olan Acik Kaynakli LLM'ler

#### 2.1 Akademik Benchmark Sonuclari

**CETVEL Benchmark** (2026) - 33 acik agirlikli model degerlendirmesi:
- En iyi genel performans: **Llama-3.3-70B-Instruct** (ikinci: Aya-Expanse-32B, 4.5 puan geride)
- Turkce-merkezli modeller (Kanarya-2B, Turna-1B, Commencis-LLM-7B, Trendyol-LLM-7B) genel amacli cok dilli modellerin gerisinde kalmistir
- **Cere-Llama-3-8B**, gramer duzeltme (GECturk) ve Turkce/Islam tarihi QA'da Llama-3.3-70B-Instruct'i gecmistir [^107^](https://arxiv.org/pdf/2508.16431)

**TurkBench** (2026):
- En yuksek skor: **GPT-OSS-120B** (77.6 ortalama)
- **GLM-4-6** (83.7) ve **DeepSeek-V3.1** (77.4) takip eder
- **Qwen3-Next-80B** Turkce bilgi ve matematikte yuksek performans gosterir [^111^](https://arxiv.org/pdf/2601.07020)

**TUMLU Benchmark** (Turk Dilleri, ACL 2025):
- Proprietary lider: Claude 3.5 Sonnet (Turkce: 85.7)
- Acik kaynak lider: **Qwen2.5 72B** (Turkce: 73.9)
- **Llama 3.1 405B** Turkce'de 59.7 skoruyla geridedir; **Llama 3.3 70B** ise 68.4 skoruna yukselmistir [^108^](https://aclanthology.org/2025.acl-long.1112.pdf)

**TurkishMMLU**:
- **Llama 3.3 70B**, **Mistral Large 2** ve **Qwen 2.5** serisi Turkce akademik bilgi testlerinde guclu sonuclar verir [^114^](https://aclanthology.org/2024.findings-emnlp.413.pdf)

#### 2.2 Model Degerlendirmesi (Turkce Acisindan)

| Model | Turkce Degerlendirmesi | Parametre | VRAM (Q4) | Tool Calling | Lisans |
|---|---|---|---|---|---|
| **Qwen 3.5 122B-A10B** | 201 dil; Turkce dahil; MMMLU 86.7 | 122B (10B aktif) | ~48GB+ | Var | Apache 2.0 |
| **Qwen 3.5 27B** | 201 dil; Turkce dahil; coding lideri | 27B | ~16GB | Var | Apache 2.0 |
| **Llama 3.3 70B** | Resmi 8 dil (Turkce yok); ama multilingual pretraining ile guclu Turkce yetenek; CETVEL lideri | 70B | ~40GB | Var | Llama 3.3 |
| **Llama 4 Scout** | 12 resmi dil; 200+ dilde pretraining; 10M context | 109B (17B aktif) | ~24GB | Var (pythonic) | Llama 4 |
| **Llama 4 Maverick** | 12 resmi dil; 200+ dilde pretraining; en guclu Meta modeli | 400B (17B aktif) | ~48GB+ | Var (pythonic) | Llama 4 |
| **Mistral Large 2** | 80+ dil destegi; Avrupa kokenli; 128K context | 123B | ~60GB | Var | Apache 2.0 |
| **Gemma 4 31B** | 100+ dil pretraining, 30+ dil destegi; multimodal | 31B | ~20GB | Native | Gemma |
| **Command R+** | 10 dil resmi; RAG ve tool-use optimize | 104B (16B aktif) | ~60GB | Var | CC-BY-NC |
| **DeepSeek V3.2** | Cok dilli; MIT lisans; 685B MoE | 685B (37B aktif) | ~48GB+ | Var (Base/Exp) | MIT |
| **Aya-Expanse-32B** | Cohere'in cok dilli modeli; CETVEL #2 | 32B | ~20GB | Var | Apache 2.0 |

#### 2.3 Turkce Icin Oneriler

- **En iyi genel Turkce performans (acik kaynak):** Llama-3.3-70B-Instruct (CETVEL lideri)
- **En iyi Turkce anlama (TUMLU):** Qwen2.5 72B
- **En iyi kod + Turkce:** Qwen 3.5 27B (SWE-bench 72.4%, Turkce destekli)
- **24GB VRAM sinirinda en iyi Turkce:** Llama 4 Scout veya Gemma 4 31B
- **En iyi Turkce-ozellestirilmis model:** Cere-Llama-3-8B (gramer ve tarihi QA'da 70B'yi gecer)

---

### 3. Quantization Yontemleri ve Performans Etkileri

#### 3.1 Format Karsilastirmasi

| Format | Bits | Kalite (MMLU) | Hiz Optimizasyonu | Ekosistem | Calibrasyon |
|---|---|---|---|---|---|
| **GGUF Q8_0** | 8-bit | 99.5% | CPU/GPU genel | Ollama, llama.cpp, LM Studio | Hayir |
| **GGUF Q6_K** | 6-bit | ~98% | CPU/GPU genel | Ollama, llama.cpp | Hayir |
| **GGUF Q5_K_M** | 5-bit | 96-97% | CPU/GPU genel | Ollama, llama.cpp | Hayir |
| **GGUF Q4_K_M** | 4-bit | ~95% | CPU/GPU genel | Ollama, llama.cpp | Hayir |
| **GGUF Q3_K_M** | 3-bit | Dikkate deger kayip | CPU/GPU genel | Ollama, llama.cpp | Hayir |
| **GPTQ Int4** | 4-bit | ~95-96% | CUDA GPU hizli | vLLM, transformers, AutoGPTQ | Evet (128-256 ornek) |
| **AWQ** | 4-bit | ~96% | CUDA GPU, kalite koruma | vLLM, HuggingFace | Evet |
| **EXL2** | 2.5-6 (ayarlanabilir) | Sinifinin en iyisi | Consumer GPU, ExLlamaV2 only | ExLlamaV2 only | Evet |
| **EXL3** | 2-8 (ayarlanabilir) | QTIP tabanli | Consumer GPU, ExLlamaV3 only | ExLlamaV3/TabbyAPI | Hayir (kismi) |
| **NVFP4** | 4-bit float | 97.5% MMLU, 79.4% MMLU-Pro | Blackwell tensor core | vLLM (Blackwell only) | Hayir |

#### 3.2 Detayli Analiz

**GGUF (llama.cpp / Ollama):** En yaygin format. Mixed-precision integer quantization kullanir. Q4_K_M, dosya boyutu ve kalite arasindaki "sweet spot" olarak kabul edilir [^34^](https://ai.rs/ai-developer/quantization-methods-compared) [^43^](https://www.sitepoint.com/definitive-guide-local-llms-2026-privacy-tools-hardware/). llama.cpp kernel optimizasyonlari ile consumer GPU'larda Ollama (Q4) vLLM (FP16) ile yarisir hale gelmistir [^37^](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/). GGUF olusturma suresi GPTQ/AWQ/EXL2'ye gore 10x daha kisadir [^35^](https://oobabooga.github.io/blog/posts/gptq-awq-exl2-llamacpp/).

**AWQ:** Activation-aware weight quantization, onemli agirliklari aktivasyon analizi ile korur. GPTQ'ye gore 4-bit'te hafif ustunluk saglar. vLLM ve transformers ile uyumlu [^34^](https://ai.rs/ai-developer/quantization-methods-compared). Uretimde maksimum kalite koruma onceliginde tercih edilir [^36^](https://www.index.dev/skill-vs-skill/ai-gptq-vs-awq-vs-gguf).

**GPTQ:** Calibration-based 4-bit integer format. vLLM + multi-LoRA icin en iyi yoldur; NVFP4 henuz LoRA adapter destegi saglamamaktadir [^34^](https://ai.rs/ai-developer/quantization-methods-compared). En hizli inference hizi saglar [^36^](https://www.index.dev/skill-vs-skill/ai-gptq-vs-awq-vs-gguf).

**EXL2/EXL3:** Per-layer bit ayari ile herhangi bir hedef boyutta sinifinin en iyi kalitesini saglar. Ancak sadece ExLlamaV2/V3 runtime ile calisir, vLLM destegi yoktur [^34^](https://ai.rs/ai-developer/quantization-methods-compared). EXL3, QTIP tabanli yeni bir formattir ve Gemma 4, Qwen 3.5 icin optimize edilmistir [^121^](https://github.com/turboderp-org/exllamav3).

**NVFP4:** NVIDIA Blackwell (RTX 5090, B100, B200) icin 4-bit floating point formati. Ozel FP4 tensor core'lari kullanir. MMLU'da 97.5% koruma saglarken, zorlu reasoning (MMLU-Pro 79.4%, AIME24 81.8%) tasklarinda belirgin dususler gorulur [^34^](https://ai.rs/ai-developer/quantization-methods-compared).

#### 3.3 70B Model Quantization Pratigi

| Quantization | Dosya Boyutu | Kalite Etkisi | Min VRAM |
|---|---|---|---|
| FP16 | ~140 GB | Baseline | ~140GB |
| Q8_0 | ~70 GB | Goz ardi edilebilir kayip | ~80GB |
| Q6_K | ~54 GB | Minimal kayip | ~60GB |
| Q5_K_M | ~46 GB | Cok hafif kayip | ~50GB |
| **Q4_K_M** | **~40 GB** | **En iyi kalite/boyut orani** | **~40-48GB** |
| Q3_K_M | ~33 GB | Dikkate deger bozulma | ~36GB |
| Q2_K | ~25 GB | Onemli bozulma | ~28GB |

[^43^](https://www.sitepoint.com/definitive-guide-local-llms-2026-privacy-tools-hardware/)

---

### 4. Donanim Gereksinimleri

#### 4.1 GPU VRAM ile Model Eslestirmesi

| GPU VRAM | Sigan Modeller | Onerilen Format |
|---|---|---|
| 6 GB | 7-8B (Q4_K_M, dar) | Q4_K_M veya IQ4_XS |
| 8 GB | 7-8B (Q4-Q5), 8B Q8_0 | Q5_K_M veya Q8_0 |
| 12 GB | 7-8B (herhangi), 13-14B Q4_K_M | Q5_K_M veya Q8_0 (7B icin) |
| 16 GB | 13-14B (Q5-Q8), Qwen 2.5 14B | Q5_K_M veya Q6_K |
| **24 GB** | **34B Q4_K_M, 8B FP16, Llama 4 Scout** | **Q4_K_M veya Q5_K_M** |
| 48 GB | 70-72B Q4_K_M (tam GPU) | Q4_K_M veya Q5_K_M |
| 80 GB | 70B FP16, 405B Q4_K_M | FP16 (70B icin) |
| 2x 80 GB | 405B Q5_K_M, 70B FP16 | Q5_K_M (405B icin) |

[^33^](https://letsdatascience.com/blog/llm-quantization-run-any-model-on-consumer-hardware) [^39^](https://www.databasemart.com/blog/how-much-vram-do-you-need-for-7-70b-llm?srsltid=AfmBOorA2r3mZl9PjtnaQuF1wDzotOdFxegEO1mxg8uV7jwQWtL33BK1)

#### 4.2 Model Boyutu / Precision Matrisi

| Model | FP16 VRAM | INT4/GPTQ VRAM | FP8 VRAM |
|---|---|---|---|
| 7B | ~16-20 GB | ~6-8 GB | ~10-14 GB |
| 8B | ~16-20 GB | ~6-8 GB | ~10-14 GB |
| 13-14B | ~28-32 GB | ~10-14 GB | ~18-22 GB |
| 34B | ~70-80 GB | ~20-28 GB | ~45-60 GB |
| 70B | ~140-160 GB | ~40-48 GB | ~110-130 GB |
| 405B | ~800GB+ | ~200-250 GB | ~500GB+ |
| 671B (DeepSeek V3) | ~700GB+ | ~350-400GB (Q4) | ~500GB+ |

[^39^](https://www.databasemart.com/blog/how-much-vram-do-you-need-for-7-70b-llm?srsltid=AfmBOorA2r3mZl9PjtnaQuF1wDzotOdFxegEO1mxg8uV7jwQWtL33BK1) [^40^](https://www.gmicloud.ai/blog/which-open-source-llm-models-are-currently)

#### 4.3 Ozel Durumlar

- **DeepSeek V3 671B (Q4_K_M Ollama ile):** 24GB VRAM + 128GB RAM ile ~5-20 tok/s; CPU-only 64GB+ RAM ile 1-4 tok/s [^90^](https://www.sitepoint.com/deepseek-v3-complete-guide-deploy-and-optimize-local-ai-in-2026/)
- **DeepSeek V3 (Unsloth Dynamic 2.0 TQ1_0):** 170GB disk, 24GB VRAM + 128GB RAM ile MoE offloading ile calisir [^91^](https://unsloth.ai/docs/models/tutorials/deepseek-v3.1-how-to-run-locally)
- **ktransformers ile DeepSeek V3:** 24GB VRAM + 128GB RAM, BF16; 5-6 tok/s decode [^51^](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf)
- **Llama 4 Scout:** 24GB VRAM'de INT4 ile calisir [^85^](https://overchat.ai/ai-hub/best-local-llm)
- **Gemma 4 E4B:** 3GB VRAM'de calisir - telefon ve Raspberry Pi uyumlu [^85^](https://overchat.ai/ai-hub/best-local-llm)

#### 4.4 Donanim Onerileri (Agentik Is Yukleri)

| GPU | Qwen3-14B Hizi | Agent Deneyimi |
|---|---|---|
| RTX 4060 Ti 16GB | ~20 tok/s | Basit ajanlar icin kullanilabilir |
| RTX 4070 Ti Super | ~45 tok/s | Cok adimli ajanlar icin iyi |
| RTX 4090 | ~60 tok/s | Mukemmel - neredeyse aninda |
| Mac Studio M4 Max | ~50 tok/s | Mükemmel, sessiz, verimli |

[^31^](https://llmhardware.io/guides/local-llm-function-calling-guide/)

---

### 5. Tool Calling / Function Calling Destegi Olan Yerel Modeller

#### 5.1 Native Tool Calling Destegi Olan Modeller

| Model | Tool Calling Turu | Altyapi Uyumu | Turkce | Notlar |
|---|---|---|---|---|
| **Qwen3 8B/14B/32B** | JSON, XML | Ollama, vLLM, llama.cpp | 201 dil | En guvenilir yerel tool calling [^31^](https://llmhardware.io/guides/local-llm-function-calling-guide/) |
| **Llama 3.1 8B/70B** | JSON (llama3_json) | vLLM, Ollama, llama.cpp | Multilingual | En yaygin destek [^61^](https://docs.vllm.ai/en/latest/features/tool_calling/) |
| **Llama 4 Scout/Maverick** | Pythonic (llama4_pythonic) | vLLM, Ollama v0.8+ | 12 resmi + 200+ pretraining | Paralel tool calls destegi [^61^](https://docs.vllm.ai/en/latest/features/tool_calling/) |
| **Mistral 7B v0.3+ / Large 2** | Mistral native | vLLM, Ollama | 80+ dil | Guclu JSON schema uyumu [^116^](https://collabnix.com/best-ollama-models-for-function-calling-tools-complete-guide-2025/) |
| **Gemma 4** | Native function calling | Ollama, vLLM, llama.cpp | 100+ dil | Agentic pipeline'lara hazir [^52^](https://www.bentoml.com/blog/navigating-the-world-of-open-source-large-language-models) |
| **Command R+** | Tool-use native | Ollama, vLLM | 10 dil | RAG optimize [^94^](https://huggingface.co/blog/daya-shankar/open-source-llms) |
| **Kimi K2 Thinking** | 200-300 sequential tool calls | vLLM, SGLang | Cok dilli | Otonom agent workflows [^53^](https://fireworks.ai/blog/best-open-source-llms) |
| **DeepSeek V3.2 (Base/Exp)** | JSON | vLLM, SGLang | Cok dilli | Reasoning trace korur [^53^](https://fireworks.ai/blog/best-open-source-llms) |
| **Functionary v3.1/v3.2** | LLM-as-tool uzman | llama.cpp | Ingilizce odakli | Paralel function calling [^122^](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md) |
| **Hermes 2/3** | Generic tool format | llama.cpp, vLLM | Ingilizce odakli | Genel tool parser [^122^](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md) |
| **GPT-OSS 120B/20B** | Tool use | llama.cpp, vLLM | Cok dilli | OpenAI'nin ilk acik agirlikli modelleri [^85^](https://overchat.ai/ai-hub/best-local-llm) |

#### 5.2 Altyapi Bazinda Tool Calling Destegi

**Ollama:** Native tool calling 2026'da gelmistir [^38^](https://www.decodesfuture.com/articles/llama-cpp-vs-ollama-vs-vllm-local-llm-stack-guide). OpenAI-uyumlu `/v1/chat/completions` endpoint ile `tools` array gonderilebilir. En iyi calisan modeller: `qwen3:14b`, `llama3.1:8b`, `mistral:7b` [^31^](https://llmhardware.io/guides/local-llm-function-calling-guide/).

**vLLM:** `ToolParserManager` mimarisi ile cok sayida parser saglar: `llama3_json`, `llama4_pythonic`, `hermes`, `mistral`, `qwen3_xml`, `deepseek_v3`, `granite4`, `kimi_k2`, `glm45` [^117^](https://localai.io/features/openai-functions/). Llama 4 icin pythonic tool calling onerilir [^61^](https://docs.vllm.ai/en/latest/features/tool_calling/).

**llama.cpp:** llama-server, 2026 Subat'inda OpenAI-uyumlu tool calling kazandi. Generic JSON-schema tabanli parser ve 8+ modelin native formati desteklenir [^112^](https://www.reddit.com/r/LocalLLaMA/comments/1if8x64/llamacpp_now_supports_tool_calling/). Jinja chat template ile calisir (`--jinja` flag).

**TabbyAPI:** "OAI style tool/function calling" destegi saglar; Jinja2 template engine ile HuggingFace uyumlu [^60^](https://github.com/theroyallab/tabbyAPI/).

**LocalAI:** llama.cpp, vLLM, MLX backend'lerinin her biri icin tool calling abstraction saglar. llama.cpp icin C++ incremental parser herhangi bir GGUF modelle calisir [^117^](https://localai.io/features/openai-functions/).

---

### Major Players & Sources

| Kaynak | Rol / Onem |
|---|---|
| **vLLM GitHub / docs** [^61^](https://docs.vllm.ai/en/latest/features/tool_calling/) | Production inference standard; tool calling parser dokumantasyonu |
| **SGLang Blog / GitHub** [^41^](https://turion.ai/blog/vllm-vs-sglang-inference-comparison-2026/) [^44^](https://particula.tech/blog/sglang-vs-vllm-inference-engine-comparison) | RadixAttention teknolojisi ve benchmark verileri |
| **Ollama Resmi** [^32^](https://theaiengineer.substack.com/p/vllm-vs-ollama-vs-sglang-vs-tensorrt) [^38^](https://www.decodesfuture.com/articles/llama-cpp-vs-ollama-vs-vllm-local-llm-stack-guide) | En populer yerel runtime; tool calling, model ekosistemi |
| **llama.cpp GitHub** [^112^](https://www.reddit.com/r/LocalLLaMA/comments/1if8x64/llamacpp_now_supports_tool_calling/) [^122^](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md) | GGUF standardi, C++ inference, tool calling destegi |
| **ExLlamaV3 / TabbyAPI GitHub** [^121^](https://github.com/turboderp-org/exllamav3) [^60^](https://github.com/theroyallab/tabbyAPI/) | EXL3 formati, consumer GPU optimizasyonu |
| **ktransformers SOSP 2025 Paper** [^51^](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf) | CPU-GPU hybrid inference, MoE offloading akademik calisma |
| **CETVEL Benchmark (arXiv 2025)** [^107^](https://arxiv.org/pdf/2508.16431) | Kapsamli Turkce NLP degerlendirmesi (33 model) |
| **TUMLU Benchmark (ACL 2025)** [^108^](https://aclanthology.org/2025.acl-long.1112.pdf) | Turk dilleri (10 dil) LLM degerlendirmesi |
| **TurkBench (arXiv 2026)** [^111^](https://arxiv.org/pdf/2601.07020) | Turkce acik agirlikli model karsilastirmasi |
| **Qwen Resmi HuggingFace** [^92^](https://huggingface.co/Qwen/Qwen3.5-122B-A10B) | Qwen 3.5 benchmark sonuclari, model kartlari |
| **SitePoint Benchmark 2026** [^37^](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/) | Ollama vs vLLM kapsamli benchmark |
| **Spheron H100 Benchmarks** [^45^](https://www.spheron.network/blog/vllm-vs-tensorrt-llm-vs-sglang-benchmarks/) | vLLM vs TensorRT-LLM vs SGLang H100 benchmark |
| **PremAI Inference Benchmark** [^47^](https://blog.premai.io/vllm-vs-sglang-vs-lmdeploy-fastest-llm-inference-engine-in-2026/) | vLLM vs SGLang vs LMDeploy throughput karsilastirmasi |
| **OverChat Best Local LLMs 2026** [^85^](https://overchat.ai/ai-hub/best-local-llm/) | Donanim bazli model secim rehberi |
| **AI.rs Quantization Guide** [^34^](https://ai.rs/ai-developer/quantization-methods-compared) | GGUF, AWQ, GPTQ, EXL2, NVFP4 karsilastirmasi |

---

### Trends & Signals

- **TGI'nin bakim moduna gecisi** (Aralik 2025) ile HuggingFace, vLLM ve SGLang'a yonlendiriyor; bu iki motor arasindaki rekabet inference motoru pazarini hizla ilerletiyor [^42^](https://techsy.io/en/blog/vllm-vs-sglang)

- **MoE mimarisi** yerel LLM'lerde standard haline geldi; Llama 4 (17B aktif), Qwen 3.5 (10B aktif), DeepSeek V3 (37B aktif) gibi modeller, toplam parametrelerin sadece %5-15'ini aktive ederek buyuk model kalitesini consumer donanimda sunuyor [^85^](https://overchat.ai/ai-hub/best-local-llm)

- **CPU-GPU hybrid inference** (ktransformers, llama.cpp offload) ile 671B parametreli modeller artik 24GB VRAM ile calistirilabiliyor; bu, edge AI ve yerel deployment'ta paradigma degisikligi yaratiyor [^51^](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf)

- **Tool calling** artik acik kaynak modellerde standard ozellik; Ollama, vLLM, llama.cpp, SGLang'in tamami native tool calling destegi sagliyor. Bu, yerel ajan (agent) mimarilerinin onunu aciyor [^112^](https://www.reddit.com/r/LocalLLaMA/comments/1if8x64/llamacpp_now_supports_tool_calling/) [^117^](https://localai.io/features/openai-functions/)

- **Turkce NLP'de cok dilli modeller**, Turkce-merkezli modelleri geride birakiyor. CETVEL ve TUMLU benchmark'lari, Llama 3.3, Qwen 2.5/3.5 gibi genel modellerin, Kanarya, Turna gibi Turkce-ozel modellerden ustun oldugunu gosteriyor [^107^](https://arxiv.org/pdf/2508.16431) [^108^](https://aclanthology.org/2025.acl-long.1112.pdf)

- **Quantization kalitesi** hizla iyilesiyor; Unsloth Dynamic 2.0 ile 1-bit/2-bit quantization bile 5-shot MMLU'da minimal kayip sagliyor [^91^](https://unsloth.ai/docs/models/tutorials/deepseek-v3.1-how-to-run-locally)

- **Context uzunluklari** patliyor; Llama 4 Scout 10M token, Qwen 3.5 800K+, Gemma 4 256K context window sagliyor [^85^](https://overchat.ai/ai-hub/best-local-llm)

---

### Controversies & Conflicting Claims

- **Ollama vs vLLM tek kullanici performansi:** SitePoint benchmark'ine gore Ollama (Q4_K_M) vLLM (FP16) ile yarisirken (~62 vs ~71 tok/s), The AI Engineer'a gore Ollama 22 tok/s'de sabitlenirken vLLM 3.23x daha fazla throughput saglar. Bu fark, benchmark senaryosuna (tek kullanici sirali vs eszamanli) baglidir [^37^](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/) [^32^](https://theaiengineer.substack.com/p/vllm-vs-ollama-vs-sglang-vs-tensorrt)

- **SGLang'in yuksek eszamanlilikta performansi:** Bir GitHub issue'da, SGLang 150 eszamanli istekte vLLM'in yarisindan az throughput (150 vs 364 req/s) saglarken ve Python GIL darbogazi yasarken, diger benchmark'ler SGLang'i vLLM ustunde gosteriyor. Bu, workload tipine (unique prompt vs shared prefix) ve model boyutuna (0.5B vs 70B) bagli olarak degisir [^46^](https://github.com/sgl-project/sglang/issues/21061) [^42^](https://techsy.io/en/blog/vllm-vs-sglang)

- **NVFP4 quantization:** NVIDIA Blackwell icin 97.5% MMLU korumasi iddia edilirken, MMLU-Pro'da 79.4% ve AIME24'te 81.8% gibi zorlu reasoning tasklarinda ciddi dususler goruluyor; bu, "kaliteyi anlama" konusunda cift yonlu bir hikaye yaratiyor [^34^](https://ai.rs/ai-developer/quantization-methods-compared)

- **Turkce-ozel modellerin degeri:** CETVEL sonuclari, Turkce-ozel modellerin (Kanarya, Turna, Commencis, Trendyol) genel cok dilli modellerden geride oldugunu gosteriyor. Ancak Cere-Llama-3-8B, belirli Turkce gorevlerinde 70B'yi geciyor. Bu, "dil-ozel mi yoksa genel-multilingual mi" tartismasini alevlendiriyor [^107^](https://arxiv.org/pdf/2508.16431)

- **Llama 4'un Turkce destegi:** Resmi model kartlarinda Turkce listelenmiyor (12 resmi dil), ancak 200+ dilde pretraining yapilmis. Topluluk testleri Turkce anlama ve uretim yetenegini dogruluyor. Bu, "resmi destek" ile "gercek yetenek" arasindaki farki gosteriyor [^50^](https://dev.to/nodeshiftcloud/step-by-step-guide-to-run-llama-4-locally-with-tool-calling-enabled-jg7)

---

### Recommended Deep-Dive Areas

1. **SGLang + ktransformers entegrasyonu:** ktransformers Ekim 2025'ten itibaren SGLang'e entegre edilmistir. Bu kombinasyon, DeepSeek V3 gibi buyuk MoE modelleri SGLang'in RadixAttention ve ktransformers'in CPU offload yetenekleriyle calistirma potansiyeli tasiyor. Derinlemesine incelenmeli cunku bu, 671B modelleri agentik workflow'larda kullanma kapisi acabilir [^58^](https://github.com/kvcache-ai/ktransformers/blob/main/README_ZH.md)

2. **Qwen 3.5 27B'nin Turkce tool calling kalitesi:** Qwen 3.5, 201 dil destegi ve en guclu acik kaynak coding modeli olarak konumlaniyor. Ancak Turkce'de tool calling (ozellikle fonksiyon parametre cikarma ve JSON schema uyumu) konusunda pratik degerlendirme yapilmali; bu, OpenJarvis benzeri Turkce agent sistemleri icin kritik [^88^](https://www.digitalapplied.com/blog/qwen-3-5-medium-model-series-benchmarks-pricing-guide)

3. **Llama 4 Scout'un 24GB VRAM'de Turkce performansi:** Llama 4 Scout, 24GB VRAM'de calisan en guclu genel amacli model olarak tanimlaniyor. 10M context ve multimodal yetenekleriyle, Turkce RAG ve dokuman analizi icin ideal bir aday. Ancak CETVEL/TurkBench'de henuz degerlendirilmemis; 17B aktif parametre ile Turkce kulturel bagliligi nasil karsilastirmali? [^85^](https://overchat.ai/ai-hub/best-local-llm)

4. **EXL3 quantization + TabbyAPI uretim kullanimi:** ExLlamaV3 hizla olgunlasiyor ve Qwen 3.5/Gemma 4 icin optimize kernel'ler sunuyor. TabbyAPI'nin "hobi projesi" statusu nedeniyle uretimde kullanim riskleri neler? Alternatif olarak, EXL3 modelleri vLLM'e nasil aktarilabilir? [^121^](https://github.com/turboderp-org/exllamav3)

5. **LocalAI / LocalAGI coklu backend orchestration:** LocalAI, llama.cpp, vLLM, MLX backend'lerinin tamami icin tek bir tool calling abstraction sagliyor. OpenJarvis'in Ollama + vLLM + llama.cpp ile entegre calistigi biliniyor; LocalAI gibi bir abstraction katmani, backend'ler arasi gecis ve failover icin daha sirdurulebilir bir mimari sunabilir mi? [^117^](https://localai.io/features/openai-functions/)
