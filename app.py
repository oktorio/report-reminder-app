from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import escape
from config import Config
from models import db, Schedule, ReminderLog
from scheduler import init_scheduler
from datetime import datetime, date, timedelta
from utils import parse_offsets, parse_csv_emails, next_occurrence
from mailer import send_email
import pytz

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    init_scheduler(app)
    register_routes(app)
    return app

def register_routes(app: Flask):
    @app.route("/")
    def index():
        # Show upcoming dues and counts
        tz = pytz.timezone(Config.APP_TZ)
        today = datetime.now(tz).date()
        schedules = Schedule.query.filter_by(active=True).all()
        rows = []
        for s in schedules:
            due = next_occurrence(s.anchor_due_date, s.interval_months, today)
            offsets = parse_offsets(s.reminder_offsets_days) if s.reminder_offsets_days else Config.DEFAULT_REMINDER_OFFSETS
            rows.append({
                "schedule": s,
                "next_due": due,
                "offsets": offsets,
            })
        # Recent logs
        recent_logs = ReminderLog.query.order_by(ReminderLog.sent_at.desc()).limit(50).all()
        return render_template("index.html", rows=rows, logs=recent_logs, today=today)

    @app.route("/send-today", methods=["POST"])
    def send_today():
        from scheduler import send_today_due_reminders
        send_today_due_reminders()
        flash("Reminders for today dispatched", "success")
        return redirect(url_for("index"))

    @app.route("/scan-missed", methods=["POST"])
    def scan_missed():
        from scheduler import scan_missed_reminders
        scan_missed_reminders()
        flash("Missed reminders backfilled", "success")
        return redirect(url_for("index"))

    @app.route("/schedules")
    def list_schedules():
        schedules = Schedule.query.order_by(Schedule.entity_name, Schedule.report_name).all()
        return render_template("schedules.html", schedules=schedules)

    @app.route("/schedules/new", methods=["GET", "POST"])
    def new_schedule():
        if request.method == "POST":
            form = request.form
            s = Schedule(
                entity_name=form.get("entity_name","").strip(),
                report_name=form.get("report_name","").strip(),
                description=form.get("description","").strip() or None,
                anchor_due_date=datetime.strptime(form.get("anchor_due_date"), "%Y-%m-%d").date(),
                interval_months=int(form.get("interval_months","0") or 0),
                recipient_emails=form.get("recipient_emails","").strip(),
                cc_emails=form.get("cc_emails","").strip() or None,
                reminder_offsets_days=form.get("reminder_offsets_days","").strip() or None,
                active=True if form.get("active")=="on" else False
            )
            db.session.add(s)
            db.session.commit()
            flash("Schedule created", "success")
            return redirect(url_for("list_schedules"))
        return render_template("schedule_form.html", schedule=None)

    @app.route("/schedules/<int:sid>/edit", methods=["GET", "POST"])
    def edit_schedule(sid):
        s = Schedule.query.get_or_404(sid)
        if request.method == "POST":
            form = request.form
            s.entity_name=form.get("entity_name","").strip()
            s.report_name=form.get("report_name","").strip()
            s.description=form.get("description","").strip() or None
            s.anchor_due_date=datetime.strptime(form.get("anchor_due_date"), "%Y-%m-%d").date()
            s.interval_months=int(form.get("interval_months","0") or 0)
            s.recipient_emails=form.get("recipient_emails","").strip()
            s.cc_emails=form.get("cc_emails","").strip() or None
            s.reminder_offsets_days=form.get("reminder_offsets_days","").strip() or None
            s.active=True if form.get("active")=="on" else False
            db.session.commit()
            flash("Schedule updated", "success")
            return redirect(url_for("list_schedules"))
        return render_template("schedule_form.html", schedule=s)

    @app.route("/schedules/<int:sid>/delete", methods=["POST"])
    def delete_schedule(sid):
        s = Schedule.query.get_or_404(sid)
        db.session.delete(s)
        db.session.commit()
        flash("Schedule deleted", "info")
        return redirect(url_for("list_schedules"))

    @app.route("/logs")
    def view_logs():
        logs = ReminderLog.query.order_by(ReminderLog.sent_at.desc()).limit(200).all()
        return render_template("logs.html", logs=logs)

    @app.route("/test-email", methods=["GET", "POST"])
    def test_email():
        if request.method == "POST":
            to_list = parse_csv_emails(request.form.get("to", ""))
            subject = escape(request.form.get("subject", "").strip())
            body = escape(request.form.get("body", "").strip())
            if not to_list:
                flash("Field 'To' is required", "danger")
            else:
                ok, err = send_email([], [], subject, body, body, bcc_emails=to_list)
                if ok:
                    flash("Email terkirim", "success")
                else:
                    flash(f"Gagal mengirim email: {err}", "danger")
        return render_template("test_email.html")

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
