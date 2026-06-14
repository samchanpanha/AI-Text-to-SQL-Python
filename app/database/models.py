from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from app.database.connection import Base


# ── E-Commerce Schema ──

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    city = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    stock_qty = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"))

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    total = Column(Float, default=0.0)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# ── Scheduler Schema ──

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")
    enabled = Column(Boolean, default=True)
    max_retries = Column(Integer, default=0)
    retry_delay_minutes = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reports = relationship("ReportDefinition", back_populates="task", cascade="all, delete-orphan")
    deliveries = relationship("DeliveryConfig", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("TaskExecutionLog", back_populates="task", cascade="all, delete-orphan")


class ReportDefinition(Base):
    __tablename__ = "report_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False)
    name = Column(String(255), nullable=False)
    sql_query = Column(Text, nullable=False)
    format = Column(String(10), default="xlsx")
    sheet_name = Column(String(255), default="Sheet1")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("ScheduledTask", back_populates="reports")


class DeliveryConfig(Base):
    __tablename__ = "delivery_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False)
    type = Column(String(20), nullable=False)
    name = Column(String(255))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("ScheduledTask", back_populates="deliveries")
    email_config = relationship("EmailDelivery", back_populates="delivery", uselist=False, cascade="all, delete-orphan")
    telegram_config = relationship("TelegramDelivery", back_populates="delivery", uselist=False, cascade="all, delete-orphan")


class EmailDelivery(Base):
    __tablename__ = "email_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_config_id = Column(Integer, ForeignKey("delivery_configs.id"), unique=True, nullable=False)
    to_recipients = Column(Text, nullable=False)
    cc_recipients = Column(Text, default="")
    bcc_recipients = Column(Text, default="")
    subject_template = Column(Text, nullable=False)
    body_template = Column(Text, nullable=False)
    attachment_type = Column(String(20), default="individual")

    delivery = relationship("DeliveryConfig", back_populates="email_config")


class TelegramDelivery(Base):
    __tablename__ = "telegram_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_config_id = Column(Integer, ForeignKey("delivery_configs.id"), unique=True, nullable=False)
    chat_id = Column(String(100), nullable=False)
    bot_token = Column(String(255), nullable=False)
    message_template = Column(Text)

    delivery = relationship("DeliveryConfig", back_populates="telegram_config")


class TaskExecutionLog(Base):
    __tablename__ = "task_execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    files_generated = Column(JSON)
    delivery_results = Column(JSON)
    rows_processed = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)

    task = relationship("ScheduledTask", back_populates="logs")


# ── Audit & LLM Call Logs ──

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(Integer, default=20)
    logger_name = Column(String(255), default="")
    message = Column(Text, default="")
    module = Column(String(100), default="")
    function = Column(String(100), default="")
    line_no = Column(Integer, default=0)
    request_id = Column(String(50), default="", index=True)
    user_ip = Column(String(50), default="")
    method = Column(String(10), default="")
    path = Column(String(500), default="", index=True)
    status_code = Column(Integer, default=0, index=True)
    duration_ms = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)


class LlmCallLog(Base):
    __tablename__ = "llm_call_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    model = Column(String(100), default="")
    system_prompt = Column(Text, default="")
    user_prompt = Column(Text, default="")
    response = Column(Text, default="")
    tokens_prompt = Column(Integer, default=0)
    tokens_completion = Column(Integer, default=0)
    tokens_total = Column(Integer, default=0, index=True)
    duration_ms = Column(Integer, default=0, index=True)
    success = Column(Integer, default=1)
    error_message = Column(String(500), default="")
    request_id = Column(String(50), default="", index=True)


# ── Users / Auth ──

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, default=True)
    api_key = Column(String(64), unique=True, nullable=True)
    rate_limit_per_minute = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
