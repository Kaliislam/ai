# TurkishJARVIS v3.0 — "Auto-Learning" Mimari Tasarım Dokümanı

## Vizyon
TurkishJARVIS, yalnızca komutları yerine getiren bir asistan değil; **kendi kendine gelişen, hatalarından ders çıkaran, yeni yetenekler edinen, internetten ve belgelerden otomatik öğrenen, karmaşık görevleri alt-ajanlarla planlayıp yürüten** otonom bir AI sistemidir.

## Yeni Modüller (Autonomy Katmanı)

### 1. autonomy/planner.py — Çok Adımlı Planlama Motoru
- **Hierarchical Task Network (HTN)**: Kullanıcı talebini alt-görevlere ayırır
- **ReAct döngüsü**: Düşün (Reason) → Hareket et (Act) → Gözlemle (Observe)
- **Plan yürütme**: Adım adım LLM çağrıları, araç kullanımı, koşullu dallanma
- **Plan onarımı**: Bir adım başarısız olursa alternatif strateji üretme

### 2. autonomy/auto_skill.py — Otomatik Yetenek Edinme
- **İhtiyaç tespiti**: LLM bir görevi yapamadığında, hangi araç/skill eksik analiz eder
- **Araştırma**: İnternet (DuckDuckGo), GitHub README, API docs'tan bilgi toplar
- **Kod üretimi**: LLM ile yeni Python fonksiyonu/araç üretir
- **Sandbox test**: Üretilen kodu güvenli şekilde test eder (Docker/subprocess)
- **Kayıt**: Başarılı testten sonra `tools/` altına kaydeder, registry'ye ekler
- **Dokümantasyon**: Otomatik docstring ve kullanım örneği üretir

### 3. autonomy/meta_learning.py — Meta-Öğrenme Motoru
- **Performans izleme**: Her araç çağrısının başarı/başarısızlık durumunu kaydeder
- **Strateji değerlendirme**: "Hangi yaklaşım daha iyi çalıştı?" analizi
- **LLM prompt optimizasyonu**: Farklı prompt varyasyonlarını test eder, en iyisini seçer
- **Model seçimi öğrenme**: Hangi model (qwen/gemma/mistral) hangi görevde daha iyi?
- **Tecrübe veritabanı**: SQLite'da structured learning log

### 4. autonomy/self_healing.py — Kendi Kendine Düzeltme
- **Hata yakalama**: Bir araç/modül exception fırlattığında
- **Hata analizi**: Stack trace'i LLM'e verir, neden başarısız olduğunu anlamasını ister
- **Kod düzeltme**: LLM düzeltilmiş kod üretir
- **Regresyon testi**: Düzeltilen kodu tekrar test eder
- **Rollback**: Düzeltme başarısız olursa önceki çalışan versiyona döner
- **Log**: Tüm self-healing olaylarını meta-learning'e bildirir

### 5. autonomy/knowledge_miner.py — Bilgi Kazıma
- **Wikipedia**: Madde arama, özet çıkarma, RAG'e ekleme
- **arXiv**: Akademik makale arama, özet çıkarma
- **GitHub**: Repo README okuma, kod örnekleri çıkarma
- **DuckDuckGo**: Genel web arama, snippet toplama
- **Otomatik RAG**: Toplanan bilgileri vektör DB'ye indeksleme
- **Bilgi tazeliği**: Periyodik güncelleme, eski bilgileri pasifleştirme

### 6. autonomy/reflection.py — Düşünce ve Öz-Değerlendirme
- **Chain of Thought**: LLM'in adım adım düşünmesini zorla
- **Öz-değerlendirme**: "Bu yanıt doğru muydu?" sorgusu
- **Yanıt iyileştirme**: İlk yanıtı eleştirip daha iyisini üretme
- **Düşünce özetleme**: Uzun reasoning zincirlerini kompakt hale getirme

### 7. autonomy/orchestrator.py — Ajan Swarm Koordinatörü
- **Uzman ajan tanımları**: KodYazici, Arastirmaci, Analist, HafizaYoneticisi
- **Görev dağıtımı**: Ana talebi uzmanlara bölüştürme
- **Sonuç birleştirme**: Alt-ajan sonuçlarını koherent yanıta dönüştürme
- **Paralel yürütme**: Bağımsız alt-görevleri aynı anda çalıştırma
- **Hata toleransı**: Bir alt-ajan başarısız olursa alternatif ile devam

## Entegrasyon Mimarisi

```
[Kullanıcı Mesajı]
    ↓
[Orchestrator] ←→ [Planner] ←→ [Meta-Learning]
    ↓
[LLM Core] ←→ [Tool Registry] ←→ [Auto-Skill]
    ↓
[Tool Execution] ←→ [Self-Healing]
    ↓
[Knowledge Miner] ←→ [RAG] ←→ [Reflection]
    ↓
[Bellek Katmanları] (SQLite + ChromaDB + Graph)
    ↓
[Yanıt]
```

## main.py Değişiklikleri
- Yeni tüm autonomy modülleri lifespan'da initialize edilecek
- Chat döngüsüne planlama + reflection adımları eklenecek
- Meta-learning her etkileşimden sonra güncellenecek
- Self-healing araç çağrılarına entegre edilecek
- Auto-skill, bilinmeyen bir görev geldiğinde otomatik tetiklenecek
