#!/usr/bin/env bash
# TurkishJARVIS WSL/Linux Otomatik Kurulum Script'i v4.0
# 176 ajan, 7 Ollama model, API-key'siz internet arama
# Çalıştır: bash scripts/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"
DATA_DIR="$PROJECT_DIR/data"
MODELS_DIR="$PROJECT_DIR/models"

# Renkli çıktı
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }
header() { echo -e "${BLUE}▶ $*${NC}"; }

# ---------------------------------------------------------------------------
# WSL tespiti
# ---------------------------------------------------------------------------
IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=true
    info "WSL ortamı tespit edildi! 🇪🇺"
fi

# ---------------------------------------------------------------------------
# 1. Sistem bağımlılıkları
# ---------------------------------------------------------------------------
header "1/8 — Sistem bağımlılıkları kontrol ediliyor..."
MISSING_DEPS=()

command -v python3 >/dev/null 2>&1 || MISSING_DEPS+=("python3")
command -v pip3 >/dev/null 2>&1 || MISSING_DEPS+=("python3-pip")
command -v curl >/dev/null 2>&1 || MISSING_DEPS+=("curl")
command -v git >/dev/null 2>&1 || MISSING_DEPS+=("git")

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    warn "Eksik paketler: ${MISSING_DEPS[*]}"
    if command -v apt-get >/dev/null 2>&1; then
        info "apt-get ile kurulum yapılıyor..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq python3 python3-pip python3-venv curl git \
            build-essential libsndfile1 libportaudio2 portaudio19-dev \
            libxml2-dev libxslt1-dev 2>/dev/null || true
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3 python3-pip curl git libsndfile
    elif command -v brew >/dev/null 2>&1; then
        brew install python curl git libsndfile
    else
        error "Paket yöneticisi bulunamadı. Lütfen eksik bağımlılıkları manuel kurun."
        exit 1
    fi
else
    info "Sistem bağımlılıkları tam. ✅"
fi

# ---------------------------------------------------------------------------
# 2. Ollama kontrolü
# ---------------------------------------------------------------------------
header "2/8 — Ollama ve mevcut modeller kontrol ediliyor..."

OLLAMA_URL="${JARVIS_OLLAMA_BASE_URL:-http://localhost:11434}"

if command -v ollama >/dev/null 2>&1; then
    info "Ollama kurulu."
    
    # Mevcut modelleri listele
    info "Mevcut Ollama modelleriniz:"
    MODELS_JSON=$(curl -s "$OLLAMA_URL/api/tags" 2>/dev/null || echo '{"models":[]}')
    echo "$MODELS_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    size_gb = m.get('size', 0) / (1024**3)
    print(f'  • {m[\"name\"]} ({size_gb:.1f} GB)')
" 2>/dev/null || echo "  (Modeller listelenemedi)"
else
    warn "Ollama bulunamadı."
    if [ "$IS_WSL" = true ]; then
        info "WSL'de kurulum: curl -fsSL https://ollama.com/install.sh | sh"
    fi
fi

# ---------------------------------------------------------------------------
# 3. Python venv
# ---------------------------------------------------------------------------
header "3/8 — Python sanal ortamı oluşturuluyor..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    info "Venv oluşturuldu: $VENV_DIR ✅"
else
    info "Venv zaten mevcut. ✅"
fi

source "$VENV_DIR/bin/activate"

# ---------------------------------------------------------------------------
# 4. Python bağımlılıkları
# ---------------------------------------------------------------------------
header "4/8 — Python bağımlılıkları yükleniyor..."
info "pip güncelleniyor..."
pip install --upgrade -q pip setuptools wheel

info "Requirements yükleniyor (biraz sürecek)..."
pip install -q -r "$PROJECT_DIR/requirements.txt"

info "Test bağımlılıkları..."
pip install -q pytest pytest-asyncio ruff 2>/dev/null || true

# ---------------------------------------------------------------------------
# 5. Model optimizasyonu
# ---------------------------------------------------------------------------
header "5/8 — Model optimizasyonu..."

