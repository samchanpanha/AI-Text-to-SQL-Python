from app.utils.helpers import call_llm, parse_json
from app.database.schema import get_table_schemas, format_schema_for_prompt
from config.app import Settings


settings = Settings()

SYSTEM_PROMPT = open("app/prompts/table_select.txt").read()
_schema_cache: dict | None = None


def select_tables(question: str) -> dict:
    """Determine which tables and columns are needed for the question."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = get_table_schemas()

    schema_text = format_schema_for_prompt(_schema_cache)
    user_prompt = f"Question: {question}\n\nSchema:\n{schema_text}"

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=settings.OPENAI_MODEL_CHEAP,
        max_tokens=800,
    )
    return parse_json(result)


def get_filtered_schema(selected: dict) -> str:
    """Return only the selected tables/columns from the schema."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = get_table_schemas()

    tables = selected.get("tables", [])
    columns = selected.get("columns", [])
    lines = []

    for table_name in tables:
        if table_name in _schema_cache:
            info = _schema_cache[table_name]
            lines.append(f"Table: {table_name}")
            for col in info["columns"]:
                col_ref = f"{table_name}.{col['name']}"
                if not columns or col_ref in columns:
                    lines.append(f"  - {col['name']} ({col['type']})")
            for fk in info["foreign_keys"]:
                lines.append(f"  - FK: {fk['column']} → {fk['references']}")
            lines.append("")

    return "\n".join(lines) if lines else format_schema_for_prompt(_schema_cache)
