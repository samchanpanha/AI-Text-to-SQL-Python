import time
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import engine
from config.app import Settings


settings = Settings()


def execute_sql(sql_query: str) -> dict:
    """Execute a SQL query safely and return results."""
    start = time.time()
    results = []
    columns = []
    row_count = 0
    error = None

    try:
        with engine.connect() as conn:
            # Set MySQL execution timeout
            conn.execute(text(f"SET max_execution_time={settings.QUERY_TIMEOUT_SECONDS * 1000}"))

            # Enforce LIMIT if not present
            query_upper = sql_query.strip().upper()
            if "LIMIT" not in query_upper:
                sql_query = sql_query.rstrip(";") + f" LIMIT {settings.QUERY_MAX_ROWS}"

            result = conn.execute(text(sql_query))
            columns = list(result.keys())
            rows = result.fetchall()
            row_count = len(rows)

            for row in rows:
                results.append(dict(zip(columns, row)))

    except SQLAlchemyError as e:
        error = str(e)

    elapsed = int((time.time() - start) * 1000)

    return {
        "success": error is None,
        "columns": columns,
        "results": results,
        "row_count": row_count,
        "execution_time_ms": elapsed,
        "error": error,
    }
