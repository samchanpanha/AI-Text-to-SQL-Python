#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "╔══════════════════════════════════════════════╗"
echo "║   Text-to-SQL — Development Mode             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Prerequisites ──
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required. Install it from https://docs.docker.com/get-docker/"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "❌ docker compose is required."; exit 1; }

# ── Create .env from template if missing ──
if [ ! -f .env ]; then
  if [ -f .env.template ]; then
    cp .env.template .env
    echo "📝 Created .env from .env.template"
    echo "⚠️  Edit .env with your OpenAI API key and other settings before starting"
    echo ""
  fi
fi

# ── Create frontend .env if missing ──
if [ ! -f nuxt/.env ]; then
  if [ -f nuxt/.env.example ]; then
    cp nuxt/.env.example nuxt/.env
    echo "📝 Created nuxt/.env from nuxt/.env.example"
  fi
fi

# ── Check for required keys ──
if grep -q "sk-your-key-here" .env 2>/dev/null; then
  echo "⚠️  WARNING: OpenAI API key is still the placeholder."
  echo "   Edit .env and set OPENAI_API_KEY before running queries."
  echo ""
fi

# ── Start services ──
echo "🚀 Starting all services in development mode..."
echo "   Frontend: http://localhost:3000"
echo "   API:      http://localhost:8000"
echo "   Health:   http://localhost:8000/health"
echo ""

docker compose up --build
