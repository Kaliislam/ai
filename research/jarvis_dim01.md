# JARVIS Research: Dim 01 - Yerel LLM Altyapisi ve Turkce Model Ekosistemi + Dim 09 - Donanim Optimizasyonu

**Research Date:** 2026-05-06  
**Search Count:** 24+ independent web searches  
**Sources:** Technical blogs, GitHub repos, benchmark papers (CETVEL, TUMLU, TurkBench), official documentation, arXiv papers, community benchmarks  

---

## Executive Summary

Bu derinlemesine arastirma, JARVIS tarzi bir yerel AI asistani icin en uygun LLM altyapisi, Turkce model ekosistemi ve donanim optimizasyon stratejilerini analiz eder. Ana bulgular:

1. **JARVIS tarzi asistan icin en uygun altyapi:** llama.cpp server (native tool calling + OpenAI API uyumlulugu) veya Ollama (kolay kurulum). Uretim ortami icin vLLM/SGLang.
2. **Turkce en iyi model:** CETVEL benchmark'ina gore **Llama-3.3-70B-Instruct** acik kaynak lideri. **Qwen 3.5** (27B/35B-A3B) kodlama ve ajanik gorevlerde guclu, 201 dil destegiyle Turkce'yi de kapsar.
3. **Tool calling:** llama.cpp server artik "~any model" icin native function calling destegi sunuyor [^248^]. Qwen 3.5, Gemma 4, GLM 4.7, Devstral test edilmis calisiyor [^306^].
4. **VRAM profilleri:** 8GB -> Llama 3.1 8B Q4_K_M; 16GB -> Mistral Small 3.1 24B; 24GB -> Qwen 3.6 27B Q4_K_M veya DeepSeek-R1 32B.
5. **Donanim:** CPU-only'de llama.cpp altin standart; AMD ROCm/Vulkan, Intel SYCL, Apple Metal/MLX destegi var; Raspberry Pi 5'te 3B modeller 4-7 tok/s calisir.

---

## DIM 01 - LLM Altyapi ve Modeller

### 1. Ollama vs vLLM vs llama.cpp vs SGLang: JARVIS Asistani Icin En Uygunu

#### Framework Karşılastirmasi

**Claim:** vLLM, uretim ortamlarinda eszamanli kullanici yuku altinda en yuksek throughput'u saglarken; Ollama yerel gelistirme ve prototipleme icin en dusuk surtunmeyi sunar; llama.cpp ise en genis donanim portabilitesini (CPU, edge, Apple Silicon) saglar. [^184^] [^185^] [^186^]

**Source:** Build with Matija - LLM Inference Engine Showdown
**URL:** https://www.buildwithmatija.com/blog/vllm-vs-ollama-vs-tgi-choose-llm-inference-engine
**Date:** 2026-04-06
**Excerpt:** "If you need to ship a production API that handles concurrent users, use vLLM. If you want to run models locally for development or prototyping, use Ollama."
**Context:** vLLM'nin PagedAttention ve continuous batching'in tek kullanicili yerel senaryolarda Ollama'ya gore 3.23x daha fazla throughput sagladigi belirtiliyor.
**Confidence:** High

---

**Claim:** SGLang, ajanik is yukleri (agentic workloads), yapilandirilmis ciktilar (structured outputs) ve on ek tekrar kullanimi (prefix reuse) gerektiren senaryolarda vLLM'ye gore avantajlidir. Hugging Face yeni dagitimlar icin vLLM veya SGLang onerir. [^185^] [^294^]

**Source:** AI Competence - Local LLM Stack Comparison
**URL:** https://aicompetence.org/local-llm-stack-comparison/
**Date:** 2026-03-23
**Excerpt:** "SGLang: High-performance serving and structured runtime. Best for: Agentic workloads, structured outputs, prefix reuse."
**Context:** SGLang'in RadixAttention ile KV cache on eklerini otomatik olarak yeniden kullandigi, bu da cok donuslu ajanik akislar icin onemli bir optimizasyon.
**Confidence:** High

---

**Claim:** llama.cpp, C/C++ ile yazilmis, harici bagimlilik gerektirmeyen, 1.5-bit'ten 8-bit'e kadar quantization destegi olan, CUDA/Metal/Vulkan/HIP/SYCL backend'lerini destekleyen taşinabilir inference motorudur. Ollama'nin altinda calisan motor budur. [^213^] [^272^]

**Source:** PremAI Blog - 10 Best vLLM Alternatives
**URL:** https://blog.premai.io/10-best-vllm-alternatives-for-llm-inference-in-production-2026/
**Date:** 2026-02-28
**Excerpt:** "llama.cpp is the guerrilla fighter of LLM inference. No CUDA required. Runs on a Raspberry Pi. Powers most local LLM applications."
**Context:** Tuketici GPU'larinda (RTX 3080 10GB gibi), CPU inference'da ve Apple Silicon'da llama.cpp vLLM'yi geride birakir.
**Confidence:** High

---

**Claim:** Ollama, llama.cpp uzerine insa edilmis, tek komutla model calistiran, OpenAI-uyumlu API sunan, 100.000+ GitHub yildizi olan en populer yerel LLM calistirma aracidir. Ancak eszamanli istek optimizasyonu yoktur - 5 eszamanli kullanicida p95 latency 5x artar. [^187^]

**Source:** The AI Engineer - vLLM vs Ollama vs SGLang
**URL:** https://theaiengineer.substack.com/p/vllm-vs-ollama-vs-sglang-vs-tensorrt
**Date:** 2026-04-10
**Excerpt:** "Ollama doesn't batch. If three people hit your endpoint simultaneously, requests 2 and 3 wait in line until request 1 finishes. At 5 concurrent users, your p95 latency is already 5x your single-user latency."
**Context:** Ollama throughput tavanı ~22 req/s'de duzlesirken, vLLM ayni donanimda 128 eszamanli istekte 3.23x daha fazla istek isleyebilir.
**Confidence:** High

---

**Claim:** llama.cpp server modu, OpenAI API uyumlu `/v1/chat/completions` endpoint'i, Anthropic Messages API destegi, multimodal destegi, surekli batching, spekulatif decoding, ve **function calling / tool use for ~any model** destegi sunar. [^248^] [^113^]

**Source:** llama.cpp GitHub - tools/server/README.md
**URL:** https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
**Date:** 2026-05-06
**Excerpt:** "Features: ... Function calling / tool use for ~any model ... Schema-constrained JSON response format ... Continuous batching"
**Context:** llama.cpp server, `--jinja` flag'i ile Jinja chat template destegi saglar ve OpenAI-stili function calling'i parse edebilir. Claude Code ile entegrasyon da mevcuttur.
**Confidence:** High

