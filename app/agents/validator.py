from app.utils.helpers import call_llm, parse_json, format_results_for_prompt
from config.app import Settings


settings = Settings()

SYSTEM_PROMPT = open("app/prompts/validate.txt").read()


def validate_results(question: str, sql_query: str, results: list[dict], row_count: int) -> dict:
    """Check if query results answer the user's question."""
    sample = format_results_for_prompt(results, max_rows=10)
    user_prompt = (
        f"Question: {question}\n\n"
        f"SQL query: {sql_query}\n\n"
        f"Results:\n{sample}\n\n"
        f"Total rows: {row_count}"
    )

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=settings.OPENAI_MODEL_CHEAP,
        max_tokens=500,
    )
    return parse_json(result)
