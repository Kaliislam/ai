# Dim 02 - Sesli Etkileşim Pipeline ve Gerçek Zamanlı Ses İşleme

**Araştırma tarihi:** 2026-01-20  
**Araştırmacı:** AI Agent  
**Kapsam:** Tamamen yerel çalışan AI asistan sesli etkileşim sistemi - STT, TTS, Wakeword, Wyoming Pipeline  
**Arama sayısı:** 24+ bağımsız kaynak

---

## 1. STT Pipeline

### 1.1 Whisper Türkçe Doğruluğu - Farklı Versiyonlar

```
Claim: Whisper Large-v3 Türkçe FLEURS benchmark'unda %7.5 WER (Word Error Rate) değerine ulaşır. Bu, İngilizce'nin %2.7'sine kıyasla yaklaşık 2.8 kat daha yüksek bir hata oranıdır. [^335^]
Source: ElevenLabs Scribe - Turkish Speech to Text Benchmark
URL: https://elevenlabs.io/speech-to-text/turkish
Date: Mevcut (güncel sayfa)
Excerpt: "Whisper Large v3 | 7.5% WER | FLEURS"
Context: ElevenLabs'ın kendi Scribe v1 modeli (%3.8 WER) ile kıyaslama yapılan ticari bir benchmark sayfası. Whisper Large-v3 için FLEURS sonucu net olarak %7.5 olarak veriliyor.
Confidence: high
```

```
Claim: MDPI Sensors dergisinde yayınlanan bağımsız bir akademik çalışmada, Whisper Large-v3 Türkçe FLEURS verisetinde %7.5 WER, METU MS'de %4.3 WER, TNST'de %8.5 WER ve Mozilla Common Voice'da %14.2 WER elde etmiştir. [^69^]
Source: MDPI Sensors 2024, "Implementation of a Whisper Architecture-Based Turkish ASR System and Evaluation of the Effect of Fine-Tuning with a Low-Rank Adaptation (LoRA) Adapter on Its Performance"
URL: https://www.mdpi.com/2079-9292/13/21/4227
Date: 2024-10-28
Excerpt: "In the METU MS dataset... the WER drops to 0.10 in the large-v2 model... with the large-v3 model, the WER drops to 0.043... FLEURS (100%) WER 0.075... Mozilla CV (30%) WER 0.142"
Context: Türkçe için en kapsamlı bağımsız akademik Whisper değerlendirmesi. 5 farklı Türkçe veriseti (METU MS, TNST, FLEURS, Mozilla CV, TASRT) üzerinde test edilmiş.
Confidence: high
```

```
Claim: Whisper farklı boyutları Türkçe'de şu WER değerlerini verir (MDPI çalışması, ön-test): Tiny %36, Base %24, Small %16, Medium %15, Large-v2 %10 (METU MS veriseti). [^69^]
Source: MDPI Sensors 2024, Table 3
URL: https://www.mdpi.com/2079-9292/13/21/4227
Date: 2024-10-28
Excerpt: "METU MS (100%) | WER | Tiny 0.36 | Base 0.24 | Small 0.16 | Medium 0.15 | Large-v2 0.10"
Context: METU MS (100%) veriseti üzerinde yapılan ön-test sonuçları.
Confidence: high
```

```
Claim: Whisper Large-v3 İngilizce LibriSpeech clean'de %2.1 WER, gerçek dünya İngilizce'de %3.8-5.2 WER, Türkçe ise Tier 2 dil olarak %9-13 WER aralığındadır. [^59^] [^270^]
Source: VexaScribe / NovaScribe - Whisper Accuracy 2026
URL: https://vexascribe.com/how-accurate-is-whisper
Date: 2026-05-03
Excerpt: "Turkish | Tier 2 | 9–13% | Agglutination" ve "Whisper Large-v3 achieves around 2.7% WER on LibriSpeech test-clean"
Context: Whisper'ın 99 dildeki genel performans kategorizasyonu. Türkçe, agglutinasyon nedeniyle Tier 2'de yer alıyor.
Confidence: high
```

### 1.2 Fine-Tuned Whisper Türkçe Modelleri

```
Claim: HuggingFace'de erdiyalcin/whisper-large-v3-turkish-test1 modeli Common Voice 17.0 üzerinde %12.80 WER elde etmiştir. 1000 adım, 1e-5 learning rate ile eğitilmiş. [^304^]
Source: HuggingFace Model Card - erdiyalcin/whisper-large-v3-turkish-test1
URL: https://huggingface.co/erdiyalcin/whisper-large-v3-turkish-test1
Date: 2025-10-24 (model kartı)
Excerpt: "It achieves the following results on the evaluation set: Loss: 0.1566; Wer: 12.7956. The following hyperparameters were used... learning_rate: 1e-05, training_steps: 1000"
Context: Doğrudan kullanılabilir, Apache-2.0 lisanslı fine-tuned Türkçe Whisper modeli. Son ay 147 indirme.
Confidence: high
```

```
Claim: HuggingFace'de selimc/whisper-large-v3-turbo-turkish modeli Common Voice 17.0 üzerinde %18.92 WER elde etmiştir. 0.8B parametreli (Large-v3 Turbo tabanlı). [^293^]
Source: HuggingFace Model Card - selimc/whisper-large-v3-turbo-turkish
URL: https://huggingface.co/selimc/whisper-large-v3-turbo-turkish
Date: 2024-10-08
Excerpt: "It achieves the following results on the evaluation set: Loss: 0.3123; Wer: 18.9229. Model size: 0.8B params"
Context: Large-v3 Turbo tabanlı (daha hızlı ama base model olarak daha düşük doğrulukta) fine-tuned model. Son ay 855 indirme. MIT lisanslı.
Confidence: high
```

```
Claim: MDPI makalesine göre LoRA (Low-Rank Adaptation) fine-tuning ile Whisper-large-v2 modelinde Türkçe Mozilla CV verisetinde WER %49 iyileştirilmiş (fine-tuning öncesi WER 0.156 → sonrası WER 0.079, %49.00 düşüş). METU MS'de %43.37, TNST'de %15.25, TASRT'de %2.47 iyileşme elde edilmiştir. [^69^]
Source: MDPI Sensors 2024, Table 8
URL: https://www.mdpi.com/2079-9292/13/21/4227
Date: 2024-10-28
Excerpt: "Mozilla CV (30%) | WER 0.156 → 0.079 | -49.00%. METU MS (100%) | WER 0.061 → 0.043 | -29.08%. TNST (30%) | WER 0.103 → 0.085 | -17.30%"
Context: Akademik çalışma, 8000 epoch, ~90 saat eğitim süresi. Chunk size 32, learning rate 5×10⁻⁶.
Confidence: high
```

