import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.triage import triage_question
from app.agents.table_selector import select_tables, get_filtered_schema
from app.agents.sql_generator import generate_sql
from app.agents.sql_executor import execute_sql
from app.agents.responder import generate_response


logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)

    async def send(self, ws: WebSocket, message: dict):
        await ws.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await manager.send(websocket, {
            "role": "assistant",
            "content": "Hello! I can help you query data. Ask me a question about customers, products, orders, or sales.",
        })

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            question = msg.get("content", "").strip()

            if not question:
                continue

            await manager.send(websocket, {"role": "user", "content": question})
            await manager.send(websocket, {"role": "assistant", "content": "Thinking..."})

            try:
                answer = await _process_question(question)
                await manager.send(websocket, {"role": "assistant", "content": answer})
            except Exception as e:
                logger.error(f"Query error: {e}")
                await manager.send(websocket, {
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {str(e)}",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _process_question(question: str) -> str:
    """Process a question through the full pipeline (async wrapper)."""
    classification = triage_question(question)
    category = classification.get("category", "general")

    if category == "out_of_scope":
        return f"I cannot answer that. {classification.get('reason', '')}"

    if category == "general":
        return "I'm a data analysis assistant. Try asking about sales, customers, or products."

    selected = select_tables(question)
    filtered_schema = get_filtered_schema(selected)
    sql_query, _ = generate_sql(question, filtered_schema, str(selected.get("tables", [])))

    if not sql_query:
        return "I couldn't generate a query. Could you rephrase?"

    result = execute_sql(sql_query)
    if not result["success"]:
        return f"Database error: {result['error']}"

    return generate_response(question, sql_query, result["results"], result["row_count"])
