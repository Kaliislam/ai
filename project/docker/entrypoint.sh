#!/bin/bash
# TurkishJARVIS Docker entrypoint

set -e

# Pull Ollama model if available (optional, best-effort)
if [ -n "${JARVIS_OLLAMA_BASE_URL:-}" ]; then
    echo "Ollama URL: $JARVIS_OLLAMA_BASE_URL"
fi

# Ensure data dirs exist
mkdir -p /app/data/chroma /app/data/uploads

exec "$@"