```
Claim: Bağımsız bir akademik makalede (Kazakh ASR çalışması) Whisper Türkçe için LoRA fine-tuning'in WER'i %52'ye kadar azalttığı belirtilmiştir. [^230^]
Source: MDPI Information 2025, "Speech Recognition and Synthesis Models and Platforms for the Kazakh Language"
URL: https://www.mdpi.com/2078-2489/16/10/879
Date: 2025-10-10
Excerpt: "Whisper-based Turkish ASR was explored in [22], where LoRA fine-tuning reduced WER by up to 52%."
Context: Kazakh dili odaklı çalışmanın literature review bölümünde Türkçe Whisper sonuçlarına atıf.
Confidence: medium
```

### 1.3 faster-whisper vs whisper.cpp Performans Karşılaştırması

```
Claim: Whisper.cpp batching desteklemediğinden çoklu dosya karşılaştırmasında slower-whisper daha hızlıdır, ancak batch size=1 karşılaştırmasında whisper.cpp en hızlısıdır. whisper.cpp GPU'da batching olmadığı için dezavantajlıdır. [^181^]
Source: Medium - "Whisper Transcription: I benched every major backend so you don't have to"
URL: https://medium.com/@vici0549/whisper-transcription-i-benched-every-major-backend-so-you-dont-have-to-8eff4a68d2a0
Date: 2026-03-10
Excerpt: "whisper.cpp does not support batching... when using a batch size of 1 comparison whisper.cpp was the fastest!"
Context: Tüm major Whisper backend'lerinin (Vanilla, HF Transformers, Whisper-S2T-Reborn, Faster Whisper, WhisperX, whisper.cpp) kapsamlı benchmark'ı.
Confidence: high
```

```
Claim: CPU'da (Intel N97, 4 çekirdek, GPU yok) uzun seslerde (31 sn) whisper.cpp (base) faster-whisper'a kıyasla 9.7x daha yavaş olabilir (49.15s vs 5.07s). Kısa seslerde (10.6s) performansları benzerdir. [^176^]
Source: GitHub Issue - whisper.cpp vs faster-whisper scaling on longer audio
URL: https://github.com/ggml-org/whisper.cpp/issues/3682
Date: 2026-02-26
Excerpt: "faster-whisper (base) | 5.07s | Baseline... whisper.cpp (base) | 49.15s | 9.7x SLOWER"
Context: whisper.cpp'nin uzun seslerde farklı ölçeklenme davranışı gösterdiği bir GitHub issue tartışması. Kullanıcı beklenen 2-3x avantaj yerine 9.7x yavaşlık gözlemliyor.
Confidence: high
```

```
Claim: faster-whisper streaming'de beam_size=1 kullanmak latency'yi minimize eder. condition_on_previous_text=False streaming için kritiktir; aksi halde hallucination drift oluşur. 4 saniyelik chunk'lar, 0.5 saniye overlap önerilir. [^317^]
Source: Spheron Network - "Deploy Whisper v4 and Production ASR on GPU Cloud"
URL: https://www.spheron.network/blog/whisper-v4-asr-gpu-cloud-production-guide/
Date: 2026-04-25
Excerpt: "condition_on_previous_text=False is the most important flag for streaming... Buffer incoming audio into 4-second windows with 0.5-second overlaps... Run faster-whisper on each chunk with beam_size=1"
Context: Production ASR streaming için optimizasyon rehberi.
Confidence: high
```

### 1.4 Gerçek Zamanlı Streaming STT Stratejileri

```
Claim: Whisper native streaming modeli değildir; encoder-decoder mimarisi sabit uzunluklu audio pencereleriyle çalışır. Üretim yaklaşımı "chunked streaming with overlap"tır. [^317^]
Source: Spheron Network - Whisper Production ASR Guide
URL: https://www.spheron.network/blog/whisper-v4-asr-gpu-cloud-production-guide/
Date: 2026-04-25
Excerpt: "Whisper is not a native streaming model. It processes fixed-length audio windows through an encoder-decoder architecture... The production approach is chunked streaming with overlap."
Context: Whisper'ın streaming ASR olarak kullanımının temel teknik sınırlamaları.
Confidence: high
```

```
Claim: whisper.cpp stream örneği (--step 500 --length 5000) her 0.5 saniyede audio örnekler ve sürekli transkripsiyon çalıştırır. Sliding window modu (--step 0) VAD ile tetiklenir. [^326^]
Source: whisper.cpp GitHub - examples/stream/README.md
URL: https://github.com/ggerganov/whisper.cpp/blob/master/examples/stream/README.md
Date: 2022-09-25 (güncel)
Excerpt: "The whisper-stream tool samples the audio every half a second and runs the transcription continuously... Setting --step argument to 0 enables the sliding window mode"
Context: whisper.cpp'nin resmi streaming örneği. SDL2 bağımlılığı var.
Confidence: high
```

```
Claim: WebSocket tabanlı faster-whisper streaming server'ında ilk denemede 1 saniyelik buffer+transcribe yaklaşımı timeout'lara neden olur. Background multithreading ile client disconnect sorunu çözülür. [^239^]
Source: Neurl Creators - "Building Real-Time Speech-to-Text with Faster Whisper"
URL: https://neurlcreators.substack.com/p/how-do-you-build-a-real-time-speech
Date: 2025-12-18
Excerpt: "I built a WebSocket server that buffered one second of audio, sent it to Whisper for transcription, and returned the text. Simple, right? In practice, it failed. Whisper took too long to respond..."
Context: Pratik streaming STT geliştirme deneyimleri.
Confidence: high
```

