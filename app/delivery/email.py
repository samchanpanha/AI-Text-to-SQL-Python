import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders

from jinja2 import Template

from config.app import Settings


settings = Settings()


def send_email_report(
    to: list[str],
    subject_template: str,
    body_template: str,
    files: list[dict],
    task,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
):
    """Send an email with report files attached using Jinja2 templates."""
    context = {
        "task_name": task.name,
        "task_description": task.description,
        "date": formatdate(localtime=True),
        "report_count": len(files),
        "file_names": [f.get("name", "report") for f in files],
    }

    subject = Template(subject_template).render(**context)
    body = Template(body_template).render(**context)

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_DEFAULT_FROM
    msg["To"] = ", ".join(to)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = ", ".join(cc)

    msg.attach(MIMEText(body, "html" if "<html" in body else "plain"))

    for f in files:
        path = f.get("path")
        name = f.get("name", "report")
        if path and os.path.exists(path):
            with open(path, "rb") as fp:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(fp.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=\"{name}\"",
                )
                msg.attach(part)

    all_recipients = to + (cc or []) + (bcc or [])

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_DEFAULT_FROM, all_recipients, msg.as_string())
