from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, timedelta
import pytz
from flask import current_app
from config import Config
from models import db, Schedule, ReminderLog
from utils import (
    parse_csv_emails,
    parse_offsets,
    next_occurrence,
    should_send_for_due,
    generate_upcoming_occurrences,
)
from mailer import send_email

def build_email_content(schedule: Schedule, due_date: date, offset_days: int):
    h_text = f"H-{offset_days}" if offset_days > 0 else ("HARI H" if offset_days == 0 else f"H+{abs(offset_days)}")
    subject = f"[Reminder {h_text}] {schedule.report_name} - {schedule.entity_name} (Due {due_date:%d %b %Y})"
    html = f"""
    <p>Yth. PIC <b>{schedule.entity_name}</b>,</p>
    <p>Ini adalah pengingat <b>{h_text}</b> untuk penyampaian laporan <b>{schedule.report_name}</b>.</p>
    <ul>
      <li><b>Entitas</b>: {schedule.entity_name}</li>
      <li><b>Laporan</b>: {schedule.report_name}</li>
      <li><b>Jatuh tempo</b>: {due_date:%A, %d %B %Y}</li>
    </ul>
    <p>{schedule.description or ''}</p>
    <p>Mohon tindak lanjut sesuai ketentuan. Terima kasih.</p>
    <hr>
    <p><i>Pesan ini dikirim otomatis oleh sistem reminder.</i></p>
    """
    text = f"""Reminder {h_text} untuk {schedule.report_name} - {schedule.entity_name}
Jatuh tempo: {due_date:%A, %d %B %Y}
{schedule.description or ''}
Pesan ini dikirim otomatis oleh sistem reminder.
"""
    return subject, html, text

def _get_offsets(schedule: Schedule):
    custom = parse_offsets(schedule.reminder_offsets_days) if schedule.reminder_offsets_days else None
    from config import Config
    return custom or Config.DEFAULT_REMINDER_OFFSETS


def scan_missed_reminders(days: int | None = None):
    """Backfill reminders that should have been sent in the past N days."""
    tz = pytz.timezone(Config.APP_TZ)
    today = datetime.now(tz).date()
    lookback = days or getattr(Config, "MISSED_SCAN_DAYS", 7)
    window_start = today - timedelta(days=lookback)

    with current_app.app_context():
        schedules = Schedule.query.filter_by(active=True).all()
        for sch in schedules:
            offsets = _get_offsets(sch)
            if not offsets:
                continue
            max_off = max(offsets)
            due_start = window_start
            due_end = today + timedelta(days=max_off)
            dues = generate_upcoming_occurrences(
                sch.anchor_due_date, sch.interval_months, due_start, due_end
            )
            for due in dues:
                for off in offsets:
                    send_day = due - timedelta(days=off)
                    if send_day < window_start or send_day > today:
                        continue
                    exists = ReminderLog.query.filter_by(
                        schedule_id=sch.id,
                        planned_due_date=due,
                        reminder_offset_days=off,
                        status="SENT",
                    ).first()
                    if exists:
                        continue

                    to_emails = parse_csv_emails(sch.recipient_emails)
                    cc_emails = parse_csv_emails(sch.cc_emails or "")
                    subject, html, text = build_email_content(sch, due, off)
                    ok, err = send_email(to_emails, cc_emails, subject, html, text)

                    log = ReminderLog(
                        schedule_id=sch.id,
                        planned_due_date=due,
                        reminder_offset_days=off,
                        status="SENT" if ok else "FAILED",
                        error_message=None if ok else str(err),
                        backfilled=True,
                        retry_count=0,
                    )
                    db.session.add(log)
                    db.session.commit()