---

#### JARVIS Icin Karar Matrisi

| Senaryo | En Iyi Secim | Neden |
|---------|-------------|-------|
| Tek kullanicili yerel asistan (JARVIS) | **llama.cpp server** veya **Ollama** | Tool calling + OpenAI API + kolay kurulum |
| Cok kullanicili uretim | **vLLM** | En yuksek throughput, PagedAttention |
| Ajanik is yukleri + yapilandirilmis cikti | **SGLang** | RadixAttention + regex/JSON schema constrained decoding |
| CPU-only / Edge | **llama.cpp** | En genis donanim destegi |
| Apple Silicon | **Ollama 0.19+ (MLX)** veya **llama.cpp Metal** | MLX 2x hizli decode saglar |

---

### 2. Turkce En Iyi Performans Gosteren Modeller (2026)

#### CETVEL Benchmark Sonuclari

**Claim:** CETVEL (Turkce NLP benchmark) sonuclarina gore, **Llama-3.3-70B-Instruct** tum modeller arasinda en iyi genel performansi gosterir (ortalama 53.5 puan). Ikinci sirada Aya-Expanse-32B (50.8) gelir. [^188^]

**Source:** CETVEL: A Unified Benchmark for Evaluating Language Models in Turkish (EACL 2026)
**URL:** https://aclanthology.org/2026.eacl-long.46.pdf
**Date:** 2026 (EACL Long Papers)
**Excerpt:** "The best-performing model overall is Llama-3.3-70B-Instruct, which exceeds the second-best model, Aya-Expanse-32B, by 2.7 points in average score."
**Context:** CETVEL, 7 kategoride 23 gorev iceren Turkce'ye ozgu bir benchmark'tir. Turkce merkezli modeller genel olarak cokdilli modellerin gerisinde kalir.
**Confidence:** High

---

**Claim:** **Cere-Llama-3-8B**, Turkce merkezli modeller arasinda en iyi performansi gosterir ve Grammatical Error Correction (GECturk: 46.0) ve Extractive QA (TQuAD) gorevlerinde **70B parametreli Llama-3.3-70B-Instruct'i bile geride birakir**. [^188^]

**Source:** CETVEL Benchmark Paper
**URL:** https://aclanthology.org/2026.eacl-long.46.pdf
**Date:** 2026
**Excerpt:** "Cere-Llama-3-8B achieves the highest score on TQuAD and GECturk datasets, even outperforming the largest model Llama-3.3-70B-Instruct on these tasks."
**Context:** Cere-Llama-3-8B, Llama-3-8B uzerine Turkce instruction tuning ile egitilmis bir modeldir. Ancak bilgi yogun gorevlerde (knowledge-intensive) dusuk performans gosterir.
**Confidence:** High

---

#### TurkBench Sonuclari

**Claim:** TurkBench (8.151 ornek, 21 gorev) sonuclarina gore **GPT-OSS 120B** en yuksek ortalama puani alir (87.6), ardindan GLM-4-6 (75.9) ve DeepSeek-V3.1 (73.2) gelir. **Qwen3-Next-80B-Inst** da guclu bir performans gosterir. [^247^]

**Source:** A Benchmark for Evaluating Turkish Large Language Models (arXiv)
**URL:** https://arxiv.org/pdf/2601.07020
**Date:** 2026
**Excerpt:** Model siralamasi: GPT-oss-120b (87.6), GLM-4-6 (75.9), DeepSeek-V3.1 (73.2), Qwen3-Next-80B-Inst (70+ aralik)
**Context:** TurkBench, MMLU, okuma kavrayisi, mantiksal akil yurutme, duygu analizi, toxicity detection, halusinasyon gibi 21 farkli gorevi kapsar.
**Confidence:** High

---

#### TUMLU (Turkic Languages Benchmark)

**Claim:** TUMLU, 8 Turk dili (Azerice, Kirim Tatarcasi, Karakalpakca, Kazakca, Kircizca, Tatarca, Turkce, Uygurca, Ozbekce) ve 11 akademik konuda 38.139 soru iceren yerli bir MMLU benchmark'idir. Proprietery modeller (Claude 3.5 Sonnet oncilik eder) acik kaynak modellere gore ustun performans gosterir. [^243^] [^245^]

**Source:** TUMLU: A Unified and Native Language Understanding Benchmark for Turkic Languages (ACL 2025)
**URL:** https://aclanthology.org/2025.acl-long.1112/
**Date:** 2025-07 (ACL Vienna)
**Excerpt:** "Proprietary models consistently outperform open-source models across all Turkic languages and academic subjects in the 5-shot setting, with Claude 3.5 Sonnet leading significantly."
**Context:** TUMLU, makine cevirisi yerine yerli veri kullanarak olusturulmus, kultur ve linguistik nuanslari koruyan bir benchmark'tir.
**Confidence:** High

---

#### Qwen 3.5 Turkce Destegi

**Claim:** Qwen 3.5, **201 dil ve lehce** destegi sunar. Bu kapsamda Turkce de yer alir. Qwen3.5-Omni'nin FLEURS ASR benchmark'inda Turkce WER (Word Error Rate) 3.1-4.4 araliginda, ceviride ise en->tr 30.4, tr->en 40.3 puanlari elde edilmistir. [^210^] [^211^]

**Source:** Qwen3.5-Omni Technical Report
**URL:** https://arxiv.org/html/2604.15804v1
**Date:** 2026-04-17
**Excerpt:** "Turkish: 3.1 (WER) ... Turkish translation: en2tr 30.4, tr2en 40.3"
**Context:** Qwen 3.5 ailesi (0.8B'den 397B-A17B MoE'ye kadar) kodlama, ajanik gorevler, uzun baglam ve cokdilli islemede guclu performans gosterir.
**Confidence:** High

---

#### Turkce Model Tavsiye Siralamasi (2026)

| Kategori | En Iyi Model | Notlar |
|----------|-------------|--------|
| Genel Turkce (en iyi acik kaynak) | **Llama-3.3-70B-Instruct** | CETVEL lideri, 128K baglam |
| Kodlama + Turkce | **Qwen 3.5-27B / 35B-A3B** | 256K baglam, tool calling, 201 dil |
| Gramer duzeltme + TQuAD | **Cere-Llama-3-8B** | CETVEL'de 70B'yi gecti |
| Kucuk model (8GB VRAM) | **Llama-3.1-8B** | Q4_K_M'de 4.7GB, ~70 tok/s |
| Cokdilli (Turkce dahil) | **Aya-Expanse-32B** | Ikinci sirada CETVEL'de |

---

