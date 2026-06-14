# Text-to-SQL RAG System — User Guide

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Asking Questions](#asking-questions)
3. [Web Chat Interface](#web-chat-interface)
4. [REST API](#rest-api)
5. [Scheduled Reports](#scheduled-reports)
6. [Receiving Reports](#receiving-reports)
7. [Telegram Bot](#telegram-bot)
8. [n8n Workflows](#n8n-workflows)
9. [Tips & Best Practices](#tips--best-practices)
10. [FAQ](#faq)

---

## Getting Started

### What is Text-to-SQL RAG?

This system lets you ask questions in plain English and get answers from your
database — without knowing SQL. It uses AI to understand your question,
generate the right SQL query, run it against MySQL, and return the answer
in conversational language.

**Example:**
```
You:  "What were our top 5 products by revenue last month?"
System: "Your top 5 products by revenue last month were:
         1. Laptop Pro — $25,000
         2. Smartphone X — $18,000
         3. Wireless Headphones — $7,500
         4. Running Shoes — $5,200
         5. Yoga Mat Premium — $3,200"
```

### Access Methods

| Method | How to Access |
|---|---|
| **Web Chat** | Open `http://localhost:8000/chat` in your browser |
| **REST API** | Use `POST /api/query` with your API key |
| **Telegram Bot** | Send `/ask <question>` to your bot |
| **n8n Workflows** | Trigger via n8n webhook URL |

### Authentication

You need an account to use the system. Your administrator will provide:

- **Username and password** — for interactive use (web chat, Telegram)
- **API Key** — for programmatic use (REST API, n8n)

To log in via API:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
# → Returns an access_token (valid for 24 hours)
```

To get your API key (after logging in):
```bash
curl -X POST http://localhost:8000/api/auth/api-key \
  -H "Authorization: Bearer <your-token>"
# → Returns: {"api_key": "tsq_abc123..."}
```

---

## Asking Questions

### What You Can Ask

The system understands questions about:

**Sales & Revenue**
- "What were total sales this month?"
- "Which day had the highest revenue?"
- "What's the average order value?"

**Products**
- "List our top 10 best-selling products."
- "Which products have low stock?"
- "What's the most expensive product?"

**Customers**
- "How many customers do we have?"
- "Which city has the most customers?"
- "Show me orders from Alice Johnson."

**Orders**
- "How many orders are pending?"
- "What's the cancellation rate?"
- "Which month had the most orders?"

**Trends & Comparisons**
- "Compare sales this month vs last month."
- "What was our revenue growth rate?"

### How Questions Work

1. **Triage** — The system checks if your question is data-related, general,
   or out of scope
2. **Schema Analysis** — AI identifies which tables and columns are needed
3. **SQL Generation** — AI writes a MySQL SELECT query
4. **Execution** — The query runs against the database (with safety limits)
5. **Validation** — AI checks if the results answer your question
6. **Response** — Results are formatted into a natural language answer

### Tips for Better Questions

| Do ✅ | Don't ❌ |
|---|---|
| "Show me total sales by category" | "Get data" |
| "What were sales between Jan 1 and Jan 31?" | "Give me numbers" |
| "List the top 5 products by revenue" | "Top products" |
| "How many orders are in 'shipped' status?" | "Give me the orders" |
| "Compare revenue this year vs last year" | "Do comparison" |

---

## Web Chat Interface

### Access

Open `http://localhost:8000/chat` in your browser.

### Using the Chat

1. Type your question in the text input at the bottom
2. Press Enter or click Send
3. The assistant will think and respond with your answer
4. You can ask follow-up questions in the same session

### Example Conversation

```
You: What were our total sales last month?
Bot: Let me check... Total sales last month were $124,500 across 230 orders.

You: Which product contributed the most?
Bot: Laptop Pro was the top contributor with $45,000 in revenue (36% of total).

You: What about the lowest performing product?
Bot: The lowest was Wireless Headphones at $7,500. However, they had the
    highest quantity sold (150 units), suggesting a lower price point.
```

### Session Persistence

Each WebSocket connection maintains its own conversation context.
Closing or refreshing the page starts a new session.

---

## REST API

### Query Endpoint

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tsq_your-api-key" \
  -d '{"question": "What were total sales last month?"}'
```

**Response:**
```json
{
  "answer": "Total sales last month were $124,500 across 230 orders.",
  "sql_query": "SELECT SUM(total) ...",
  "row_count": 1,
  "execution_time_ms": 450
}
```

### Endpoint Summary

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/query` | POST | Required | Ask a data question |
| `/api/auth/login` | POST | No | Get access token |
| `/api/auth/me` | GET | Required | Your profile |
| `/api/auth/api-key` | POST | Required | Generate API key |
| `/api/tasks` | GET | Required | List available reports |
| `/api/tasks/{id}/execute` | POST | Required | Run a report now |
| `/api/schema` | GET | Required | Show available tables |

### Authentication Headers

Choose one:
```bash
# JWT Bearer token
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# API Key
-H "X-API-Key: tsq_abc123def456..."
```

### Error Responses

```json
// 401 — Missing or invalid authentication
{"error": {"code": 401, "message": "Authentication required", "type": "http_error"}}

// 429 — Too many requests
{"error": {"code": 429, "message": "Rate limit exceeded", "type": "rate_limit"}}

// 400 — Out of scope question
{"error": {"code": 400, "message": "I cannot answer that question.", "type": "http_error"}}
```

---

## Scheduled Reports

### What Are Scheduled Reports?

Scheduled reports are automated Excel files generated on a cron schedule
and delivered via email. Your administrator creates these, but you can
opt in or view past reports.

### Viewing Available Reports

```bash
curl http://localhost:8000/api/tasks \
  -H "X-API-Key: tsq_your-key"
```

### Manually Running a Report

```bash
curl -X POST http://localhost:8000/api/tasks/1/execute \
  -H "X-API-Key: tsq_your-key"
```

### Execution History

```bash
curl http://localhost:8000/api/tasks/1/logs \
  -H "X-API-Key: tsq_your-key"
```

---

## Receiving Reports

### Via Email

When a scheduled report runs, you'll receive an email with:

- **Subject:** Customizable per report (e.g., "Weekly Sales Report — June 14, 2026")
- **Body:** Summary text or HTML description
- **Attachments:** Excel (.xlsx) files or zip archives

If multiple reports are generated in one task, they are combined into a
single zip file before being attached.

### Via Telegram

If your administrator has set up Telegram delivery, you'll receive:

- A text message with the report summary
- Excel files sent as documents

You can also interact with the bot:

```
/start          → Welcome message
/ask What were sales?  → Query and reply in chat
/list_tasks     → Show available reports
/run 1          → Execute report #1 now
```

---

## Telegram Bot

### Setup

1. Find your bot on Telegram (your admin will share the bot name)
2. Start a chat with `/start`
3. Use the commands below

### Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and usage instructions |
| `/ask <question>` | Ask a data question and get an answer |
| `/list_tasks` | List all scheduled reports you can access |
| `/run <task_id>` | Manually trigger a report and receive it |

### Example

```
You:  /ask What were total sales this week?
Bot:  Total sales this week were $32,450 across 67 orders.
      The top day was Tuesday with $8,900.

You:  /ask Which products need restocking?
Bot:  Products with low stock (under 50 units):
      1. Laptop Pro — 25 remaining
      2. Winter Jacket — 15 remaining
      Would you like me to generate a full inventory report?
```

---

## n8n Workflows

### What is n8n?

n8n is a workflow automation tool. Your team may use it to create complex
automation pipelines that involve the text-to-SQL system.

### Imported Workflows

Your administrator may have imported pre-built workflows:

| Workflow | What It Does |
|---|---|
| **Webhook → Query → Email** | Call a URL with a question → get answer via email |
| **Daily Digest** | Runs 3 queries every morning → emails a summary |
| **Telegram Query Bot** | Ask questions via Telegram → get replies |
| **Slack Slash Command** | Type `/ask` in Slack → get answers in Slack |

### Using a Webhook Workflow

If a workflow uses a webhook trigger, you'll get a URL like:
```
http://localhost:5678/webhook/text-to-sql-query
```

Send a POST request:
```bash
curl -X POST http://localhost:5678/webhook/text-to-sql-query \
  -H "Content-Type: application/json" \
  -d '{"question": "What were sales yesterday?", "email": "you@company.com"}'
```

The workflow will:
1. Call the text-to-SQL API
2. Format the answer
3. Email it to you

---

## Tips & Best Practices

### Getting Better Answers

1. **Be specific about time periods**
   - ✅ "What were sales in March 2026?"
   - ❌ "What were sales?"

2. **Mention the metric you want**
   - ✅ "Show me total revenue by product category"
   - ❌ "Show me products"

3. **Use natural numbers**
   - ✅ "List the top 10 customers"
   - ❌ "List the best customers"

4. **Specify sorting**
   - ✅ "Show products ordered by price descending"
   - ✅ "What are the most expensive products?"

### Understanding Limitations

- The system answers based ONLY on data in the database
- It cannot access external websites or real-time data outside MySQL
- Complex multi-step questions may need to be broken down
- The system enforces a maximum of 1,000 rows per query
- Queries time out after 30 seconds

### Data Freshness

The database contains data up to the last point it was synced.
If you need real-time data, ask your administrator about the
refresh schedule.

### Privacy

- All queries are logged for audit purposes
- Questions and answers are sent to OpenAI for processing
- Never include sensitive personal information in your questions

---

## FAQ

**Q: What if the system doesn't understand my question?**
A: Try rephrasing. Be more specific about what data you want and the time
period. If it still doesn't work, the data you're looking for may not
exist in the database.

**Q: Can I ask about data that's not in the database?**
A: The system will tell you if it can't find relevant data. General
questions (like "What's the weather?") are recognized and redirected to
ask a data-related question instead.

**Q: How long does a query take?**
A: Most queries return in 2-5 seconds. Complex queries involving large
datasets may take up to 30 seconds.

**Q: Can I download the raw data?**
A: Scheduled reports generate Excel files you can download via email
or Telegram. For ad-hoc queries, use the API and save the JSON response.

**Q: What format are report files in?**
A: Reports are generated as Excel (.xlsx) files with formatted columns.
If a task produces multiple reports, they are combined into a .zip file.

**Q: How do I report a problem?**
A: If you get an error or unexpected result:
1. Note what question you asked
2. Check if the error is repeatable
3. Contact your administrator with the details

**Q: Can I share results with my team?**
A: Forward the email report or share the query results manually.
The system does not currently have built-in sharing features.

**Q: What happens to my API key if I forget it?**
A: Generate a new one via `POST /api/auth/api-key`. The old key will
stop working.

**Q: Is my data safe?**
A: Yes. All connections use encryption. Queries are read-only (SELECT only).
API keys are stored securely. Rate limiting prevents abuse. Logs are
retained for audit and automatically purged after 30 days.
