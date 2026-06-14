#!/bin/bash
# Import all n8n workflow templates from n8n/workflows/
# Usage: ./n8n/setup/import-workflows.sh [n8n-url]
# Requires n8n owner API key in N8N_API_KEY env var

N8N_URL="${1:-http://localhost:5678}"
WORKFLOW_DIR="$(dirname "$0")/../workflows"

if [ -z "$N8N_API_KEY" ]; then
  echo "⚠️  No N8N_API_KEY set."
  echo "To get your API key:"
  echo "  1. Open n8n UI at $N8N_URL"
  echo "  2. Settings → API → Create API Key"
  echo "  3. Export: export N8N_API_KEY='your-key-here'"
  exit 1
fi

echo "Importing workflows from $WORKFLOW_DIR..."
for file in "$WORKFLOW_DIR"/*.json; do
  name=$(basename "$file" .json)
  echo "  Importing: $name..."
  
  # Read workflow JSON and update name/remove ids
  workflow=$(cat "$file" | python3 -c "
import json, sys
wf = json.load(sys.stdin)
# Remove auto-generated fields so n8n creates fresh ones
wf.pop('id', None)
wf.pop('webhookId', None)
wf.pop('versionId', None)
for node in wf.get('nodes', []):
    node.pop('id', None)
    node.pop('webhookId', None)
print(json.dumps(wf))
")

  curl -s -X POST "$N8N_URL/rest/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$workflow" > /dev/null && echo "  ✅ Imported" || echo "  ❌ Failed"
done

echo "All workflows imported. Check n8n UI at $N8N_URL"