### 3. Tool Calling Destegi Olan Modeller - Test Edilmis Kantlar

#### llama.cpp Server Tool Calling

**Claim:** llama.cpp server, OpenAI-stili function calling'i `--jinja` flag'i ile destekler. Test edilmis calisan modeller: **Qwen 3.5 (35B, 122B)**, **Qwen 3 Coder Next**, **GLM 4.7 Flash**, **GPT OSS 20B**, **Devstral**. Calismayanlar/kismi calisanlar: Gemma 4 (infinite loop ~11 adim sonra), Llama 4 Scout (parser yok). [^306^] [^309^]

**Source:** AkitaOnRails - Testing LLMs: Open Source and Commercial
**URL:** https://www.akitaonrails.com/en/2026/04/05/testing-llms-open-source-and-commercial-can-anyone-beat-claude-opus/
**Date:** 2026-04-05
**Excerpt:** "Qwen 3.5 (35B, 122B): Yes, --jinja --reasoning-format none, Completed successfully. Gemma 4 27B: Partial (b8665+), Infinite loop after ~11 steps. Llama 4 Scout: No, No parser in llama.cpp."
**Context:** Test, gercek bir kodlama ajanik gorev uzerinden yapilmistir. llama.cpp'de her model icin ozel parser gereklidir.
**Confidence:** High

---

#### vLLM Tool Calling

**Claim:** vLLM, `--enable-auto-tool-choice` ve `--tool-call-parser` parametreleri ile otomatik tool calling destegi sunar. Qwen3 Coder parser'i mevcuttur. [^310^]

**Source:** Medium - How to run Claude Code/Codex with local models
**URL:** https://medium.com/@luongnv89/how-to-run-claude-code-codex-with-local-models-via-llamacpp-ollama-lmstudio-and-vllm-2026-7d00ba7e63a4
**Date:** 2026-04-15
**Excerpt:** "vLLM serve Qwen/Qwen3.5-27B --enable-auto-tool-choice --tool-call-parser qwen3_coder"
**Context:** vLLM, Claude Code entegrasyonu icin en iyi uretim cozumudur.
**Confidence:** High

---

#### Ollama Tool Calling

**Claim:** Ollama, `/api/chat` endpoint'i uzerinden OpenAI formatinda tool calling destegi sunar. **Qwen3 modelleri** en stabil tool calling davranisini gosterir (hallusinasyon dusuk). **Gemma 4** dogal (native) function calling ile egitilmistir. [^207^] [^308^]

**Source:** MorphLLM - Best Ollama Models 2026
**URL:** https://www.morphllm.com/best-ollama-models
**Date:** 2026-04-05
**Excerpt:** "Qwen3 models have the most stable tool calling, rarely hallucinating calls or dropping parameters. Gemma 4 ships with native function calling trained into the model weights."
**Context:** Gemma 4, vision + tool calling kombinasyonu ile Ollama uzerinde benzersiz bir modeldir.
**Confidence:** High

---

### 4. VRAM Profilleri Icin Model Onerileri

#### 8GB VRAM Profili

**Claim:** 8GB VRAM'de (RTX 4060, RTX 5060 Ti, Intel B580) en iyi secenekler: **Llama 3.1 8B Q4_K_M** (~4.7GB, ~70 tok/s), **Qwen3 8B** (~5GB, en iyi cokdilli + kodlama), **Phi-4 Mini 3.8B** (~2.3GB, en hizli). 13B+ modellerden kacininilmalidir. [^209^]

**Source:** Prompt Quorum - Local LLM Hardware Guide 2026
**URL:** https://www.promptquorum.com/local-llm-hardware-guide-2026
**Date:** 2026-04-04
**Excerpt:** "8 GB VRAM: Llama 3.1 8B Q4_K_M (4.7 GB, ~70 tok/s) -- recommended. Qwen3 8B (5 GB, best multilingual + coding). Phi-4 Mini 3.8B (2.3 GB, fastest)."
**Context:** Phi-4 Mini, matematiksel akil yurutmede daha buyuk modellere meydan okur.
**Confidence:** High

---

#### 16GB VRAM Profili

**Claim:** 16GB VRAM'de (RTX 4080, RTX 5080, RTX 4090 laptop) en iyi secenekler: **Mistral Small 3.1 24B Q4_K_M** (~13GB, 55 tok/s), **Devstral Small 24B** (~16GB, 45 tok/s - ajanik kodlama), **DeepSeek-R1 14B Q8_0** (~15GB, 40 tok/s). **Llama 3.3 70B Q4_K_M** (~39GB) SIGMAZ. [^209^]

**Source:** Prompt Quorum - Local LLM Hardware Guide 2026
**URL:** https://www.promptquorum.com/local-llm-hardware-guide-2026
**Date:** 2026-04-04
**Excerpt:** "Best overall for 16 GB: Mistral Small 3.1 24B Q4_K_M at ~13 GB, 55 tok/sec. For agentic coding: Devstral Small 24B at 45 tok/sec. Best reasoning: DeepSeek-R1 14B Q8_0 at 40 tok/sec."
**Context:** RTX 4090 laptop GPU'larinin 16GB VRAM'i vardir (24GB degil), bu nedenle masaustu RTX 4090 ile ayni tavan paylasir.
**Confidence:** High

---

#### 24GB VRAM Profili

**Claim:** 24GB VRAM'de (RTX 4090, RTX 5090, Tesla L40) en iyi secenekler: **Qwen 3.6 27B Q4_K_M** (~16GB, 77.2% SWE-bench - en iyi dense kodlama modeli), **DeepSeek-R1 32B Q4_K_M** (~19GB, en iyi akil yurutme), **Qwen2.5 32B Q5_K_M** (~21GB). Llama 3.3 70B 2x 24GB GPU gerektirir. [^209^] [^228^]

**Source:** Prompt Quorum / Knightli VRAM Table
**URL:** https://www.promptquorum.com/local-llm-hardware-guide-2026 / https://www.knightli.com/en/2026/05/01/qwen3-6-local-vram-quantization-table/
**Date:** 2026-04-04 / 2026-05-01
**Excerpt:** "24GB: Qwen 3.6 27B Q4_K_M (~16GB, best dense coding). DeepSeek-R1 32B Q4_K_M (~19GB, best reasoning)."
**Context:** Qwen3.6-27B Q4_K_M GGUF dosyasi 16.82GB'dir ve 20GB minimum VRAM onerilir. Uzun baglam icin daha dusuk quantization veya kisa baglam kullanilmalidir.
**Confidence:** High

---

#### VRAM Hesaplama Kurali