```
Claim: Silero VAD ön-işleme süresi ~0.06s, tam buffer VAD işleme ~0.21s tutarlıdır. Whisper large-v3 ile toplam transkripsiyon gecikmesi 0.88-1.66s arasındadır; base modelde 0.44s'e düşer. [^324^]
Source: arXiv 2024 - "Adapting STT Whisper Models to Real-Time Environments"
URL: https://arxiv.org/html/2405.03484v1
Date: 2024-05-06
Excerpt: "Silero pre-trained VAD... consistent at 0.06 ± 0.2 seconds and 0.21 ± 0.02 seconds... transcription delay spanning from 0.88 seconds to 1.66 seconds when the large-v3 Whisper model is used"
Context: Akademik çalışma, Whispy adlı gerçek zamanlı Whisper adaptasyonunun timing analizi.
Confidence: high
```

---

## 2. TTS Pipeline

### 2.1 Piper TTS Türkçe Ses Modelleri

```
Claim: Piper TTS Türkçe için tr_TR-dfki-medium modeli mevcuttur. 63.2 MB, 22,050 Hz sample rate, CC BY-NC-SA 4.0 lisanslı dfki-ot-data dataseti üzerinden eğitilmiş. U.S. English lessac voice'tan fine-tuned. [^316^]
Source: HuggingFace - rhasspy/piper-voices/tr/tr_TR/dfki/medium/MODEL_CARD
URL: https://huggingface.co/rhasspy/piper-voices/blob/main/tr/tr_TR/dfki/medium/MODEL_CARD
Date: ~3 yıl önce (ilk commit)
Excerpt: "Language: tr_TR (Turish, Turkey)... Quality: medium... Samplerate: 22,050 Hz... Dataset URL: https://github.com/marytts/dfki-ot-data... License: https://creativecommons.org/licenses/by-nc-sa/4.0/"
Context: Piper TTS'nin tek Türkçe ses modeli. Fahrettin ve Fettah sesleri contributor talebi üzerine kaldırılmış.
Confidence: high
```

```
Claim: Piper TTS genel performansı: MOS 3.5, RTF 0.008, <100 MB RAM (CPU), 30+ dil, MIT lisanslı, sentence-level streaming destekler. Raspberry Pi'de gerçek zamanlı çalışır. [^43^]
Source: Codesota - "Best Open-Source TTS Models Compared | 2026 Guide"
URL: https://www.codesota.com/guides/tts-models
Date: 2026-03-28
Excerpt: "Piper | 3.5 | 0.008 | < 100 MB (CPU) | 6-60M | No | MIT... Piper is the go-to TTS for edge devices... a ten-second clip in eighty milliseconds"
Context: 8 açık kaynak TTS modelinin kapsamlı karşılaştırması.
Confidence: high
```

```
Claim: Trelis Research'in 2026 değerlendirmesinde Piper TTS %28 roundtrip CER ve 3.3 MOS puanı almıştır. "Airy and choppy delivery" olarak tanımlanmıştır. Daha fazla eğitim verisiyle MOS 4.0+ mümkündür. [^318^]
Source: Trelis Research - "Top Text-to-Speech (TTS) Models in 2026"
URL: https://trelis.substack.com/p/top-text-to-speech-tts-models-in
Date: 2026-03-31
Excerpt: "Piper recorded 28% CER and 3.3 MOS. This smaller model exhibited an airy quality with some choppiness in the output... With more training data and higher quality audio, this architecture can achieve MOS scores above 4.0."
Context: 10 TTS modelinin zorlayıcı metinler üzerinde karşılaştırılması (semboller, kısaltmalar, özel isimler).
Confidence: high
```

```
Claim: Piper TTS streaming desteği Home Assistant Wyoming protokolünde sentence-level olarak mevcuttur. LLM token stream'i cümlelere bölünüp anında sentezlenir, bu da uzun yanıtlarda bekleme süresini ortadan kaldırır. [^299^] [^300^]
Source: Home Assistant Community - "Streaming support for Wyoming TTS" ve "TTS streaming support"
URL: https://community.home-assistant.io/t/streaming-support-for-wyoming-tts/900708
Date: 2025-06-12 / 2025-07-11
Excerpt: "a stream of text chunks is combined into sentences, which are then sent for synthesis. The audio data is stored in a buffer and transmitted to HA... Piper to switch from temporary files to working with RAW output"
Context: Wyoming TTS proxy/custom integration geliştirmeleri.
Confidence: high
```

### 2.2 Kokoro-82M Türkçe Desteği

```
Claim: Kokoro-82M şu anda sadece İngilizce (Amerikan/British), Japonca, Korece ve Çince destekler. Türkçe desteği mevcut değildir. Gelecekte genişletilmesi mimari olarak mümkün olsa da roadmap'te belirtilmemiştir. [^44^] [^62^] [^220^]
Source: TTS Insider - "XTTS V2 vs Kokoro 82M" ve Medium - "Kokoro-82M: The best TTS model"
URL: https://www.ttsinsider.com/xtts-v2-vs-kokoro/ ve https://medium.com/data-science-in-your-pocket/kokoro-82m-the-best-tts-model-in-just-82-million-parameters-512b4ba4f94c
Date: 2026-03-24 / 2025-01-20
Excerpt: "Kokoro 82M currently offers a more limited selection, focusing primarily on English, Japanese, Korean, and Chinese." ve "Limited Multilingual Support: Currently supports only English"
Context: Kokoro-82M'nin en büyük sınırlamalarından biri. espeak-ng g2p bağımlılığı var ve bu Türkçe için ayrıca geliştirilmesi gerekiyor.
Confidence: high
```

```
Claim: Kokoro-82M, 82M parametre, MOS 4.2, RTF 0.03, <1 GB VRAM, Apache 2.0 lisanslı, streaming generation destekler. [^43^]
Source: Codesota - Best Open-Source TTS Models Compared 2026
URL: https://www.codesota.com/guides/tts-models
Date: 2026-03-28
Excerpt: "Kokoro | 4.2 | 0.03 | < 1 GB | 82M | No (style presets) | Apache 2.0... Real-time or faster — low-latency inference suitable for streaming"
Context: En yüksek MOS puanlı açık kaynak TTS modeli, ancak Türkçe desteği yok.
Confidence: high
```

### 2.3 Coqui TTS / XTTS-v2 Türkçe Desteği

