# n8n Integration for Text-to-SQL RAG

Pre-built workflows, webhook endpoints, and Docker setup to connect
[n8n](https://n8n.io) with the Text-to-SQL system.

---

## Quick Start

```bash
# Start everything (app + mysql + n8n)
docker compose --profile n8n up -d

# n8n UI: http://localhost:5678
# App API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Architecture

```
┌─────────────┐     HTTP      ┌──────────────────┐
│   n8n       │ ──────────►   │  FastAPI App      │
│  (workflow  │               │  POST /api/n8n/*  │
│   engine)   │ ◄──────────── │  GET  /api/n8n/*  │
└─────────────┘     JSON      └──────────────────┘
       │
       │ triggers / schedules
       ▼
┌─────────────┐
│  Email      │
│  Telegram   │
│  Slack      │
│  Webhook    │
└─────────────┘
```

## n8n Webhook Endpoints

All endpoints are at `http://app:8000/api/n8n/*` (inside Docker) or
`http://localhost:8000/api/n8n/*` (from host).

| Endpoint | Method | Description |
|---|---|---|
| `/api/n8n/webhook/query` | POST | Question in → answer + metadata out |
| `/api/n8n/webhook/query-simple` | POST | Question in → plain answer text out |
| `/api/n8n/webhook/query-and-send` | POST | Query + auto-deliver via email or Telegram |
| `/api/n8n/webhook/execute-task` | POST | Trigger a scheduled report task |
| `/api/n8n/tasks` | GET | List all scheduled tasks (for n8n dropdowns) |
| `/api/n8n/schema` | GET | Database schema as JSON |
| `/api/n8n/schema/text` | GET | Database schema as text (for LLM prompts) |

## Pre-built Workflows

Import these from the n8n UI → **Workflows** → **Import from File**.

| File | Purpose |
|---|---|
| `01-webhook-query-email.json` | Webhook receives a question → queries → emails result |
| `02-scheduled-report-email.json` | Cron trigger → executes a scheduled task → emails report |
| `03-slack-query-bot.json` | Slack slash command → queries → replies in Slack |
| `04-daily-digest-email.json` | Daily cron → runs 3 queries → merges → sends digest email |
| `05-telegram-query-bot.json` | Telegram `/ask` command → queries → replies in chat |

## Credentials Setup

n8n needs credentials for SMTP, Telegram, and Slack nodes.

### Option A: Manual (Recommended)

1. Open `http://localhost:5678`
2. Create an owner account
3. Go to **Settings → Credentials → Add Credential**
4. **SMTP**: Host=`$SMTP_HOST`, Port=`$SMTP_PORT`, User=`$SMTP_USER`, Password=`$SMTP_PASSWORD`
5. **Telegram API**: Access Token=`$TELEGRAM_BOT_TOKEN`
6. **Slack API** (optional): Add your Slack bot token

### Option B: Scripted

```bash
# Requires n8n owner API key
export N8N_API_KEY="your-api-key"
bash n8n/setup/import-credentials.sh
bash n8n/setup/import-workflows.sh
```

## Using Webhook Workflows

Each webhook-based workflow creates a unique URL in n8n like:

```
http://localhost:5678/webhook/text-to-sql-query
```

Send a POST with JSON body:

```json
{
  "question": "What were total sales last month?",
  "email": "manager@company.com"
}
```

The workflow will query the Text-to-SQL system and send the result.

## Using Scheduled Workflows

The `02-scheduled-report-email.json` and `04-daily-digest-email.json` workflows
use n8n's Schedule Trigger. They will:

1. Fire at the configured cron time
2. Call our API to execute tasks or run queries
3. Deliver results via email

To customize the schedule:
1. Open the workflow in n8n
2. Double-click the Schedule Trigger node
3. Adjust the cron expression

## Example: Slack Integration

1. Create a Slack app with a Slash Command (e.g., `/ask`)
2. Set the Request URL to `http://localhost:5678/webhook/slack-text-to-sql`
3. Import `03-slack-query-bot.json` into n8n
4. Activate the workflow
5. Type `/ask What were our top 5 products?` in Slack

## Example: Telegram Integration

1. Create a bot via [@BotFather](https://t.me/BotFather) and get the token
2. Set `TELEGRAM_BOT_TOKEN` in `.env`
3. Import `05-telegram-query-bot.json`
4. Configure the Telegram Trigger node with your bot token
5. Activate the workflow
6. Send `/ask What were total sales?` to your bot

## Troubleshooting

**n8n can't reach the app service**
- Ensure both are on the same Docker network (they are by default)
- Test with: `docker compose exec n8n curl http://app:8000/health`

**Webhook returns 404**
- Activate the workflow in n8n (toggle switch at the top)
- Check the webhook URL path matches the node configuration

**Email not sending**
- Verify SMTP credentials in n8n
- Check SMTP_HOST is accessible from the n8n container
- Gmail users may need an [App Password](https://support.google.com/accounts/answer/185833)

**Workflows not showing**
- Use **Import from File** in the n8n UI
- Or run: `bash n8n/setup/import-workflows.sh`