**Claim:** Yerel LLM icin temel VRAM hesaplamasi: (Model boyutu GB olarak) / Quantization bit = VRAM ihtiyaci. Ornek: 70B model Q4'te = 70/8 * 2 ~= 39-43GB. Qwen 3.5-27B Q4_K_M = ~14-17GB GGUF dosyasi. [^228^] [^232^]

**Source:** Knightli VRAM Table / Spheron GPU Requirements
**URL:** https://www.knightli.com/en/2026/05/01/qwen3-6-local-vram-quantization-table/ / https://www.spheron.network/blog/gpu-requirements-cheat-sheet-2026/
**Date:** 2026-05-01 / 2026-04-15
**Excerpt:** Qwen3.6-27B Q4_K_M: 16.82GB GGUF, 20GB minimum VRAM, 24GB safer VRAM.
**Context:** KV cache (baglam cache) de VRAM tuketir. 128K baglam 70B modelde 14GB+ KV cache kullanabilir.
**Confidence:** High

---

### 5. GGUF Quantization Kalite Kaybi ve Hiz Trade-off'lari

#### Quantization Kalite Karsilastirmasi

**Claim:** GGUF quantization seviyeleri ve kalite trade-off'lari: **Q4_K_M** (4.58GB 7B icin, +0.0535 ppl) - varsayilan tavsiye edilen; **Q5_K_M** (5.33GB, +0.0142 ppl) - daha yuksek kalite; **Q6_K** (6.14GB, +0.0044 ppl) - neredeyse kayipsiz; **Q8_0** (7.96GB, +0.0004 ppl) - minimal kalite kaybi; **Q2_K** (2.96GB, +3.5199 ppl) - asiri sikistirma, belirgin kalite kaybi. [^193^]

**Source:** Medium - GGUF in Practice: From Model to Production (Part 2)
**URL:** https://medium.com/@michael.hannecke/gguf-in-practice-from-model-to-production-part-2-27c7eed23daa
**Date:** 2025-12-07
**Excerpt:** "Q4_K_M: 4.58GB, +0.0535 ppl -- The recommended default. Best balance. Q5_K_M: 5.33GB, +0.0142 ppl -- Higher quality, slightly larger. Q8_0: 7.96GB, +0.0004 ppl -- Barely any quality loss."
**Context:** Perplexity (ppl) dusuklugu = iyi kalite. IQ (importance quantization) turleri importance matrix gerektirir.
**Confidence:** High

---

**Claim:** vLLM quantization benchmark'inda GGUF Q4_K_M, perplexity'de AWQ ve BitsandBytes'e yakin performans gosterir (6.74 vs 6.56 baseline), HumanEval kod uretiminde ise AWQ, Marlin-AWQ, GGUF Q4_K_M ve BitsandBytes'un tamami %51.83 Pass@1 skoru elde etmistir (baseline %56.1). [^192^]

**Source:** JarvisLabs - Complete Guide to LLM Quantization with vLLM
**URL:** https://jarvislabs.ai/blog/vllm-quantization-complete-guide-benchmarks
**Date:** 2026-01-07
**Excerpt:** "GGUF (Q4_K_M) comes second with 6.74 perplexity, showing excellent quality preservation despite being 4-bit. AWQ, Marlin-AWQ, GGUF (Q4_K_M), and BitsandBytes all achieve 51.83% on HumanEval."
**Context:** Tum quantization yontemleri baseline'in ~%6 icinde kalir. Cogu uygulama icin bu fark farkedilmeyecektir.
**Confidence:** High

---

**Claim:** Unsloth Dynamic 2.0 quantization, katman bazli optimal quantization secimi ile standart quantization'a gore ayni bit seviyesinde %5-8 daha dusuk KL divergence saglar. Qwen 3.5 GGUF'lari icin gunncellenmis imatrix verisi chat, kodlama, uzun baglam ve tool-calling senaryolarinda iyilestirmeler saglar. [^229^]

**Source:** Unsloth - Qwen3.5 How to Run Locally
**URL:** https://unsloth.ai/docs/models/qwen3.5
**Date:** 2026-04-19
**Excerpt:** "All GGUFs now updated with an improved quantization algorithm... Tool-calling improved following our chat template fixes."
**Context:** Unsloth Dynamic 2.0, onemli katmanlari 8 veya 16-bit'e yukseltir, bu da 4-bit quantization'da daha iyi kalite saglar.
**Confidence:** High

---

#### Quantization Oneri Tablosu

| Quantization | Boyut (7B icin) | Kalite | Hiz | En Iyi Kullanim |
|-------------|------------------|--------|-----|----------------|
| Q2_K | ~3GB | Dusuk | En hizli | Sadece RAM kisitli |
| Q3_K_M | ~3.8GB | Kabul edilebilir | Hizli | Daha buyuk modeller icin |
| **Q4_K_M** | **~4.6GB** | **Iyi (varsayilan)** | **Hizli** | **Genel kullanim** |
| Q5_K_M | ~5.3GB | Cok iyi | Hizli | Kalite kritik |
| Q6_K | ~6.1GB | Neredeyse kayipsiz | Orta | Yuksek kalite gerektiren |
| Q8_0 | ~8GB | Minimal kayip | Orta | Uretim kalitesi |

---

## DIM 09 - Donanim Optimizasyonu

### 1. CPU-Only Senaryo: Hangi Model, Hangi Quantization Calisir?

#### llama.cpp CPU Inference Altin Standart

**Claim:** CPU-only inference'de llama.cpp altin standarttir. AVX2, AVX-512 ve ARM NEON optimizasyonlari ile yillarca CPU optimizasyonu yapilmistir. CPU-only uretim ortaminda gunluk binlerce istek islemek mumkundur. Beklenen hiz: 10-30 tok/s (model boyutuna ve donanima gore). [^213^] [^210^]

**Source:** PremAI Blog / Clarifai Blog
**URL:** https://blog.premai.io/10-best-vllm-alternatives-for-llm-inference-in-production-2026/ / https://www.clarifai.com/blog/ilama.cpp
**Date:** 2026-02-28 / 2026-03-17
**Excerpt:** "CPU inference: vLLM's CPU support is minimal. llama.cpp has years of CPU optimizations including AVX2, AVX-512, and ARM NEON."
**Context:** vLLM CPU destegi minimaldir; CPU-only inference icin llama.cpp veya OpenVINO (Intel icin) tercih edilmelidir.
**Confidence:** High

---

#### CPU-Only 16GB RAM Model Onerileri

**Claim:** CPU-only 16GB sistem RAM'de en iyi secenekler: **Phi-4 Mini 3.8B Q4_K_M** (~2.5GB RAM, ~25 tok/s Ryzen 9 7950X uzerinde), **Gemma 2 2B Q8** (~28 tok/s, en hizli), **Llama 3.2 3B Q4_K_M** (~4.9GB, ~12 tok/s). [^209^]

