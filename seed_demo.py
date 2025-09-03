from app import app
from models import db, Schedule
from datetime import date

with app.app_context():
    db.drop_all()
    db.create_all()

    demo = [
        {
            "entity_name": "Bank Contoh A",
            "report_name": "LBU Bulanan",
            "description": "Laporan Bulanan Bank Umum sesuai ketentuan.",
            "anchor_due_date": date(2025, 9, 30),
            "interval_months": 1,
            "recipient_emails": "picA@bank.co.id, compliance@bank.co.id",
            "cc_emails": "pengawas@ojk.go.id",
            "reminder_offsets_days": "7,3,1,0",
            "active": True
        },
        {
            "entity_name": "Bank Contoh B",
            "report_name": "APU PPT Triwulanan",
            "description": "Laporan penerapan APU dan PPT triwulanan.",
            "anchor_due_date": date(2025, 10, 15),
            "interval_months": 3,
            "recipient_emails": "picB@bank.co.id",
            "cc_emails": "",
            "reminder_offsets_days": "",
            "active": True
        },
        {
            "entity_name": "P2P Contoh C",
            "report_name": "RBB Tahunan",
            "description": "Rencana Bisnis Tahunan entitas P2P.",
            "anchor_due_date": date(2025, 12, 31),
            "interval_months": 12,
            "recipient_emails": "ops@p2p.co.id",
            "cc_emails": "supervisor@ojk.go.id",
            "reminder_offsets_days": "30,14,7,3,1,0",
            "active": True
        }
    ]

    for d in demo:
        s = Schedule(**d)
        db.session.add(s)
    db.session.commit()
    print("Seeded demo data.")
