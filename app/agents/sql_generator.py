from app.utils.helpers import call_llm, parse_json
from config.app import Settings


settings = Settings()

SYSTEM_PROMPT = open("app/prompts/sql_gen.txt").read()
SQL_FIX_PROMPT = open("app/prompts/sql_fix.txt").read()


def generate_sql(question: str, schema: str, selected_tables: str, max_retries: int = 2) -> tuple[str | None, str | None]:
    """Generate a SQL query. Returns (sql, explanation) or (None, None) on failure."""
    user_prompt = (
        f"Schema:\n{schema}\n\n"
        f"Relevant tables and columns:\n{selected_tables}\n\n"
        f"User question: {question}\n"
        f"Max rows: {settings.QUERY_MAX_ROWS}"
    )

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=settings.OPENAI_MODEL,
        max_tokens=settings.OPENAI_MAX_TOKENS,
    )

    try:
        parsed = parse_json(result)
        return parsed.get("sql_query"), parsed.get("explanation")
    except ValueError:
        return None, None


def fix_sql(sql_query: str, error: str, question: str, schema: str) -> tuple[str | None, str | None]:
    """Fix a broken SQL query using the error message."""
    user_prompt = (
        f"SQL query:\n{sql_query}\n\n"
        f"Error:\n{error}\n\n"
        f"Schema:\n{schema}\n\n"
        f"Question: {question}"
    )

    result = call_llm(
        system_prompt=SQL_FIX_PROMPT,
        user_prompt=user_prompt,
        model=settings.OPENAI_MODEL,
        max_tokens=settings.OPENAI_MAX_TOKENS,
    )

    try:
        parsed = parse_json(result)
        return parsed.get("sql_query"), parsed.get("explanation")
    except ValueError:
        return None, None
