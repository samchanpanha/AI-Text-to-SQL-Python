from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_auth
from app.models.schemas import QueryRequest, QueryResponse
from app.agents.triage import triage_question
from app.agents.table_selector import select_tables, get_filtered_schema
from app.agents.sql_generator import generate_sql, fix_sql
from app.agents.sql_executor import execute_sql
from app.agents.validator import validate_results
from app.agents.responder import generate_response


router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest, _=Depends(require_auth)):
    """Main text-to-SQL endpoint: question in → answer out."""

    # Step 1: Triage
    classification = triage_question(req.question)
    category = classification.get("category", "general")

    if category == "out_of_scope":
        raise HTTPException(
            status_code=400,
            detail=f"I cannot answer that question. {classification.get('reason', '')}",
        )

    if category == "general":
        return QueryResponse(
            answer="I'm a data analysis assistant. I can help you query the database. "
                   "Try asking about sales, customers, products, or orders.",
        )

    # Step 2: Select tables
    selected = select_tables(req.question)
    filtered_schema = get_filtered_schema(selected)

    # Step 3: Generate SQL
    sql_query, explanation = generate_sql(req.question, filtered_schema, str(selected.get("tables", [])))

    if not sql_query:
        return QueryResponse(
            answer="I couldn't generate a SQL query for that question. Could you rephrase it?",
        )

    # Step 4: Execute SQL (with retry)
    result = execute_sql(sql_query)

    if not result["success"] and result["error"]:
        # Retry with error feedback
        from app.database.schema import format_schema_for_prompt, get_table_schemas
        schema_text = format_schema_for_prompt(get_table_schemas())
        fixed_sql, _ = fix_sql(sql_query, result["error"], req.question, schema_text)

        if fixed_sql:
            result = execute_sql(fixed_sql)
            if result["success"]:
                sql_query = fixed_sql

    if not result["success"]:
        return QueryResponse(
            answer=f"I ran into a database issue: {result['error']}",
            sql_query=sql_query,
        )

    # Step 5: Validate results
    validation = validate_results(req.question, sql_query, result["results"], result["row_count"])

    if not validation.get("answers_question", True):
        return QueryResponse(
            answer=f"I found data but I'm not sure it fully answers your question. "
                   f"{validation.get('reason', '')}\n\n"
                   f"Here's what I found:\n{generate_response(req.question, sql_query, result['results'], result['row_count'])}",
            sql_query=sql_query,
            row_count=result["row_count"],
            execution_time_ms=result["execution_time_ms"],
        )

    # Step 6: Generate response
    answer = generate_response(req.question, sql_query, result["results"], result["row_count"])

    return QueryResponse(
        answer=answer,
        sql_query=sql_query,
        row_count=result["row_count"],
        execution_time_ms=result["execution_time_ms"],
    )
