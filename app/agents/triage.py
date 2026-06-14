from app.utils.helpers import call_llm, parse_json
from config.app import Settings


settings = Settings()

SYSTEM_PROMPT = open("app/prompts/triage.txt").read()


def triage_question(question: str) -> dict:
    """Classify a user question as data, general, or out_of_scope."""
    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=question,
        model=settings.OPENAI_MODEL_CHEAP,
        max_tokens=200,
    )
    return parse_json(result)