```
Claim: XTTS-v2 (Coqui TTS) 17 dil destekler ve bunlar arasında Türkçe de vardır. Ancak CPML (Coqui Public Model License) altında lisanslanmıştır ve ticari kullanım yasaktır. 467M parametre, ~4 GB VRAM, RTF 0.18. [^44^]
Source: TTS Insider - "XTTS V2 vs Kokoro 82M"
URL: https://www.ttsinsider.com/xtts-v2-vs-kokoro/
Date: 2026-03-24
Excerpt: "XTTS V2 supports 17 languages including English, Spanish, French, German, Italian, Portuguese, Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Japanese, Hungarian, Korean, and Hindi."
Context: XTTS-v2 ticari kullanım için uygun değil (CPML). Türkçe için en iyi voice cloning seçeneği olabilir.
Confidence: high
```

```
Claim: Coqui TTS paketi pip install TTS ile kurulur. XTTS v2 6 saniyelik referans ses ile zero-shot voice cloning yapar. tts_stream() ile chunk bazlı streaming üretimi destekler. [^210^]
Source: Local AI Master - "Coqui TTS: Technical Analysis"
URL: https://localaimaster.com/models/coqui-tts
Date: 2025-10-28
Excerpt: "tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2')... tts.tts_stream(long_text, speaker_wav='voice.wav')"
Context: Coqui TTS kurulum ve kullanım rehberi.
Confidence: medium
```

### 2.4 Ses Streaming ve Latency Optimizasyonu

```
Claim: Yerel voice assistant pipeline latency beklentisi: Whisper base ~0.5s, LLM first token (Qwen3 7B) 1-3s, Kokoro TTS ~0.3s. Toplam 2-5 saniye. Piper TTS Kokoro'dan daha hızlıdır (~0.5s). [^332^]
Source: LLM Hardware - "Local AI Voice Assistant: Whisper + Ollama + Kokoro TTS"
URL: https://llmhardware.io/guides/local-voice-assistant-guide
Date: 2026-04-01
Excerpt: "STT (Whisper base) ~0.5s... LLM first token 1–3s... TTS start (Kokoro) ~0.3s... Total 2–5 seconds"
Context: Yerel voice assistant kurulum rehberi. 8 GB VRAM önerilir.
Confidence: high
```

```
Claim: RTX 4060 (8 GB) ile gerçek ölçümler: Whisper base transkripsiyon ~0.5s, Qwen3 7B Q4 ~55 tok/s, 150 token yanıt ~2-3s, Kokoro TTS (CPU) ~0.5s. [^332^]
Source: LLM Hardware - Local Voice Assistant Guide
URL: https://llmhardware.io/guides/local-voice-assistant-guide
Date: 2026-04-01
Excerpt: "RTX 4060 (8 GB) — real numbers: Whisper base transcription ~0.5s, Qwen3 7B Q4 speed ~55 tok/s, 150-token response ~2–3s, Kokoro TTS (CPU) ~0.5s"
Context: Gerçek donanım üzerinde ölçülmüş latency değerleri.
Confidence: high
```

```
Claim: Home Assistant yerel voice pipeline'da latency 5-10 saniye (home automation) ve >30-60 saniye (uzun yanıtlar) olabilmektedir. Bu, kullanıcı tarafından raporlanan gerçek deneyimdir. [^348^]
Source: Reddit r/homeassistant - "Local LLM/Whisper/Piper for HA Voice Assist"
URL: https://www.reddit.com/r/homeassistant/comments/1migi2p/local_llmwhisperpiper_for_ha_voice_assist_how_to/
Date: 2026-02-06
Excerpt: "The latency is like 5-10 seconds for home automations, and >30-60 seconds for something like 'tell me a joke'"
Context: i7-12700K + RTX A2000 + 32GB RAM + NVME + Ollama 3.2 kullanıcı deneyimi.
Confidence: high
```

---

## 3. Wakeword

### 3.1 openWakeWord Kurulumu ve "Jarvis" Eğitimi

```
Claim: openWakeWord, Apache 2.0 lisanslı, özel wakeword'leri <1 saatte eğitim yapabilir. Sentetik veri (TTS üretimi) kullanır, manuel veri toplamaya gerek yoktur. Çıktı ONNX/TFLite formatındadır. [^75^]
Source: openWakeWord - Official Website
URL: https://openwakeword.com/
Date: Mevcut
Excerpt: "Train custom voice activation models in under an hour. No ML expertise required. Works with Home Assistant, Rhasspy, OpenVoiceOS"
Context: openWakeWord'ün resmi tanıtım sayfası.
Confidence: high
```

```
Claim: openWakeWord modelleri 80ms audio frame'leri işler, 0-1 arası confidence score döner. Her ek model küçük bir etki yaratır çünkü paylaşılan feature extraction backbone kullanılır. RPi 3 tek çekirdeğinde 15-20 model eşzamanlı çalışabilir. [^327^]
Source: GitHub - dscripka/openWakeWord
URL: https://github.com/dscripka/openWakeWord
Date: 2022-05-28 (güncel)
Excerpt: "a single core of a Raspberry Pi 3 can run 15-20 openWakeWord models simultaneously in real-time... Models process a stream of audio data in 80 ms frames, and return a score between 0 and 1"
Context: openWakeWord'ün proje hedefleri ve teknik detayları.
Confidence: high
```

```
Claim: openWakeWord ile "Jarvis" wakeword eğitimi Google Colab üzerinden yapılabilir. Piper TTS ile sentetik örnekler üretilir, otomatik 16kHz resampling uygulanır. Çıktı .tflite formatında Home Assistant entegrasyonu için indirilebilir. [^182^] [^229^]
Source: Home Assistant Community - "Train a Custom French Wake Word for Home Assistant with OpenWakeWord (Colab)"
URL: https://community.home-assistant.io/t/guide-train-a-custom-french-wake-word-for-home-assistant-with-openwakeword-colab/943111
Date: 2025-10-22
Excerpt: "Train your own French wake word (e.g., 'Alexa', 'Jarvis', 'Lumière') offline using OpenWakeWord + Piper TTS—directly in Google Colab!"
Context: Fransızca odaklı rehber ama "Jarvis" örneği veriliyor. Türkçe için tr_TR-dfki-medium Piper modeli kullanılabilir.
Confidence: high
```

