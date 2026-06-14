export interface QueryRequest {
  question: string
}

export interface QueryResponse {
  answer: string
  sql_query: string | null
  row_count: number | null
  execution_time_ms: number | null
}

export interface TaskCreate {
  name: string
  description?: string
  cron_expression: string
  timezone?: string
  enabled?: boolean
  max_retries?: number
  retry_delay_minutes?: number
}

export interface TaskUpdate {
  name?: string
  description?: string
  cron_expression?: string
  timezone?: string
  enabled?: boolean
  max_retries?: number
  retry_delay_minutes?: number
}

export interface TaskResponse {
  id: number
  name: string
  description: string | null
  cron_expression: string
  timezone: string
  enabled: boolean
  created_at: string
}

export interface ReportDefinitionCreate {
  name: string
  sql_query: string
  format?: string
  sheet_name?: string
  sort_order?: number
}

export interface ReportDefinitionResponse {
  id: number
  task_id: number
  name: string
  sql_query: string
  format: string
  sheet_name: string
  sort_order: number
}

export interface DeliveryConfigCreate {
  type: 'email' | 'telegram'
  name?: string
  enabled?: boolean
}

export interface EmailDeliveryCreate {
  to_recipients: string
  cc_recipients?: string
  bcc_recipients?: string
  subject_template: string
  body_template: string
  attachment_type?: string
}

export interface TelegramDeliveryCreate {
  chat_id: string
  bot_token: string
  message_template?: string
}

export interface TaskExecuteResponse {
  task_id: number
  status: string
  started_at: string
  log_id: number | null
}

export interface DashboardStats {
  period_days: number
  users: { total: number; active: number }
  tasks: { total: number; active: number; reports_defined: number }
  api: { requests: number; errors_5xx: number; avg_duration_ms: number }
  llm: { total_calls: number; total_tokens: number }
  scheduler: { task_executions: number; failed_executions: number }
}

export interface AuditLog {
  id: number
  timestamp: string
  level: number
  message: string
  module: string
  request_id: string
  method: string
  path: string
  status_code: number
  duration_ms: number
  user_ip: string
}

export interface LlmCallLog {
  id: number
  timestamp: string
  model: string
  tokens_prompt: number
  tokens_completion: number
  tokens_total: number
  duration_ms: number
  success: boolean
  error_message: string | null
  request_id: string
}

export interface AuditStats {
  period_days: number
  total_requests: number
  errors_5xx: number
  warnings_4xx: number
  avg_duration_ms: number
  top_paths: { path: string; count: number }[]
}

export interface LlmStats {
  period_days: number
  total_calls: number
  failed_calls: number
  total_estimated_cost_usd: number
  models: {
    model: string
    calls: number
    total_prompt_tokens: number
    total_completion_tokens: number
    total_tokens: number
    avg_duration_ms: number
    total_duration_ms: number
    estimated_cost_usd: number
  }[]
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  per_page: number
  total_pages: number
  logs: T[]
}

export interface N8nTask {
  id: number
  name: string
  description: string
  cron_expression: string
  enabled: boolean
  report_count: number
}

export interface SystemInfo {
  app: {
    name: string
    version: string
    environment: string
    debug: boolean
    uptime_seconds: number
  }
  database: {
    host: string
    database: string
    pool_size: number
    max_overflow: number
  }
  llm: {
    model: string
    cheap_model: string
    max_tokens: number
    configured: boolean
  }
  scheduler: { enabled: boolean }
  security: {
    allowed_hosts: string[]
    cors_origins: string[]
    rate_limit_per_minute: number
    query_timeout_seconds: number
    query_max_rows: number
  }
  logging: {
    level: string
    format: string
    output: string
    db_retention_days: number
  }
}