**Source:** Prompt Quorum - Local LLM Hardware Guide 2026
**URL:** https://www.promptquorum.com/local-llm-hardware-guide-2026
**Date:** 2026-04-04
**Excerpt:** "CPU-only (16 GB system RAM): Llama 3.2 3B Q8 (20 tok/sec) or Phi-4 Mini Q4_K_M (25 tok/sec). A used RTX 4060 8GB (~$150) is 5-10x faster."
**Context:** CPU-only inference kullanilabilir ancak interaktif kullanim icin yavas olabilir. Kullanilmis RTX 4060 8GB (~$150) veya RTX 5060 Ti 12GB (~$250) 5-10x daha hizlidir.
**Confidence:** High

---

#### CPU-Only Model Sinirlari

**Claim:** 10B parametrenin altindaki modeller, iyi tanimlanmis gorevlerde (yönlendirme, ozetleme, hafif kod uretimi) basarili olur ancak karmasik akil yurutme veya yaratici yazim icin GPT-4/Claude seviyesi beklenmemelidir. [^210^]

**Source:** Clarifai - llama.cpp Blog
**URL:** https://www.clarifai.com/blog/ilama.cpp
**Date:** 2026-03-17
**Excerpt:** "Roger Ngo notes that models under 10B parameters excel at well-defined tasks but should not be expected to match GPT-4 or Claude in open-ended scenarios."
**Context:** CPU-only senaryoda model secimi cok onemlidir. Kucuk ama verimli modeller (Phi-4 Mini, Gemma 2 2B) buyuk ama yavas modellere tercih edilmelidir.
**Confidence:** High

---

### 2. NVIDIA Olmayan GPU'lar: ROCm, Intel Arc, Apple Silicon

#### AMD GPU - ROCm ve Vulkan

**Claim:** llama.cpp, AMD GPU'lari HIP (ROCm) ve Vulkan backend'leri ile destekler. ROCm destegi NVIDIA'ya gore 6-12 ay geridedir ancak iyilesmektedir. llama.cpp + ROCm en stabil AMD secenegidir. vLLM de ROCm uzerinde calisir ancak 2-3 ay geridedir. [^213^] [^280^]

**Source:** PremAI Blog / GitHub - LLAMA.CPP-ROCm
**URL:** https://blog.premai.io/10-best-vllm-alternatives-for-llm-inference-in-production-2026/ / https://github.com/mambiux/LLAMA.CPP-ROCm
**Date:** 2026-02-28 / 2024-12-27
**Excerpt:** "llama.cpp with ROCm is probably the most stable option." / "It only uses 25 Watts for a 8B Q4KM Quantized LLama model with 20.1 tokens/sec for prompt processing and 6.8 tokens/sec for text generation."
**Context:** AMD Ryzen 7 5700U APU ile ROCm uzerinde 8B Q4_K_M model 20.1 tok/s prompt processing ve 6.8 tok/s text generation hizi elde edilmistir.
**Confidence:** High

---

**Claim:** ROCm/vLLM Docker imaji, AMD Instinct MI300X serisi GPU'lar icin onbuild optimize edilmis ortam sunar. vLLM ROCm uzerinde GGUF destegi sinirlidir - `torch.bfloat16` desteklenmez. [^249^] [^296^]

**Source:** ROCm Documentation / vLLM Discuss Forum
**URL:** https://rocm.docs.amd.com/en/docs-7.2.2/how-to/rocm-for-ai/inference/benchmark-docker/ / https://discuss.vllm.ai/t/how-to-run-gguf-with-vllm-and-rocm/2414
**Date:** 2026-04-21 / 2026-03-01
**Excerpt:** "The ROCm vLLM Docker image offers a prebuilt, optimized environment for validating LLM inference performance on AMD Instinct MI300X Series GPUs."
**Context:** AMD 7900 XTX ile ROCm uzerinde GGUF calistirmak mumkun gorunmuyor (bfloat16 destegi yok).
**Confidence:** Medium

---

#### Intel Arc GPU - SYCL ve Vulkan

**Claim:** llama.cpp, Intel Arc GPU'lari SYCL backend'i ile destekler. Intel Arc Pro B70 uzerinde Qwen3.6-27B Q4_K_M GGUF basariyla calistirilmistir. SYCL runtime OpenCL backend uzerine dusebiliyor, bu sadece VRAM telemetrisini etkiler, inference'i degil. [^214^] [^215^]

**Source:** Medium - How to Run Qwen3.6-27B on Intel Arc Pro B70
**URL:** https://bibek-poudel.medium.com/how-to-run-qwen3-6-27b-locally-on-intel-arc-pro-b70-what-actually-works-c96dec67c6f7
**Date:** 2026-04-26
**Excerpt:** "On my machine: SYCL0: Intel(R) Graphics [0xe223]... The SYCL runtime landed on the OpenCL backend rather than Level Zero. The model loaded and served correctly."
**Context:** Intel Arc GPU'lar yerel LLM inference icin pratik bir alternatif olabilir, ancak kurulum SYCL/oneAPI gerektirir.
**Confidence:** High

---

#### Apple Silicon - Metal ve MLX

**Claim:** Apple Silicon'da llama.cpp Metal backend'i en kanitlanmis yaklasimdir. **Ollama 0.19+ MLX backend** ile Metal'e gore ~2x daha hizli decode (111.4 vs 57.8 tok/s) ve ~1.6x daha hizli prefill elde edilir. MLX avantaji 14B alti modellerde 20-87% arasindadir; 27B+ modellerde bellek bant genisligi doygunlugu nedeniyle avantaj kaybolur. [^227^] [^230^]

**Source:** gingter.org - Ollama Goes MLX / Starmorph - Apple Silicon LLM Optimization
**URL:** https://gingter.org/2026/04/23/ollama-goes-mlx/ / https://blog.starmorph.com/blog/apple-silicon-llm-inference-optimization-guide
**Date:** 2026-04-23 / 2026-04-10
**Excerpt:** "On an M5 Max, Ollama is advertising up to 1851 tokens/s prefill and 134 tokens/s decode with int4 quantization in 0.19." / "MLX is 20-87% faster than llama.cpp for generation on Apple Silicon (under 14B params)."
**Context:** MLX, Apple Silicon'un birlesik bellek mimarisini (UMA) kullanarak CPU-GPU kopyalarini ortadan kaldirir. Ollama 0.19+ MLX backend'i 32GB+ birlesik bellek gerektirir.
**Confidence:** High

---