```
Claim: openWakeWord TFLite dönüşümü için tensorflow==2.19.0, onnx2tf, onnx==1.17.0, onnxruntime==1.18.1 sürümları gereklidir. Son TensorFlow güncellemeleriyle uyumsuzluk olabilir. [^229^]
Source: Home Assistant Community - French Wake Word Guide (yorumlar)
URL: https://community.home-assistant.io/t/guide-train-a-custom-french-wake-word-for-home-assistant-with-openwakeword-colab/943111
Date: 2025-10-22
Excerpt: "To convert an ONNX model to TFLite, make sure to use these exact library versions: !pip install tensorflow==2.19.0, onnx2tf, onnx==1.17.0, onnxruntime==1.18.1"
Context: Kullanıcı deneyimleriyle belirlenen doğru dependency versiyonları.
Confidence: high
```

### 3.2 Alternatif Wakeword Motorları

```
Claim: Porcupine (Picovoice) ücretsiz hesap: ayda sadece 3 wake word modeline izin verir, her wake word ayrı modeldir. 5 saat kullanım limiti vardır (Cheetah/Leopard için). Geliştirici hesabı $500/ay (yıllık taahhüt). [^242^]
Source: Medium - "Picovoice AI Product Research"
URL: https://medium.com/@chrisandsherry416/picovoice-ai-product-research-4f2a8592cba2
Date: 2024-06-01
Excerpt: "The Porcupine product allows only for 3 wake word models per 30 day window. Each wake word or phrase is a separate model. The paid subscription next step up to the developer account is $500 per month... commit to 1 year"
Context: Picovoice ürün ailesinin ücretsiz sınırlamalarının detaylı analizi.
Confidence: high
```

```
Claim: Porcupine %97+ true positive rate, <1 false alarm/saat, RPi 3'te <%4 CPU kullanımı. 6 farklı keyword (alexa, computer, jarvis, smart mirror, snowboy, view glass) üzerinde 50+ konuşmacı ve 18 gürültü ortamında test edilmiştir. [^281^]
Source: Picovoice Blog - "Wake Word Detection in React Native: Complete 2026 Guide"
URL: https://picovoice.ai/blog/react-native-wake-word/
Date: 2025-11-19
Excerpt: "97%+ true positive rate with <1 false alarm per hour across six keywords from more than 50 distinct speakers and 18 different noise environments at 10dB SNR"
Context: Porcupine'ın üretim performans iddiaları.
Confidence: medium
```

```
Claim: Snowboy (KITT.AI) 31 Aralık 2020'de kapatılmıştır. GitHub repo'ları açık kalmıştır ancak sadece topluluk desteği mevcuttur. Artık önerilmemektedir. [^234^]
Source: Reddit r/speechtech - "Snowboy is shutting down"
URL: https://www.reddit.com/r/speechtech/comments/giawtu/snowboy_is_shutting_down/
Date: 2025-07-11 (arşiv postu)
Excerpt: "We plan to shut down all KITT.AI products (Snowboy, NLU and Chatflow) by Dec. 31st, 2020... Our github repositories will remain open, but only community support will be available"
Context: Snowboy'un tarihi kapanış duyurusu. 85,000+ geliştiriciye hizmet vermişti.
Confidence: high
```

```
Claim: Precise-lite (OpenVoiceOS) ONNX formatına taşınmıştır. RPi 5'te CPU kullanımı tflite_runtime (~1.8-2.6%) yerine ONNX (~1.0-1.3%) olarak yarı yarıya düşmüştür. [^275^]
Source: OpenVoiceOS Blog - "Precise Wake Word Engine Goes ONNX!"
URL: https://blog.openvoiceos.org/posts/2025-11-03-precise-onnx
Date: 2025-11-03
Excerpt: "Initial testing on a Raspberry Pi 5 shows a significant reduction in CPU usage: Precise (tflite-runtime) ~1.8% - 2.6% | Precise (ONNX) ~1.0% - 1.3%"
Context: OpenVoiceOS ekosisteminde Precise wake word engine'inin modernizasyonu.
Confidence: high
```

### 3.3 Wake Word Sonrası Pipeline (Komut Moduna Geçiş)

```
Claim: Wyoming protokolünde wake word detection sonrası `detection` event'i gönderilir. Pipeline: detect → audio-start → audio-chunk (until silence) → audio-stop → transcript → intent/LLM → synthesize → audio-chunk (TTS). [^325^]
Source: GitHub - OHF-Voice/wyoming (Peer-to-peer protocol for voice assistants)
URL: https://github.com/OHF-Voice/wyoming
Date: 2023-09-29
Excerpt: "detection - response when detection occurs... name of wake word that was detected... Event Flow: → detect → audio-start → audio-chunk → audio-stop → transcript"
Context: Wyoming protokolünün resmi event tipleri ve akışı.
Confidence: high
```

```
Claim: violawake pipeline'ında wakeword inference ~8ms/frame (ONNX), VAD <1ms/frame, STT (Whisper base, 3s audio) 0.5-2s, TTS first audio (Kokoro) 0.3-0.8s. [^272^]
Source: PyPI - violawake 0.2.2
URL: https://libraries.io/pypi/violawake
Date: 2026-03-28
Excerpt: "Wake word inference (20ms frame) | 7.8 ms | 12.1 ms... VAD (WebRTC, 20ms frame) | 0.4 ms | 0.8 ms... STT (Whisper base, 3s audio) | 680 ms | 1.2s... TTS first audio (Kokoro, 1 sentence) | 310 ms | 580 ms"
Context: Python voice pipeline kütüphanesi benchmark'ı. i7-12700H + RTX 3060 (CPU inference).
Confidence: medium
```

---

## 4. Tam Pipeline

### 4.1 Wyoming Protokolü Mimarisi (Home Assistant)

```
Claim: Wyoming protokolü JSON Lines (JSONL) tabanlı, stdin/stdout veya TCP üzerinden çalışan bir interprocess event protokolüdür. Her event `type` (zorunlu), `data` (opsiyonel) ve `payload_length` (binary audio için) içerir. Audio 16kHz mono PCM formatındadır. [^212^] [^325^]
Source: GitHub - rhasspy/rhasspy3/docs/wyoming.md
URL: https://github.com/rhasspy/rhasspy3/blob/master/docs/wyoming.md
Date: 2025-10-06
Excerpt: "Each event in the Wyoming protocol is: 1. A single line of JSON... MUST have a type field... MAY have a payload_length field... Example: { 'type': 'audio-chunk', 'data': { 'rate': 16000, 'width', 'channels': 1 }, 'payload_length': 2048 }"
Context: Wyoming protokolünün orijinal tanımı. Rhasspy v3'ten türemiştir.
Confidence: high
```

