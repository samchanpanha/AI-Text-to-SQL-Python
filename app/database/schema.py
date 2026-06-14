from sqlalchemy import inspect
from app.database.connection import engine


def get_table_schemas():
    """Introspect MySQL and return all table schemas as a dict."""
    inspector = inspect(engine)
    schemas = {}

    for table_name in inspector.get_table_names():
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default", "")),
                "primary_key": col.get("primary_key", False),
            })

        foreign_keys = []
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys.append({
                "column": fk["constrained_columns"],
                "references": f"{fk['referred_table']}.{fk['referred_columns']}",
            })

        schemas[table_name] = {
            "columns": columns,
            "foreign_keys": foreign_keys,
            "row_count": _get_row_count(table_name),
        }

    return schemas


def _get_row_count(table_name: str):
    try:
        with engine.connect() as conn:
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            return result.scalar()
    except Exception:
        return 0


def format_schema_for_prompt(schemas: dict) -> str:
    """Format schema dict into a readable prompt string for the LLM."""
    lines = []
    for table_name, info in schemas.items():
        lines.append(f"Table: {table_name} ({info['row_count']} rows)")
        for col in info["columns"]:
            pk = " PK" if col["primary_key"] else ""
            lines.append(f"  - {col['name']} ({col['type']}){pk}")
        for fk in info["foreign_keys"]:
            lines.append(f"  - FK: {fk['column']} → {fk['references']}")
        lines.append("")
    return "\n".join(lines)
