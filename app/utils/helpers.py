import json
import re
import time
import logging

from config.app import Settings
from openai import OpenAI
from app.logging.llm_logger import log_llm_call


settings = Settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger("app.utils")


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    max_tokens: int = 1024,
    request_id: str = "",
) -> str:
    """Call OpenAI LLM with logging of every call."""
    model = model or settings.OPENAI_MODEL
    start = time.time()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.1,
        )

        result = response.choices[0].message.content.strip()
        duration = int((time.time() - start) * 1000)

        usage = response.usage
        log_llm_call(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=result,
            duration_ms=duration,
            success=True,
            tokens_prompt=usage.prompt_tokens if usage else 0,
            tokens_completion=usage.completion_tokens if usage else 0,
            request_id=request_id,
        )

        return result

    except Exception as e:
        duration = int((time.time() - start) * 1000)
        log_llm_call(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response="",
            duration_ms=duration,
            success=False,
            error_message=str(e),
            request_id=request_id,
        )
        logger.error("LLM call failed: %s", e)
        raise


def parse_json(text: str) -> dict:
    """Extract and parse JSON from LLM response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:200]}")


def format_results(results: list[dict], max_rows: int = 20) -> str:
    """Format query results as a readable table string."""
    if not results:
        return "No results returned."

    lines = []
    headers = list(results[0].keys())
    header_line = " | ".join(headers)
    sep = "-" * len(header_line)
    lines.append(header_line)
    lines.append(sep)

    for row in results[:max_rows]:
        values = []
        for h in headers:
            v = row.get(h, "")
            if v is None:
                v = "NULL"
            values.append(str(v))
        lines.append(" | ".join(values))

    if len(results) > max_rows:
        lines.append(f"... and {len(results) - max_rows} more rows")

    return "\n".join(lines)


def format_results_for_prompt(results: list[dict], max_rows: int = 10) -> str:
    """Format results concisely for LLM prompt context."""
    if not results:
        return "No results returned."

    lines = []
    for i, row in enumerate(results[:max_rows]):
        parts = [f"{k}={v}" for k, v in row.items()]
        lines.append(f"Row {i + 1}: {', '.join(parts)}")

    if len(results) > max_rows:
        lines.append(f"... and {len(results) - max_rows} more rows")

    return "\n".join(lines)