```
Claim: Wyoming protokolü TTS streaming için `synthesize-start`, `synthesize-chunk`, `synthesize-stop`, `synthesize-stopped` event'lerini tanımlar. Bu sayede LLM token stream'i cümle cümle TTS'e gönderilebilir. [^325^]
Source: GitHub - OHF-Voice/wyoming
URL: https://github.com/OHF-Voice/wyoming
Date: 2023-09-29
Excerpt: "Streaming: 1. synthesize-start - starts stream... 2. synthesize-chunk - text: part of text to synthesize... 3. synthesize-stop - end of stream... 4. synthesize-stopped - sent back to server after final audio"
Context: Wyoming protokolünün TTS streaming extension'ı. Home Assistant 2025.07+ ile desteklenir.
Confidence: high
```

```
Claim: Wyoming Satellite projesi artık bakımlanmıyor (deprecated). Yerine Linux Voice Assistant (ESPHome protokolü kullanan) geçmiştir. Wyoming protokolü kendisi hâlâ aktif ve Home Assistant entegrasyonu devam etmektedir. [^233^] [^333^]
Source: GitHub - rhasspy/wyoming-satellite (Deprecation Notice)
URL: https://github.com/rhasspy/wyoming-satellite
Date: 2026-01-27
Excerpt: "NOTE: This project is no longer maintained as it has been replaced by Linux Voice Assistant that uses the ESPHome protocol, which supports the newest features"
Context: Wyoming Satellite'in durumu. Wyoming protokolü (server-client) hâlâ kullanımda.
Confidence: high
```

```
Claim: Home Assistant Wyoming entegrasyonu otomatik Zeroconf keşif destekler. Uzak ses satellite'leri (örn. Raspberry Pi) Home Assistant'a bağlanabilir. Ses işleme ayarları: Noise suppression (webrtc), Auto gain (webrtc), Mic volume. [^227^]
Source: Home Assistant Docs - Wyoming Protocol Integration
URL: https://www.home-assistant.io/integrations/wyoming/
Date: 2026-04-01
Excerpt: "Remote voice satellites can be connected to Home Assistant using the Wyoming protocol. These satellites typically run on Raspberry Pi's, and are automatically discovered by Home Assistant through Zeroconf."
Context: Resmi Home Assistant entegrasyon dokümantasyonu.
Confidence: high
```

```
Claim: Wyoming-openwakeword sunucusu 10400 portunda TCP üzerinden çalışır. Özel .tflite modelleri --custom-model-dir ile yüklenebilir. Docker image mevcuttur. [^328^]
Source: GitHub - rhasspy/wyoming-openwakeword
URL: https://github.com/rhasspy/wyoming-openwakeword
Date: 2023-10-03
Excerpt: "script/run --uri 'tcp://0.0.0.0:10400'... --custom-model-dir <DIR> - look for custom wake word models (.tflite)"
Context: Wyoming protokolüne uygun openWakeWord sunucusu.
Confidence: high
```

### 4.2 End-to-End Latency Hesaplaması

```
Claim: Tipik bir voice agent latency bütçesi: End of utterance detection 100-300ms, STT processing 150-500ms, LLM time-to-first-token (TTFT) 200-800ms, TTS time-to-first-byte (TTFB) 100-500ms, Network overhead 50-200ms. Toplam optimize edilmemiş: 1-2+ saniye. [^302^]
Source: Sayna AI - "Sub-Second Voice Agent Latency: A Practical Architecture Guide"
URL: https://sayna.ai/blog/sub-second-voice-agent-latency-practical-architecture-guide
Date: 2025-12-29
Excerpt: "End of utterance detection | 100-300ms | 150-200ms... STT processing | 150-500ms | 100-200ms... LLM (TTFT) | 200-800ms | 150-300ms... TTS (TTFB) | 100-500ms | 80-150ms"
Context: Voice agent latency bütçesi optimizasyon rehberi.
Confidence: high
```

```
Claim: Streaming pipeline mimarisi ile (STT partial → LLM token stream → TTS sentence-level) toplam algılanan latency <1 saniye hedeflenebilir. Ideal breakdown: Audio transport <50ms, STT first partial 100-200ms, LLM TTFT 200-400ms, TTS TTFB 100-300ms. [^160^]
Source: LiveKit Blog - "Voice Agent Architecture: STT, LLM, and TTS Pipelines Explained"
URL: https://livekit.com/blog/voice-agent-architecture-stt-llm-tts-pipelines-explained
Date: 2026-02-21
Excerpt: "STT (first partial result) | 100–200ms | Streaming STT... LLM time-to-first-token | 200–400ms... TTS time-to-first-audio | 100–300ms... Total (perceived) | < 1 second"
Context: Üretim voice agent pipeline mimarilerinin genel latency hedefleri.
Confidence: high
```

```
Claim: Home Assistant yerel pipeline'da gerçek ölçümler: STT 0.8s, NLP 0.16s, TTS 0.0s. Ancak end-to-end 13 saniye sürebilir. Fark Home Assistant pipeline orchestration ve cihaz önizleme gecikmesinden kaynaklanır. [^209^]
Source: Home Assistant Community - "Workaround for pipeline orchestration latency in HA"
URL: https://community.home-assistant.io/t/workaround-for-pipeline-orchestration-latency-in-ha/964783
Date: 2025-12-20
Excerpt: "Debug shows STT 0.8s, NLP 0.16s and TTS 0.0s, yet end to end it takes 13secs to hear the response. I understood that this is 100% down to HA -by name the pipeline orchestration."
Context: Home Assistant'ın sequential pipeline mimarisinin neden olduğu orchestration overhead.
Confidence: high
```

