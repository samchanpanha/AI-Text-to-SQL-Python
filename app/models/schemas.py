from datetime import datetime
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    answer: str
    sql_query: str | None = None
    row_count: int | None = None
    execution_time_ms: int | None = None


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    cron_expression: str
    timezone: str = "UTC"
    enabled: bool = True
    max_retries: int = 0
    retry_delay_minutes: int = 5


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    enabled: bool | None = None
    max_retries: int | None = None
    retry_delay_minutes: int | None = None


class TaskResponse(BaseModel):
    id: int
    name: str
    description: str | None
    cron_expression: str
    timezone: str
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportDefinitionCreate(BaseModel):
    name: str
    sql_query: str
    format: str = "xlsx"
    sheet_name: str = "Sheet1"
    sort_order: int = 0


class ReportDefinitionResponse(BaseModel):
    id: int
    task_id: int
    name: str
    sql_query: str
    format: str
    sheet_name: str
    sort_order: int

    model_config = {"from_attributes": True}


class DeliveryConfigCreate(BaseModel):
    type: str
    name: str | None = None
    enabled: bool = True


class EmailDeliveryCreate(BaseModel):
    to_recipients: str
    cc_recipients: str = ""
    bcc_recipients: str = ""
    subject_template: str
    body_template: str
    attachment_type: str = "individual"


class TelegramDeliveryCreate(BaseModel):
    chat_id: str
    bot_token: str
    message_template: str | None = None


class TaskExecuteResponse(BaseModel):
    task_id: int
    status: str
    started_at: datetime
    log_id: int | None = None
