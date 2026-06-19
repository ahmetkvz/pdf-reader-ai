import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_reset_email(to_email: str, reset_token: str, reset_link: str):
    subject = "PDF Reader AI - Şifre Sıfırlama"
    body = f"""Merhaba,

Şifreni sıfırlamak için talepte bulundun. Aşağıdaki bağlantıya tıklayarak yeni şifre belirleyebilirsin:

{reset_link}

Bu bağlantı 30 dakika boyunca geçerlidir.

Eğer bu talebi sen yapmadıysan bu emaili görmezden gelebilirsin.

PDF Reader AI"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email gönderme hatası: {e}")
        return False
