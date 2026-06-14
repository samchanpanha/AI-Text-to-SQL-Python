import os
import logging

from config.app import Settings


settings = Settings()
logger = logging.getLogger(__name__)


class TelegramBot:
    """Handles Telegram webhook registration and incoming updates."""

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.webhook_url = settings.TELEGRAM_WEBHOOK_URL

    async def set_webhook(self):
        if not self.token or not self.webhook_url:
            return
        try:
            import httpx
            url = f"https://api.telegram.org/bot{self.token}/setWebhook"
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json={"url": self.webhook_url})
                logger.info(f"Telegram webhook set: {resp.json()}")
        except Exception as e:
            logger.error(f"Failed to set Telegram webhook: {e}")

    async def handle_update(self, update: dict):
        """Process an incoming Telegram update."""
        try:
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "").strip()

            if not chat_id or not text:
                return

            if text.startswith("/start"):
                await self._send_message(chat_id,
                    "Hello! I can help you query data and generate reports.\n\n"
                    "Commands:\n"
                    "/ask <question> - Ask a data question\n"
                    "/list_tasks - List scheduled reports\n"
                    "/run <task_id> - Run a report now"
                )
            elif text.startswith("/ask"):
                question = text[5:].strip()
                if question:
                    answer = await self._process_query(question)
                    await self._send_message(chat_id, answer)
                else:
                    await self._send_message(chat_id, "Please provide a question after /ask")
            elif text.startswith("/list_tasks"):
                await self._send_message(chat_id, "Task listing coming soon.")
            elif text.startswith("/run"):
                await self._send_message(chat_id, "Manual task execution coming soon.")
            else:
                await self._send_message(chat_id, "Unknown command. Try /start")
        except Exception as e:
            logger.error(f"Telegram update error: {e}")

    async def _send_message(self, chat_id: int, text: str):
        import httpx
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": chat_id, "text": text})

    async def _process_query(self, question: str) -> str:
        from app.router.query import query
        from app.models.schemas import QueryRequest

        try:
            result = await query(QueryRequest(question=question))
            return result.answer
        except Exception as e:
            return f"Error processing query: {e}"


def send_telegram_report(
    chat_id: str,
    bot_token: str,
    files: list[dict],
    task,
    message_template: str | None = None,
):
    """Send report files via Telegram bot."""
    import httpx

    if not message_template:
        message_template = "Report: {{ task_name }} - {{ date }}"

    from jinja2 import Template
    from email.utils import formatdate

    context = {
        "task_name": task.name,
        "task_description": task.description,
        "date": formatdate(localtime=True),
        "report_count": len(files),
    }
    text = Template(message_template).render(**context)

    with httpx.Client() as client:
        # Send text message
        msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        client.post(msg_url, json={"chat_id": chat_id, "text": text})

        # Send files
        for f in files:
            path = f.get("path")
            name = f.get("name", "report")
            if path and os.path.exists(path):
                doc_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                with open(path, "rb") as fp:
                    client.post(
                        doc_url,
                        data={"chat_id": chat_id},
                        files={"document": (name, fp)},
                    )