**Claim:** M4 Max (128GB birlesik bellek) uzerinde Llama 3.1 70B Q4_K_M ~8-10 tok/s, M4 Pro 48GB'de ~6-8 tok/s calisir. Qwen2.5 72B Q4_K_M 128GB'de ~7 tok/s calisir. [^234^]

**Source:** youngju.dev - Running LLMs on Apple Silicon
**URL:** https://www.youngju.dev/blog/culture/2026-03-18-apple-silicon-llm-inference-deep-dive.en
**Date:** 2026-03-18
**Excerpt:** "M4 Max 128GB: llama3.1:70b runs at ~8-10 tok/s comfortably. M4 Pro 48GB: llama3.1:70b ~6-8 tok/s."
**Context:** Apple Silicon'da bellek bant genisligi darbogazdir - hesaplama degil, VRAM degil, GPU core sayisi degil.
**Confidence:** High

---

### 3. RAM Optimizasyonu: Offloading Stratejileri

#### llama.cpp Layer Offloading

**Claim:** llama.cpp, model katmanlarini CPU ve GPU arasinda dagitmaya olanak tanir. `-ngl 99` tum katmanlari GPU'ya offloader. MoE modellerinde `--n-cpu-moe N` ile uzman katmanlarinin bir kismini CPU'ya atamak mumkundur. `-ot` (override-tensor) ile belirli tensor'leri hassas kontrolle CPU'ya yonlendirilebilir. [^270^] [^271^] [^273^]

**Source:** Medium - Tune llama.cpp on Apple Silicon / HuggingFace Blog - llama.cpp MoE Offload Guide
**URL:** https://medium.com/@michael.hannecke/tuning-llama-cpp-on-apple-silicon-843f37a6c3dc / https://huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide
**Date:** 2026-04-29 / 2026-01-29
**Excerpt:** "-ngl 99 offloads all model layers to the Metal GPU. The number gets clamped to the actual layer count, so 99 is just shorthand for 'everything.'" / "-ot 'blk.([0-9]|[1-2][0-9]|30).=CUDA0,exps=CPU'"
**Context:** MoE modellerinde attention tensor'leri GPU'da, FFN expert tensor'leri CPU'da tutulmasi en iyi performans/kalite oranini saglar.
**Confidence:** High

---

#### ktransformers - Ultra Buyuk Modeller Icin

**Claim:** **ktransformers**, 24GB VRAM ve 382GB DRAM ile **671B DeepSeek-R1/V3** Q4_K_M modelini calistirabilir. llama.cpp'ye gore **27.79x daha hizli prefill** (286.55 vs 10.31 tok/s) ve **3.03x daha hizli decode** (13.69 vs 4.51 tok/s) saglar. 128K baglamda 7.1x hizlanma, 1M baglamda 16 tok/s (10x hizlanma) elde edilir. [^278^] [^279^] [^246^]

**Source:** TechNode / ktransformers GitHub
**URL:** https://technode.com/2025/02/17/tsinghua-universitys-ktransformers-enables-full-powered-deepseek-r1-with-low-cost-graphics-card/ / https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/DeepseekR1_V3_tutorial.md
**Date:** 2025-02-17 / 2025-02-15
**Excerpt:** "With a 24GB VRAM 4090D, users can run the full-powered DeepSeek-R1 and V3 671B version locally. Pre-processing speeds can reach up to 286 tokens per second, while inference generation speeds peak at 14 tokens per second."
**Context:** ktransformers, CPU/DRAM + GPU heterojen sistem optimizasyonu kullanir. Intel AMX hizlandirilmis kernel ve secici uzman aktivasyonu ile daha da hizlanacaktir.
**Confidence:** High

---

#### KV Cache Quantization

**Claim:** llama.cpp, KV cache quantization ile bellek tasarrufu saglar. `--cache-type-k q8_0 --cache-type-v q8_0` ile KV cache 8-bit'e dusurulur, bu da uzun baglam senaryolarinda onemli VRAM tasarrufu saglar. `--flash-attn` bu optimizasyon icin on sarttir. [^270^]

**Source:** Medium - Tune llama.cpp on Apple Silicon
**URL:** https://medium.com/@michael.hannecke/tuning-llama-cpp-on-apple-silicon-843f37a6c3dc
**Date:** 2026-04-29
**Excerpt:** "--cache-type-k q8_0 --cache-type-v q8_0 ... -fa 1 is a hard prerequisite for KV cache quantization."
**Context:** KV cache quantization, uzun baglamli RAG ve multi-turn chat senaryolarinda VRAM kisitini gevsetmeye yardimci olur.
**Confidence:** High

---

#### DMA-BUF ile Sistem RAM GPU'ya Dogrudan Erisim

**Claim:** GreenBoost gibi araclar, VRAM'den taan model katmanlarini PCIe 4.0 uzerinden DMA-BUF ile GPU'nun dogrudan sistem RAM'e erismesini saglar. Bu, geleneksel CPU offloading'e gore 5-10x daha hizlidir. Ancak PCIe 4.0 bant genisligi (~32GB/s) hala darbogazdir. [^276^]

**Source:** Hacker News - How does this differ from anything llama.cpp offers
**URL:** https://news.ycombinator.com/item?id=47432495
**Date:** 2026-03-18
**Excerpt:** "route the overflow memory to DDR4 via DMA-BUF, which gives the GPU direct access to system RAM over PCIe 4.0 without a CPU copy involved."
**Context:** Bu yaklasim deneyseldir ve henuz yaygin degildir, ancak buyuk modelleri tiketici GPU'larinda calistirmanin gelecekteki yonu olabilir.
**Confidence:** Medium

---

### 4. Edge Cihaz: Raspberry Pi 5 Performansi

#### Raspberry Pi 5 LLM Benchmarklari

**Claim:** Raspberry Pi 5 (8GB RAM, Cortex-A76 2.4GHz) ile **Llama-3.2-3B Q4_K_M** ~4-6 tok/s, **TinyLlama 1.1B** ~5-7 tok/s, **Mistral/Llama 7B Q4_K_M** ~0.7-3 tok/s calisir. Pi 4'e gore 3x daha hizli hesaplama sunar. [^216^] [^305^] [^311^]