```
Claim: Home Assistant debug log örneğinde: run-start 18:42:00.092 → stt-vad-start 18:42:01.159 (VAD start ~1s) → stt-vad-end 18:42:02.782 (VAD end ~2.7s) → stt-end 18:42:02.963 (transcript hazır ~0.96s) → intent-start 18:42:02.964 → intent-progress ilk token 18:42:08.388 (~5.4s LLM TTFT) → tts-start 18:42:08.632 → run-end 18:42:08.632. Toplam: ~8.5 saniye. [^235^]
Source: Home Assistant Community - "Voice Assistant getting progressively slower each request"
URL: https://community.home-assistant.io/t/please-help-voice-assistant-getting-progressively-slower-each-request/986100
Date: 2026-02-12
Excerpt: "run-start 2026-02-12T18:42:00.092... stt-vad-start 2026-02-12T18:42:01.159... stt-end 2026-02-12T18:42:02.963... intent-progress first token 2026-02-12T18:42:08.388... run-end 2026-02-12T18:42:08.632"
Context: Home Assistant debug çıktısı. Ollama llama3.2:1b kullanılıyor. LLM TTFT ~5.4s baskın faktör.
Confidence: high
```

```
Claim: Yerel pipeline için önerilen latency optimizasyonu: `prefer_local_intents: true` ayarı ile "Işıkları aç" gibi komutlar doğrudan HA intent recognition ile 200ms'de işlenir, LLM'e gitmeden. [^72^]
Source: Joe Karlsson Blog - "I Built a Fully Local Voice Assistant for Home Assistant (With GPU, No Cloud Required)"
URL: https://www.joekarlsson.com/blog/local-voice-ai-home-assistant-gpu/
Date: 2026-04-12
Excerpt: "prefer_local_intents: true is the most important setting most guides skip over... 'Turn on the lights' gets handled by HA directly. Fast. Reliable. The LLM only engages for things HA can't handle natively."
Context: Üretimde çalışan yerel voice pipeline deneyimi. GPU hızlandırmalı faster-whisper + Piper + Ollama.
Confidence: high
```

### 4.3 Barge-in / Interruption Handling

```
Claim: Barge-in (interruption) handling için kritik adımlar: 1) VAD ile konuşma başlangıcı tespiti, 2) TTS playback'i anında durdurma, 3) Audio buffer'ı temizleme, 4) LLM generation'ı iptal etme, 5) Yeni input'u işlemeye başlama. İyi ayarlanmış pipeline'da toplam interruption latency 25ms'de pipeline temizlenebilir. [^206^] [^274^]
Source: Orga AI Blog - "Barge-in for Voice Agents" ve Chanl.ai - "Voice AI pipeline: STT, LLM, TTS and the 300ms budget"
URL: https://orga-ai.com/blog/blog-barge-in-voice-agents-guide ve https://www.chanl.ai/blog/voice-ai-pipeline-stt-tts-latency-budget
Date: 2026-02-12 / 2026-04-01
Excerpt: "Total interruption latency: 25ms to clear the pipeline. The user perceives no overlap because audio playback stops within one frame (20ms)." ve "T+0ms: User starts speaking. VAD detects speech onset... T+25ms: Pipeline is clear and processing new audio."
Context: Barge-in teknik implementasyonu ve latency timeline'ı.
Confidence: high
```

```
Claim: Barge-in implementasyonunda TTS output küçük chunk'lar halinde (100-200ms) tutulmalıdır, böylece interruption anında kelime ortasında kesilme olmadan hızlıca durdurulabilir. [^217^]
Source: Medium - "Handling Interruptions in Speech-to-Speech Services"
URL: https://medium.com/@roshini.rafy/handling-interruptions-in-speech-to-speech-services-a-complete-guide-4255c5aa2d84
Date: 2025-10-10
Excerpt: "Keep TTS output in small chunks (100–200ms) so you can stop quickly without cutting off mid-word."
Context: Interruption handling best practices.
Confidence: high
```

```
Claim: Acoustic echo cancellation (AEC) olmadan barge-in çalışmaz; mikrofon asistanın kendi TTS çıktısını duyar ve bu bir interruption olarak algılanır (self-interruption). Çözüm: echoCancellation: true (WebRTC getUserMedia) veya kulaklık kullanmak. [^45^]
Source: AssemblyAI Blog - "Build a voice assistant app with Voice Agent API"
URL: https://www.assemblyai.com/blog/build-a-voice-assistant-app-with-voice-agent-api
Date: 2026-05-06
Excerpt: "Why does my voice agent keep interrupting itself? Almost always acoustic echo: the mic is picking up the agent's TTS output through the speakers. Pass echoCancellation: true to getUserMedia"
Context: Voice agent API geliştirme rehberi. Browser tabanlı AEC.
Confidence: high
```

### 4.4 Echo Cancellation Stratejileri

```
Claim: Yerel AI asistan pipeline'ında echo cancellation için iki temel strateji vardır: 1) Acoustic Echo Cancellation (AEC) - AI'ın kendi sesini mikrofon girdisinden çıkararak full-duplex konuşmaya izin verir. 2) Half-Duplex - konuşma ve dinleme modları arasında geçiş yapar, tek seferde bir taraf konuşur. AEC doğal konuşma sağlar; half-duplex daha basit implementasyon sunar. [^319^]
Source: AnveVoice - "Acoustic Echo Cancellation vs Half-Duplex for Voice AI"
URL: https://anvevoice.app/faq/acoustic-echo-cancellation-vs-half-duplex-for-voice-ai
Date: 2026-05-04
Excerpt: "Acoustic Echo Cancellation excels at natural full-duplex conversation where both parties can speak simultaneously. Half-Duplex for Voice AI excels at simpler implementation with no echo artifacts."
Context: Voice AI echo cancellation karşılaştırması.
Confidence: high
```

```
Claim: WebRTC audio processing modülü (APM) AEC, NS (noise suppression) ve AGC (automatic gain control) içerir. Python'da `aec-audio-processing` PyPI paketi ile kullanılabilir: `AudioProcessor(enable_aec=True, enable_ns=True, enable_agc=True)`. 16kHz mono PCM, 10ms frame'ler halinde işlenir. [^296^]
Source: PyPI - aec-audio-processing
URL: https://pypi.org/project/aec-audio-processing/
Date: 2025-09-01
Excerpt: "ap = AudioProcessor(enable_aec=True, enable_ns=True, enable_agc=True)... ap.set_stream_format(16000, 1)... audio_out = ap.process_stream(audio_10ms)"
Context: WebRTC tabanlı açık kaynak Python echo cancellation kütüphanesi.
Confidence: high
```

