#!/bin/bash
# n8n credentials import script
# Run this AFTER n8n starts up to pre-populate credentials.
# Usage: ./n8n/setup/import-credentials.sh
# Requires: N8N_API_KEY from env or manual n8n user setup

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:-}"

if [ -z "$N8N_API_KEY" ]; then
  echo "⚠️  No N8N_API_KEY set. Credentials must be set up manually in the n8n UI."
  echo ""
  echo "Manual setup steps:"
  echo "  1. Open http://localhost:5678"
  echo "  2. Create an owner account"
  echo "  3. Go to Settings → Credentials"
  echo "  4. Add SMTP credential using environment variables:"
  echo "       Host: \$SMTP_HOST"
  echo "       Port: \$SMTP_PORT"
  echo "       User: \$SMTP_USER"
  echo "       Password: \$SMTP_PASSWORD"
  echo "  5. Add Telegram credential:"
  echo "       Access Token: \$TELEGRAM_BOT_TOKEN"
  echo "  6. Import workflows from n8n/workflows/*.json"
  exit 1
fi

echo "Importing SMTP credential..."
curl -s -X POST "$N8N_URL/rest/credentials" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @n8n/credentials/smtp-credential.json

echo "Importing Telegram credential..."
curl -s -X POST "$N8N_URL/rest/credentials" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @n8n/credentials/telegram-credential.json

echo "Credentials imported successfully!"
