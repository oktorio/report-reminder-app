import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from config import Config
import logging

def send_email(
    to_emails: List[str],
    cc_emails: List[str],
    subject: str,
    html_body: str,
    text_body: str = None,
    bcc_emails: List[str] | None = None,
):
    if Config.EMAIL_DRY_RUN or not Config.SMTP_HOST:
        logging.info(
            "[DRY RUN] Would send email to=%s cc=%s bcc=%s subject=%s",
            to_emails,
            cc_emails,
            bcc_emails,
            subject,
        )
        logging.debug("Body (HTML):\n%s", html_body)
        return True, None

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{Config.SENDER_NAME} <{Config.SENDER_EMAIL}>"
    msg["To"] = ", ".join(to_emails) if to_emails else Config.SENDER_EMAIL
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
    # Do not add Bcc header to avoid exposing recipients

    part1 = MIMEText(text_body or "", "plain")
    part2 = MIMEText(html_body, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        if Config.SMTP_USE_TLS:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        else:
            server = smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT)
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)

        all_rcpts = to_emails + (cc_emails or []) + (bcc_emails or [])
        server.sendmail(Config.SENDER_EMAIL, all_rcpts, msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)