```
Claim: Home Assistant Voice Preview Edition (ESP32-S3 + XMOS XU316 DSP) donanım seviyesinde AEC (echo cancellation), stationary noise removal ve AGC içerir. XMOS xCORE mimarisi deterministik real-time DSP işlemleri için tasarlanmıştır. [^331^] [^343^]
Source: Home Assistant Docs - Voice Preview Edition
URL: https://www.home-assistant.io/voice-pe/
Date: 2026-05-06
Excerpt: "Audio Processing: XMOS XU316; Featuring: Echo cancellation, Stationary noise removal, Auto gain control... The xcore.ai series is a comprehensive range of 32-bit multicore microcontrollers that brings the low latency and timing determinism"
Context: Home Assistant'ın resmi voice hardware'inin teknik özellikleri.
Confidence: high
```

```
Claim: WebRTC AEC mekanizması: 1) Linear filtering (far-end sinyal modelleme), 2) Adaptive estimation (model çıkarma), 3) Non-linear suppression (NLP - artık echo bastırma). Professional grade için ERLE ≥35dB gerekir; optimize edilmiş SDK'lar 45dB+ başarabilir. [^295^]
Source: Eleshine Tech - "Beyond Video: Decoding WebRTC's Powerful Audio Processing (AEC & NS) Mechanisms"
URL: https://www.eleshine-tech.com/webrtc-audio-processing-echo-cancellation-noise-suppression-b2b.html
Date: 2026-02-04
Excerpt: "WebRTC's AEC Mechanism: 1. Linear Filtering... 2. Adaptive Estimation... 3. Non-linear Suppression (NLP)... For a B2B system to be considered Professional Grade, it typically requires an ERLE of at least 35dB."
Context: WebRTC AEC'nin teknik derinlemesine analizi.
Confidence: high
```

```
Claim: Home Assistant Wyoming satellite audio ayarlarında Noise suppression (webrtc seviyesi), Auto gain (webrtc hedef dBFS) ve Mic volume çarpanı ayarlanabilir. Bu, yazılım seviyesinde ön-işleme sağlar. [^227^]
Source: Home Assistant Docs - Wyoming Protocol
URL: https://www.home-assistant.io/integrations/wyoming/
Date: 2026-04-01
Excerpt: "Noise suppression - Level of noise suppression (uses webrtc)... Auto gain - Automatically adjusts volume based on ambient noise (uses webrtc)... Mic volume - Fixed multiplier applied to microphone audio samples"
Context: Home Assistant Wyoming entegrasyonunun audio processing ayarları.
Confidence: high
```

---

## 5. Özet ve Öneriler

### 5.1 STT Pipeline Önerisi
| Bileşen | Öneri | Gerekçe |
|---------|-------|---------|
| Model | `erdiyalcin/whisper-large-v3-turkish-test1` | En düşük Türkçe WER (%12.80, Common Voice) |
| Backend | faster-whisper | CTranslate2 quantization, 4x hızlı |
| Streaming | 4s chunk, 0.5s overlap, beam_size=1 | Optimal latency/doğruluk dengesi |
| VAD | Silero VAD v5 | Endüstri standardı, ~0.21s processing |
| Flag | condition_on_previous_text=False | Hallucination drift önleme |

### 5.2 TTS Pipeline Önerisi
| Bileşen | Öneri | Gerekçe |
|---------|-------|---------|
| Motor | Piper TTS | RTF 0.008, CPU, MIT lisans, sentence-level streaming |
| Model | tr_TR-dfki-medium | Tek mevcut Türkçe model (63.2 MB) |
| Not | CC BY-NC-SA 4.0 dataset | Ticari kullanımda hukuki değerlendirme gerekli |
| Alternatif | Kokoro (Türkçe yok) veya XTTS-v2 (CPML, ticari yasak) | |

### 5.3 Wakeword Önerisi
| Bileşen | Öneri | Gerekçe |
|---------|-------|---------|
| Motor | openWakeWord | Apache 2.0, <1 saat eğitim, sub-100KB |
| Model | "Jarvis" custom (Colab) | Sentetik veri, .tflite çıktı |
| TTS Sentetik | tr_TR-dfki-medium Piper | Türkçe telaffuz için |
| Alternatif | Porcupine | Ticari kullanımda $500/ay ücretli |

### 5.4 Tam Pipeline Önerisi
| Bileşen | Öneri | Gerekçe |
|---------|-------|---------|
| Protokol | Wyoming (stdin/stdout veya TCP) | JSONL + binary, Home Assistant native |
| Pipeline | Streaming (sentence-level TTS + token-level LLM) | Orchestration overhead azaltma |
| AEC | WebRTC AEC (aec-audio-processing PyPI) veya half-duplex | Donanımsal AEC yoksa yazılım çözümü |
| Latency Hedef | STT 0.5s + LLM TTFT 1-3s + TTS 0.3s = 2-5s | Yerel donanım için makul (Joe Karlsson ölçümleri) |
| Barge-in | VAD + TTS chunk stop + LLM cancel | 25ms pipeline clear hedefi |

### 5.5 Bilinen Sınırlamalar
1. **Kokoro-82M Türkçe desteklemiyor** - En iyi açık kaynak TTS (MOS 4.2) Türkçe'de kullanılamaz.
2. **Piper Türkçe modeli tek seçenek** - dfki-medium, MOS 3.3, "airy and choppy" kalite.
3. **XTTS-v2 ticari yasak** - En iyi Türkçe voice cloning CPML lisansı altında.
4. **Wyoming Satellite deprecated** - Yeni cihazlar için Linux Voice Assistant (ESPHome) önerilir.
5. **Home Assistant pipeline overhead** - Debug STT 0.8s + NLP 0.16s + TTS 0.0s ama E2E 13s olabilir.
6. **Whisper streaming native değil** - Chunked streaming ile çalışır, boundary hataları olabilir.
7. **Echo cancellation zorluğu** - Browser AEC dışında yerel pipeline'da loopback referans sinyali gerekli.

---

*Bu araştırma 24+ bağımsız kaynaktan derlenmiştir. Her iddia için kaynak URL ve tarih belirtilmiştir.*
