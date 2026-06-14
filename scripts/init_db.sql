-- This file is used by Docker to initialize the MySQL database.
-- Application tables are created by SQLAlchemy at startup.

CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL,
    stock_qty INT DEFAULT 0,
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total FLOAT DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    qty INT NOT NULL,
    unit_price FLOAT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    enabled BOOLEAN DEFAULT TRUE,
    max_retries INT DEFAULT 0,
    retry_delay_minutes INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report_definitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    sql_query TEXT NOT NULL,
    format VARCHAR(10) DEFAULT 'xlsx',
    sheet_name VARCHAR(255) DEFAULT 'Sheet1',
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS delivery_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    type VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS email_deliveries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_config_id INT NOT NULL UNIQUE,
    to_recipients TEXT NOT NULL,
    cc_recipients TEXT,
    bcc_recipients TEXT,
    subject_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    attachment_type VARCHAR(20) DEFAULT 'individual',
    FOREIGN KEY (delivery_config_id) REFERENCES delivery_configs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS telegram_deliveries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_config_id INT NOT NULL UNIQUE,
    chat_id VARCHAR(100) NOT NULL,
    bot_token VARCHAR(255) NOT NULL,
    message_template TEXT,
    FOREIGN KEY (delivery_config_id) REFERENCES delivery_configs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS task_execution_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    files_generated JSON,
    delivery_results JSON,
    rows_processed INT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level INT DEFAULT 20,
    logger_name VARCHAR(255) DEFAULT '',
    message TEXT,
    module VARCHAR(100) DEFAULT '',
    function VARCHAR(100) DEFAULT '',
    line_no INT DEFAULT 0,
    request_id VARCHAR(50) DEFAULT '',
    user_ip VARCHAR(50) DEFAULT '',
    method VARCHAR(10) DEFAULT '',
    path VARCHAR(500) DEFAULT '',
    status_code INT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    metadata JSON,
    INDEX idx_timestamp (timestamp),
    INDEX idx_request_id (request_id),
    INDEX idx_path (path(255)),
    INDEX idx_status_code (status_code)
);

CREATE TABLE IF NOT EXISTS llm_call_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model VARCHAR(100) DEFAULT '',
    system_prompt TEXT,
    user_prompt TEXT,
    response TEXT,
    tokens_prompt INT DEFAULT 0,
    tokens_completion INT DEFAULT 0,
    tokens_total INT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    success INT DEFAULT 1,
    error_message VARCHAR(500) DEFAULT '',
    request_id VARCHAR(50) DEFAULT '',
    INDEX idx_timestamp (timestamp),
    INDEX idx_tokens_total (tokens_total),
    INDEX idx_duration_ms (duration_ms),
    INDEX idx_request_id (request_id)
);

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    api_key VARCHAR(64) UNIQUE,
    rate_limit_per_minute INT DEFAULT 60,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
);