BEST_MODEL="qwen3-coder:30b"
if command -v ollama >/dev/null 2>&1; then
    BEST_MODEL=$(python3 -c "
import subprocess, sys
try:
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    models = [l.split()[0] for l in lines if l.strip()]
    priority = ['qwen3-coder', 'gemma4', 'mistral', 'qwen3', 'deepseek-r1', 'gemma3', 'llama3.1']
    for p in priority:
        for m in models:
            if m.startswith(p):
                print(m)
                sys.exit(0)
    print(models[0] if models else 'qwen3-coder:30b')
except Exception:
    print('qwen3-coder:30b')
" 2>/dev/null || echo "qwen3-coder:30b")
fi

info "Önerilen model: $BEST_MODEL ✅"

# ---------------------------------------------------------------------------
# 6. Piper TTS modeli
# ---------------------------------------------------------------------------
header "6/8 — Piper TTS modeli..."
PIPER_DIR="$MODELS_DIR/piper"
mkdir -p "$PIPER_DIR"

if [ ! -f "$PIPER_DIR/tr_TR-dfki-medium.onnx" ]; then
    info "Piper Türkçe modeli indiriliyor..."
    curl -sL -o "$PIPER_DIR/tr_TR-dfki-medium.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx" || warn "ONNX indirilemedi"
    curl -sL -o "$PIPER_DIR/tr_TR-dfki-medium.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx.json" || warn "Config indirilemedi"
else
    info "Piper modeli zaten mevcut. ✅"
fi

# ---------------------------------------------------------------------------
# 7. Data dizinleri ve .env
# ---------------------------------------------------------------------------
header "7/8 — Veri dizinleri ve yapılandırma..."
mkdir -p "$DATA_DIR/chroma" "$DATA_DIR/uploads" "$DATA_DIR/sessions" \
         "$DATA_DIR/knowledge_base" "$DATA_DIR/backups" "$DATA_DIR/skill_store"
info "Data dizinleri hazır. ✅"

ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    info ".env şablonu oluşturuluyor..."
    cat > "$ENV_FILE" <<EOF
# TurkishJARVIS v4.0 — 176 Agent Swarm Yapılandırma
# Tarih: $(date '+%Y-%m-%d')

# Ollama LLM
JARVIS_OLLAMA_BASE_URL=$OLLAMA_URL
JARVIS_OLLAMA_MODEL=$BEST_MODEL
JARVIS_OLLAMA_TIMEOUT=180
JARVIS_OLLAMA_FALLBACK_MODELS=gemma4:latest,mistral:latest,qwen3:4b
JARVIS_OLLAMA_AUTO_DETECT=true

# WSL: Windows Ollama kullanıyorsanız:
# JARVIS_OLLAMA_BASE_URL=http://host.docker.internal:11434

# STT/TTS
JARVIS_STT_MODEL=large-v3
JARVIS_TTS_MODEL_PATH=./models/piper/tr_TR-dfki-medium.onnx
JARVIS_TTS_CONFIG_PATH=./models/piper/tr_TR-dfki-medium.json

# Bellek
JARVIS_CHROMA_PERSIST_DIR=./data/chroma
JARVIS_SQLITE_PATH=./data/jarvis.db

# Kişilik
JARVIS_VOICE_NAME=Jarvis
JARVIS_PERSONALITY_STYLE=professional_friendly

# Server
JARVIS_HOST=0.0.0.0
JARVIS_PORT=8000

# Opsiyonel entegrasyonlar
# HOME_ASSISTANT_URL=http://homeassistant.local:8123
# HOME_ASSISTANT_TOKEN=your_token_here
# SEARXNG_URL=http://localhost:8080
EOF
    info ".env oluşturuldu ($BEST_MODEL seçildi). ✅"
fi

# ---------------------------------------------------------------------------
# 8. Kullanıcı profili
# ---------------------------------------------------------------------------
header "8/8 — Kullanıcı profili..."
if [ ! -f "$DATA_DIR/user_profile.md" ]; then
    cat > "$DATA_DIR/user_profile.md" <<'EOF'
# TurkishJARVIS — Kullanıcı Profili

## Kişisel Bilgiler
- tercih_edilen_hitap: "efendim"
- dil: "Türkçe"
- asistan_adi: "Jarvis"
- asistan_stili: "professional_friendly"

## Mevcut AI Modelleri (Ollama)
- qwen3-coder:30b, llama3.1:70b, gemma4:latest, deepseek-r1:8b
- qwen3:4b, mistral:latest, gemma3:4b

## Sistem
- platform: "WSL (Windows Subsystem for Linux)"
- kurulum_tarihi: "2026-05-07"
EOF
    info "Kullanıcı profili şablonu oluşturuldu. ✅"
fi

# ---------------------------------------------------------------------------
# Bitiş
# ---------------------------------------------------------------------------
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       TurkishJARVIS v4.0 Kurulum Tamamlandı!               ║"
echo "║         176 Ajan | 7 Model | API-Key'siz Arama             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
info "Önerilen model: $BEST_MODEL"
echo ""
echo "Çalıştırmak için:"
echo "  source .venv/bin/activate"
echo "  python turkish_jarvis/main.py"
echo ""
echo "Farklı model ile:"
echo "  JARVIS_OLLAMA_MODEL=gemma4:latest python turkish_jarvis/main.py"
echo ""
echo "Test: pytest turkish_jarvis/tests/ -v"
echo ""
if [ "$IS_WSL" = true ]; then
    echo "WSL İpuçları:"
    echo "  • Windows Ollama: JARVIS_OLLAMA_BASE_URL=http://host.docker.internal:11434"
    echo "  • WSL Ollama: curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
fi