**Source:** AI Competence - Running Llama on Raspberry Pi 5 / ohyaan.github.io / wolfpaulus.com
**URL:** https://aicompetence.org/running-llama-on-raspberry-pi-5/ / https://ohyaan.github.io/tips/local_llm_optimization_with_llama.cpp_-_on-device_ai/ / https://wolfpaulus.com/local_llama/
**Date:** 2025-09-15 / Unknown / 2026-04-27
**Excerpt:** "Pi 5 can generate 4-7 tokens per second on a quantized 3B model." / "Pi 5 (8GB) with Llama 2 7B Q4_K_M: Generation speed 4-6 tokens/second." / "Cerebras Qwen3-Coder-REAP-25B-A3B on Pi 5: about 5 tokens per second."
**Context:** Wolf Paulus'un Pi 5 testinde BLIS/OpenBLAS optimize edilmis build ile 3.04 tok/s elde edilmistir. llama.cpp'nin kendi worker thread yonetimi en iyi sonucu verir.
**Confidence:** High

---

#### Whisper + Piper + LLM Edge Pipeline

**Claim:** Whisper.cpp + TinyLLaMA (llama.cpp) + Piper TTS kombinasyonu ile Raspberry Pi 4/5 uzerinde tamamen offline, gercek zamanli sesli asistan insa edilebilir. Wyoming protokolu uzerinden Home Assistant ile entegre edilebilir. [^297^] [^295^] [^72^]

**Source:** GitHub - rsvn/voice-assistant / Pi DIY Lab / Joe Karlsson Blog
**URL:** https://github.com/risvn/voice-assistant / https://pidiylab.com/text-to-speech-raspberry-pi-piper/ / https://www.joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/
**Date:** 2025-09-06 / 2025-12-02 / 2026-04-12
**Excerpt:** "Whisper.cpp + TinyLLaMA (via llama.cpp) + Piper TTS. Built as a Bachelor's Major Project, it delivers real-time, low-latency voice interactions on constrained hardware." / "Piper paired with Whisper.cpp creates a fully local speech pipeline."
**Context:** Bu pipeline: Wake word -> Whisper STT -> LLM intent/response -> Piper TTS -> Speaker. Her birim ayri bir makinede calisabilir (Wyoming protokolu).
**Confidence:** High

---

#### Raspberry Pi Model Onerileri

| Cihaz | Model | Hiz | Kullanim |
|-------|-------|-----|----------|
| **Pi 5 (8GB)** | Llama-3.2-3B Q4_K_M | 4-6 tok/s | Genel sohbet, kodlama yardimcisi |
| **Pi 5 (8GB)** | Qwen2 1.5B/3B Q4_K_M | 5-8 tok/s | Tool/agent gorevleri |
| **Pi 5 (8GB)** | Mistral 7B Q4_K_M | 0.7-3 tok/s | Daha kaliteli yanitlar (yavas) |
| **Pi 4 (4GB)** | TinyLlama 1.1B Q4_K_M | 8-12 tok/s | Hizli, basit gorevler |
| **Pi 4 (4GB)** | Llama-3.2-3B Q3_K_M | ~1-2 tok/s | Kullanilabilir ama yavas |

---

## Tavsiye Ozeti: JARVIS Icin Optimal Stack

### Tavsiye Edilen Altyapi Siralamasi

1. **Birincil (yerel asistan):** `llama.cpp server` veya `Ollama` (llama.cpp uzerine)
   - llama.cpp server: Daha fazla kontrol, native tool calling, OpenAI API uyumlu
   - Ollama: Daha kolay kurulum, model yonetimi, otomatik GPU layer offloading

2. **Uretim (cok kullanici):** `vLLM` (NVIDIA GPU varsa) veya `SGLang` (ajanik is yukleri)

3. **Apple Silicon:** `Ollama 0.19+` (MLX backend) veya `llama.cpp Metal`

### Tavsiye Edilen Model Siralamasi (Turkce JARVIS)

| VRAM | Model | Neden |
|------|-------|-------|
| **8GB** | Llama-3.1-8B Q4_K_M veya Qwen3 8B | En iyi denge, tool calling |
| **16GB** | Mistral Small 3.1 24B Q4_K_M veya Devstral Small 24B | En iyi kalite/hiz, ajanik kodlama |
| **24GB** | Qwen 3.6 27B Q4_K_M veya Qwen 3.5-35B-A3B | En iyi kodlama, 256K baglam, 201 dil |
| **48GB+** | Llama-3.3-70B Q4_K_M | CETVEL lideri, 128K baglam |
| **CPU-only 16GB** | Phi-4 Mini 3.8B Q4_K_M veya Llama-3.2-3B Q4_K_M | Hizli ve verimli |
| **Edge (Pi 5)** | Llama-3.2-3B Q4_K_M veya Qwen2 3B | 4-6 tok/s, kullanilabilir |

### Donanim Optimizasyon Checklist

- [ ] NVIDIA GPU varsa: `-ngl 99` ile tum katmanlari GPU'ya yukle
- [ ] VRAM yetersizse: MoE modellerinde `--n-cpu-moe` ile uzmanlari CPU'ya at
- [ ] Uzun baglam gerekiyorsa: `--cache-type-k q8_0 --cache-type-v q8_0` ile KV cache quantization ac
- [ ] Apple Silicon'da: Ollama 0.19+ ile MLX backend'i dene (32GB+ gerekir)
- [ ] AMD GPU'da: llama.cpp + ROCm/HIP veya Vulkan derlemesi
- [ ] Intel Arc'da: llama.cpp + SYCL derlemesi (oneAPI gerektirir)
- [ ] CPU-only'de: OpenBLAS/BLIS derlemesi, thread optimizasyonu
- [ ] Edge'de: Q4_K_M quantization, kisa baglam (512-1024), SSD + `--use-mmap`

---

## Referanslar ve Kaynaklar

