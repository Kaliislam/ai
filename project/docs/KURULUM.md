# TurkishJARVIS v4.0 — "176 Agent Swarm" Hatasız Kurulum Kılavuzu

> "Her zaman hizmetinizdeyim efendim. 176 uzmanım hazır."

---

## ⚡ Hızlı Kurulum (5 Adım)

```bash
# 1. Projeyi indir
cd ~
git clone https://github.com/kullanici/turkish-jarvis.git turkish-jarvis
cd turkish-jarvis

# 2. Otomatik kurulum (tek komut)
chmod +x scripts/setup.sh
./setup.sh

# 3. Çalıştır
source .venv/bin/activate
python turkish_jarvis/main.py

# 4. Tarayıcıda aç
# http://localhost:8000/ui
```

---

## 🔧 Manuel Kurulum (Adım Adım)

### Adım 1: Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| CPU | 4 çekirdek | 8+ çekirdek |
| RAM | 8 GB | 16-32 GB |
| GPU | Yok (CPU çalışır) | NVIDIA 8GB+ VRAM |
| Disk | 10 GB boş | 25 GB boş |
| OS | Ubuntu 22.04 / WSL2 | Ubuntu 24.04 / WSL2 |

### Adım 2: Ollama Kurulumu

```bash
# Linux/WSL
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &

# Model indir (önerilen)
ollama pull qwen3-coder:30b
ollama pull gemma4:latest
ollama pull mistral:latest
```

### Adım 3: Python Sanal Ortamı

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Adım 4: Piper TTS Modeli

```bash
mkdir -p models/piper
cd models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx.json
```

### Adım 5: Çalıştırma

```bash
python turkish_jarvis/main.py
```

---

## 🛠️ Sorun Giderme

### "No module named 'X'" Hatası
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Ollama connection refused" (WSL)
```bash
# Windows Ollama kullanıyorsanız:
export JARVIS_OLLAMA_BASE_URL="http://$(ip route | grep default | awk '{print $3}'):11434"

# Veya .env dosyasına yazın
echo 'JARVIS_OLLAMA_BASE_URL=http://host.docker.internal:11434' >> .env
```

### "ModuleNotFoundError: No module named 'turkish_jarvis'"
```bash
# Proje kök dizininden çalıştırın
cd /path/to/turkish-jarvis
source .venv/bin/activate
python -m turkish_jarvis.main
```

### llama3.1:70b Çok Yavaş
```bash
# Daha hafif model kullanın
JARVIS_OLLAMA_MODEL=gemma4:latest python turkish_jarvis/main.py
```

### Bellek (RAM) Yetersiz
```bash
# WSL RAM limitini artırın:
# Windows'ta %UserProfile%\.wslconfig dosyası oluşturun:
# [wsl2]
# memory=32GB
# processors=8
```

### Port 8000 Kullanımda
```bash
# Farklı port ile çalıştırın
JARVIS_PORT=8080 python turkish_jarvis/main.py
```

---

## 🧪 Test

```bash
source .venv/bin/activate
pytest turkish_jarvis/tests/ -v
```

---

## 🗺️ Sistem Mimarisi (v4.0)

```
Jarvis CEO (llama3.1:70b)
    ↓
    ├── Executive Council (7)
    ├── Engineering Council (15)
    ├── Operations Council (15)
    ├── Research Council (15)
    ├── Creative Council (15)
    ├── Business Council (15)
    ├── Systems Council (15)
    ├── Specialized Council (15)
    ├── Communication Council (15)
    ├── Personal Council (15)
    ├── Knowledge Council (15)
    ├── Tools Council (15)
    ├── Meta Council (15)
    └── AI Action Council (10)
    
    Toplam: 176 ajan
```

---

**Yardım mı lazım?** `http://localhost:8000/health` endpoint'ini kontrol edin.
