import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///data.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Timezone
    APP_TZ = os.getenv("APP_TZ", "Asia/Jakarta")

    # SMTP
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SENDER_NAME = os.getenv("SENDER_NAME", "Reminder Bot")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")

    EMAIL_DRY_RUN = os.getenv("EMAIL_DRY_RUN", "true").lower() == "true"

    # Reminders
    DEFAULT_REMINDER_OFFSETS = [int(x.strip()) for x in os.getenv("DEFAULT_REMINDER_OFFSETS", "7,3,1,0").split(",") if x.strip()]
    DAILY_JOB_HOUR = int(os.getenv("DAILY_JOB_HOUR", "8"))
    DAILY_JOB_MINUTE = int(os.getenv("DAILY_JOB_MINUTE", "0"))
