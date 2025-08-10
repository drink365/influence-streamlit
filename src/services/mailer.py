from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from src.config import SMTP

def send_email(to_addrs, subject, html_body, text_body=None, cc=None, bcc=None):
    if not all([SMTP["user"], SMTP["pass"], SMTP["from"]]):
        return False, "SMTP not configured"
    if isinstance(to_addrs, str): to_addrs = [to_addrs]
    if isinstance(cc, str): cc = [cc]
    if isinstance(bcc, str): bcc = [bcc]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f'{SMTP["from_name"]} <{SMTP["from"]}>'
    msg["To"] = ", ".join(to_addrs)
    if cc:  msg["Cc"] = ", ".join(cc)
    if SMTP["reply_to"]: msg["Reply-To"] = SMTP["reply_to"]

    if text_body: msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    recipients = to_addrs + (cc or []) + (bcc or [])
    try:
        if SMTP["port"] == 465:
            server = smtplib.SMTP_SSL(SMTP["host"], SMTP["port"], timeout=20)
        else:
            server = smtplib.SMTP(SMTP["host"], SMTP["port"], timeout=20)
            server.ehlo();
            try: server.starttls()
            except Exception: pass
        server.login(SMTP["user"], SMTP["pass"])
        server.sendmail(SMTP["from"], recipients, msg.as_string())
        server.quit()
        return True, "sent"
    except Exception as e:
        return False, str(e)
