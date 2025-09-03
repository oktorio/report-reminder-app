# Reminder Laporan Rutin (Python + Flask)

A lightweight web app untuk regulator/pengawas mengelola **jadwal laporan rutin** (bank, P2P, dll.) dan mengirim **email reminder otomatis** pada H-7/H-3/H-1/H.

## ✨ Fitur Utama
- Input & kelola **schedule**: entitas, nama laporan, anchor due date, interval (bulan), email penerima, CC, offsets H-.
- **Reminder otomatis** via SMTP (Gmail/Outlook/SMTP lain). Mendukung mode **DRY RUN** (tidak benar-benar mengirim).
- **Deduping**: tidak mengirim reminder yang sama dua kali untuk due yang sama di hari yang sama.
- **Dashboard**: lihat upcoming due & recent logs.
- **APScheduler**: job harian pada jam yang bisa diatur (default 08:00 Asia/Jakarta).

## 🧱 Arsitektur Singkat
- **Flask** untuk UI (CRUD schedules, dashboard, logs).
- **SQLite** (default) via SQLAlchemy.
- **APScheduler** untuk job harian `scan_and_send_reminders()`.
- **SMTP** (smtplib) untuk kirim email (Gmail/Outlook/O365).

## 📦 Setup Cepat
1. **Clone / Download** repo ini.
2. Buat virtualenv dan install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```
3. Salin `.env.example` menjadi `.env`, lalu isi kredensial SMTP (atau biarkan `EMAIL_DRY_RUN=true` untuk uji coba).
4. (Opsional) Seed data demo:
   ```bash
   python seed_demo.py
   ```
5. Jalankan aplikasi:
   ```bash
   python app.py
   ```
   Buka `http://127.0.0.1:5000`.

## ⚙️ Konfigurasi `.env`
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your.email@domain.com
SMTP_PASSWORD=your_app_password_or_password
SMTP_USE_TLS=true
SENDER_NAME=OJK Supervisor
SENDER_EMAIL=your.email@domain.com

EMAIL_DRY_RUN=true

FLASK_SECRET_KEY=change-this-secret
DATABASE_URL=sqlite:///data.db
APP_TZ=Asia/Jakarta

DEFAULT_REMINDER_OFFSETS=7,3,1,0

DAILY_JOB_HOUR=8
DAILY_JOB_MINUTE=0
```

> **Gmail**: gunakan **App Password** jika 2FA aktif. SMTP: `smtp.gmail.com:587 (TLS)`  
> **Outlook/Office365**: `smtp.office365.com:587 (TLS)`.

## 🗓️ Cara Kerja Recurrence
- `anchor_due_date` = tanggal jatuh tempo pertama.
- `interval_months` = 0 (sekali), 1 (bulanan), 3 (triwulanan), 12 (tahunan), dst.
- Sistem menghitung **next due** berdasarkan `anchor_due_date` dan `interval_months`.

## 🔔 Mekanisme Reminder
- Setiap hari pada jam terkonfigurasi (default 08:00, Asia/Jakarta), job akan:
  - Hitung due yang relevan.
  - Cek apakah **hari ini** sama dengan `due - offset` (mis. `H-7`).
  - Cek ke **ReminderLog** apakah sudah dikirim hari ini untuk kombinasi `(schedule, due, offset)` → **hindari duplikat**.
  - Kirim email (atau log saja jika DRY RUN).
- Subjek email: `[Reminder H-x] <Laporan> - <Entitas> (Due DD MMM YYYY)`

## 🧪 Uji Coba Tanpa Kirim Email
- Biarkan `EMAIL_DRY_RUN=true` di `.env`.
- Seed demo (`python seed_demo.py`) lalu `python app.py`. Dashboard akan menampilkan schedule & recent logs (ketika job jalan).

## 🧩 Penyesuaian Cepat
- **Offsets per schedule**: isi `Offsets (H-)` di form (mis. `30,14,7,3,1,0`). Kosongkan untuk pakai default `.env`.
- **Jam Job Harian**: ubah `DAILY_JOB_HOUR` & `DAILY_JOB_MINUTE` di `.env`.
- **Notifikasi lain** (Telegram/WhatsApp): tambahkan modul sender baru mirip `mailer.py` dan panggil di `scan_and_send_reminders()`.

## 🔐 Keamanan
- Simpan kredensial di `.env` (jangan commit).
- Gunakan App Password bila perlu.
- Batasi akses app di jaringan internal/VPN OJK.

## 📁 Struktur Folder
```
report-reminder-app/
├─ app.py
├─ config.py
├─ models.py
├─ scheduler.py
├─ mailer.py
├─ utils.py
├─ templates/
│  ├─ base.html
│  ├─ index.html
│  ├─ schedules.html
│  └─ schedule_form.html
├─ seed_demo.py
├─ requirements.txt
├─ .env.example
└─ README.md
```

## 🛠️ Roadmap Fitur Lanjutan
- Escalation H+ (escalate ke manajemen bila lewat due).
- Attachment template, auto-generate surat pengantar.
- Role & multi-user.
- Import/Export Excel untuk bulk schedules.
- Integrasi kalender (Google/Outlook ICS feed).
- API endpoint untuk integrasi dengan sistem pengawasan lain.

---

Dibuat untuk kebutuhan regulator/pengawas. Saran perbaikan selalu welcome.