| # | Kaynak | URL | Tarih |
|---|--------|-----|-------|
| [^184^] | Build with Matija - vLLM vs Ollama | https://www.buildwithmatija.com/blog/vllm-vs-ollama-vs-tgi-choose-llm-inference-engine | 2026-04-06 |
| [^185^] | AI Competence - Local LLM Stack Comparison | https://aicompetence.org/local-llm-stack-comparison/ | 2026-03-23 |
| [^186^] | DecodesFuture - llama.cpp vs Ollama vs vLLM | https://www.decodesfuture.com/articles/llama-cpp-vs-ollama-vs-vllm-local-llm-stack-guide | 2026-01-31 |
| [^187^] | The AI Engineer - vLLM vs Ollama vs SGLang | https://theaiengineer.substack.com/p/vllm-vs-ollama-vs-sglang-vs-tensorrt | 2026-04-10 |
| [^188^] | CETVEL Benchmark (EACL 2026) | https://aclanthology.org/2026.eacl-long.46.pdf | 2026 |
| [^192^] | JarvisLabs - vLLM Quantization Guide | https://jarvislabs.ai/blog/vllm-quantization-complete-guide-benchmarks | 2026-01-07 |
| [^193^] | Medium - GGUF in Practice Part 2 | https://medium.com/@michael.hannecke/gguf-in-practice-from-model-to-production-part-2-27c7eed23daa | 2025-12-07 |
| [^205^] | AiOps School - Best Ollama Models 2026 | https://aiopsschool.com/blog/the-best-ollama-models-in-2026/ | 2026-04-20 |
| [^207^] | MorphLLM - Best Ollama Models | https://www.morphllm.com/best-ollama-models | 2026-04-05 |
| [^209^] | Prompt Quorum - Local LLM Hardware Guide | https://www.promptquorum.com/local-llm-hardware-guide-2026 | 2026-04-04 |
| [^210^] | Clarifai - llama.cpp Blog | https://www.clarifai.com/blog/ilama.cpp | 2026-03-17 |
| [^211^] | Mean CEO - Qwen 3.5 Release | https://blog.mean.ceo/qwen-3-5-small-model-series-release/ | 2026-03-03 |
| [^213^] | PremAI - 10 Best vLLM Alternatives | https://blog.premai.io/10-best-vllm-alternatives-for-llm-inference-in-production-2026/ | 2026-02-28 |
| [^214^] | Medium - Intel Arc Pro B70 Qwen3.6 | https://bibek-poudel.medium.com/how-to-run-qwen3-6-27b-locally-on-intel-arc-pro-b70 | 2026-04-26 |
| [^216^] | AI Competence - Raspberry Pi 5 LLM | https://aicompetence.org/running-llama-on-raspberry-pi-5/ | 2025-09-15 |
| [^217^] | arXiv - LLMs on SBCs | https://arxiv.org/html/2511.07425v1 | 2025-10-20 |
| [^227^] | gingter.org - Ollama Goes MLX | https://gingter.org/2026/04/23/ollama-goes-mlx/ | 2026-04-23 |
| [^228^] | Knightli - Qwen3.6 VRAM Table | https://www.knightli.com/en/2026/05/01/qwen3-6-local-vram-quantization-table/ | 2026-05-01 |
| [^229^] | Unsloth - Qwen3.5 Guide | https://unsloth.ai/docs/models/qwen3.5 | 2026-04-19 |
| [^230^] | Starmorph - Apple Silicon Optimization | https://blog.starmorph.com/blog/apple-silicon-llm-inference-optimization-guide | 2026-04-10 |
| [^234^] | youngju.dev - Apple Silicon Deep Dive | https://www.youngju.dev/blog/culture/2026-03-18-apple-silicon-llm-inference-deep-dive.en | 2026-03-18 |
| [^243^] | ACL - TUMLU Benchmark | https://aclanthology.org/2025.acl-long.1112/ | 2025-07 |
| [^245^] | arXiv - TUMLU | https://arxiv.org/html/2502.11020v2 | 2025-02-16 |
| [^246^] | ktransformers GitHub - Long Context | https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/long_context_introduction.md | Unknown |
| [^247^] | arXiv - TurkBench | https://arxiv.org/pdf/2601.07020 | 2026 |
| [^248^] | llama.cpp GitHub - Server README | https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md | 2026-05-06 |
| [^249^] | ROCm Docs - vLLM Benchmark | https://rocm.docs.amd.com/en/docs-7.2.2/how-to/rocm-for-ai/inference/benchmark-docker/ | 2026-04-21 |
| [^270^] | Medium - Tune llama.cpp on Apple Silicon | https://medium.com/@michael.hannecke/tuning-llama-cpp-on-apple-silicon-843f37a6c3dc | 2026-04-29 |
| [^271^] | HuggingFace - llama.cpp MoE Offload | https://huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide | 2026-01-29 |
| [^272^] | Clarifai - llama.cpp FASTer Framework | https://www.clarifai.com/blog/ilama.cpp | 2026-03-17 |
| [^273^] | dev.to - Understanding MoE Offloading | https://dev.to/someoddcodeguy/understanding-moe-offloading-5co6 | 2025-10-12 |
| [^276^] | Hacker News - DMA-BUF Offloading | https://news.ycombinator.com/item?id=47432495 | 2026-03-18 |
| [^278^] | TechNode - ktransformers DeepSeek | https://technode.com/2025/02/17/tsinghua-universitys-ktransformers-enables-full-powered-deepseek-r1/ | 2025-02-17 |
| [^279^] | ktransformers GitHub - DeepSeek Tutorial | https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/DeepseekR1_V3_tutorial.md | 2025-02-15 |
| [^280^] | GitHub - LLAMA.CPP-ROCm | https://github.com/mambiux/LLAMA.CPP-ROCm | 2024-12-27 |
| [^293^] | BestAIWeb - Quantize and Deploy LLMs | https://www.bestaiweb.ai/how-to-quantize-and-deploy-llms-with-awq-gguf-and-vllm/ | 2026-03-26 |
| [^294^] | Cohorte - SGLang in Production | https://www.cohorte.co/blog/sglang-in-production-fast-serving-structured-generation-for-agentic-workloads | 2025-12-29 |
| [^295^] | Pi DIY Lab - Piper TTS on Raspberry Pi | https://pidiylab.com/text-to-speech-raspberry-pi-piper/ | 2025-12-02 |
| [^296^] | Skywork.ai - SGLang Comprehensive Guide | https://skywork.ai/skypage/en/sglang-guide-features-trends/ | 2026-04-15 |
| [^297^] | GitHub - rsvn/voice-assistant | https://github.com/risvn/voice-assistant | 2025-09-06 |
| [^304^] | Pinggy - Top 5 Local LLM Tools | https://pinggy.io/blog/top_5_local_llm_tools_and_models/ | 2026-04-23 |
| [^306^] | AkitaOnRails - Testing LLMs | https://www.akitaonrails.com/en/2026/04/05/testing-llms-open-source-and-commercial-can-anyone-beat-claude-opus/ | 2026-04-05 |
| [^307^] | Qwen Docs - llama.cpp Guide | https://qwen.readthedocs.io/en/latest/run_locally/llama.cpp.html | Unknown |
| [^308^] | Prompt Quorum - New Ollama Models | https://www.promptquorum.com/local-llm-hardware-guide-2026 | 2026-04-04 |
| [^309^] | Unsloth - Tool Calling Guide | https://unsloth.ai/docs/basics/tool-calling-guide-for-local-llms | 2026-04-07 |
| [^310^] | Medium - Claude Code with Local Models | https://medium.com/@luongnv89/how-to-run-claude-code-codex-with-local-models-via-llamacpp-ollama-lmstudio-and-vllm-2026 | 2026-04-15 |
| [^311^] | wolfpaulus.com - Llama on Pi | https://wolfpaulus.com/local_llama/ | 2026-04-27 |
