from app.utils.helpers import call_llm, format_results_for_prompt
from config.app import Settings


settings = Settings()

SYSTEM_PROMPT = open("app/prompts/respond.txt").read()


def generate_response(question: str, sql_query: str, results: list[dict], row_count: int) -> str:
    """Format query results into a natural language answer."""
    sample = format_results_for_prompt(results, max_rows=15)
    user_prompt = (
        f"Question: {question}\n\n"
        f"SQL query: {sql_query}\n\n"
        f"Results:\n{sample}\n\n"
        f"Total rows: {row_count}"
    )

    return call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=settings.OPENAI_MODEL_CHEAP,
        max_tokens=800,
    )