def scan_and_send_reminders():
    tz = pytz.timezone(Config.APP_TZ)
    today = datetime.now(tz).date()

    with current_app.app_context():
        schedules = Schedule.query.filter_by(active=True).all()
        for sch in schedules:
            offsets = _get_offsets(sch)
            # Determine the relevant due date for which today could match any offset:
            # We need to check the 'current' or 'next' due date and maybe a few future ones.
            # Strategy: start from the next occurrence >= (today), but also check if today matches offsets for that due and possibly the immediate next due.
            # Also check if today matches offsets for a past due if offset was negative (e.g., escalation H+1). For MVP, we only consider non-negative offsets.
            due = next_occurrence(sch.anchor_due_date, sch.interval_months, today)
            candidate_dues = set()
            if due:
                candidate_dues.add(due)
            # Also consider previous occurrence in case today is H-0 for a due that equals today (already included), or H-1 for due==tomorrow is handled above.
            # Compute previous by subtracting interval once
            if sch.interval_months > 0:
                prev = sch.anchor_due_date
                while True:
                    nxt = prev  # keep track
                    nextc = prev
                    # we will move forward until nextc >= due (or today)
                    if prev >= today:
                        break
                    # advance
                    adv = nextc
                    from dateutil.relativedelta import relativedelta
                    adv = prev + relativedelta(months=sch.interval_months)
                    if adv >= today:
                        # prev is the previous occurrence before today
                        candidate_dues.add(adv)  # also check adv itself (next due)
                        candidate_dues.add(prev) # previous due in case of H+ escalation
                        break
                    prev = adv

            for d in list(candidate_dues):
                matches = should_send_for_due(d, today, offsets)
                for off in matches:
                    # Dedup: has a SENT log today for this schedule/due/off?
                    exists = ReminderLog.query.filter_by(
                        schedule_id=sch.id,
                        planned_due_date=d,
                        reminder_offset_days=off,
                        status="SENT",
                    ).filter(ReminderLog.sent_at >= datetime.combine(today, datetime.min.time())).first()
                    if exists:
                        continue

                    to_emails = parse_csv_emails(sch.recipient_emails)
                    cc_emails = parse_csv_emails(sch.cc_emails or "")
                    subject, html, text = build_email_content(sch, d, off)
                    ok, err = send_email(to_emails, cc_emails, subject, html, text)

                    log = ReminderLog(
                        schedule_id=sch.id,
                        planned_due_date=d,
                        reminder_offset_days=off,
                        status="SENT" if ok else "FAILED",
                        error_message=None if ok else str(err),
                        retry_count=0,
                    )
                    db.session.add(log)
                    db.session.commit()

        # Retry failed reminders with exponential backoff
        now = datetime.utcnow()
        failed_logs = ReminderLog.query.filter_by(status="FAILED").all()
        for log in failed_logs:
            if log.retry_count >= Config.MAX_RETRY_ATTEMPTS:
                continue
            delay = Config.RETRY_BACKOFF_BASE_MINUTES * (2 ** log.retry_count)
            if log.sent_at + timedelta(minutes=delay) > now:
                continue

            sch = log.schedule
            to_emails = parse_csv_emails(sch.recipient_emails)
            cc_emails = parse_csv_emails(sch.cc_emails or "")
            subject, html, text = build_email_content(
                sch, log.planned_due_date, log.reminder_offset_days
            )
            ok, err = send_email(to_emails, cc_emails, subject, html, text)

            log.retry_count += 1
            log.sent_at = datetime.utcnow()
            if ok:
                log.status = "SENT"
                log.error_message = None
            else:
                log.error_message = str(err)
            db.session.commit()

def send_today_due_reminders():
    """Send H reminders for schedules whose due date is today."""
    tz = pytz.timezone(Config.APP_TZ)
    today = datetime.now(tz).date()

    with current_app.app_context():
        schedules = Schedule.query.filter_by(active=True).all()
        for sch in schedules:
            due = next_occurrence(sch.anchor_due_date, sch.interval_months, today)
            if due != today:
                continue

            # Skip if already logged today
            exists = (
                ReminderLog.query.filter_by(
                    schedule_id=sch.id,
                    planned_due_date=due,
                    reminder_offset_days=0,
                    status="SENT",
                )
                .filter(
                    ReminderLog.sent_at
                    >= datetime.combine(today, datetime.min.time())
                )
                .first()
            )
            if exists:
                continue

            to_emails = parse_csv_emails(sch.recipient_emails)
            cc_emails = parse_csv_emails(sch.cc_emails or "")
            subject, html, text = build_email_content(sch, due, 0)
            ok, err = send_email(to_emails, cc_emails, subject, html, text)

            log = ReminderLog(
                schedule_id=sch.id,
                planned_due_date=due,
                reminder_offset_days=0,
                status="SENT" if ok else "FAILED",
                error_message=None if ok else str(err),
                retry_count=0,
            )
            db.session.add(log)
            db.session.commit()

def init_scheduler(app):
    scheduler = BackgroundScheduler(timezone=Config.APP_TZ)
    # Daily job at configured hour/minute
    trigger = CronTrigger(hour=Config.DAILY_JOB_HOUR, minute=Config.DAILY_JOB_MINUTE)
    scheduler.add_job(scan_and_send_reminders, trigger, id="daily_reminders", replace_existing=True)
    scheduler.start()
    # Also run once at startup (useful for dev/demo)
    with app.app_context():
        try:
            scan_and_send_reminders()
            scan_missed_reminders()
        except Exception as e:
            app.logger.warning(f"Initial scan failed: {e}")
    # Just log immediately that scheduler is running
    app.logger.info("Scheduler is running (daily at %02d:%02d %s).",
                    Config.DAILY_JOB_HOUR, Config.DAILY_JOB_MINUTE, Config.APP_TZ)

