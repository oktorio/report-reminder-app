from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Schedule(db.Model):
    __tablename__ = "schedules"
    id = db.Column(db.Integer, primary_key=True)
    entity_name = db.Column(db.String(200), nullable=False)    # e.g., Bank Neo Commerce
    report_name = db.Column(db.String(200), nullable=False)    # e.g., LBU, APU PPT
    description = db.Column(db.Text, nullable=True)

    # Recurrence
    anchor_due_date = db.Column(db.Date, nullable=False)       # first due date
    interval_months = db.Column(db.Integer, nullable=False, default=0)  # 0 = one-off; 1=monthly; 3=quarterly; 12=yearly; etc.

    # Recipients
    recipient_emails = db.Column(db.Text, nullable=False)      # comma-separated
    cc_emails = db.Column(db.Text, nullable=True)              # comma-separated

    # Custom reminder offsets (days before due date). If empty, uses global default.
    reminder_offsets_days = db.Column(db.String(100), nullable=True)    # e.g., "7,3,1,0"

    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ReminderLog(db.Model):
    __tablename__ = "reminder_logs"
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    planned_due_date = db.Column(db.Date, nullable=False)          # the due date for which reminder was sent
    reminder_offset_days = db.Column(db.Integer, nullable=False)   # e.g., 7,3,1,0
    status = db.Column(db.String(50), nullable=False)              # SENT / FAILED
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    backfilled = db.Column(db.Boolean, nullable=False, default=False)
    retry_count = db.Column(db.Integer, nullable=False, default=0)

    schedule = db.relationship("Schedule", backref="reminders")
