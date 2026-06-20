import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


def send_reset_email(to_email: str, reset_token: str, reset_link: str):
    try:
        resend.Emails.send({
            "from": "PDF Reader AI <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "PDF Reader AI - Şifre Sıfırlama",
            "html": f"""
                <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
                    <h2>Şifre Sıfırlama</h2>
                    <p>Merhaba,</p>
                    <p>Şifreni sıfırlamak için talepte bulundun. Aşağıdaki bağlantıya tıklayarak yeni şifre belirleyebilirsin:</p>
                    <p><a href="{reset_link}" style="background:#4f46e5;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block;">Şifremi Sıfırla</a></p>
                    <p style="color:#666;font-size:13px;">Bu bağlantı 30 dakika boyunca geçerlidir. Eğer bu talebi sen yapmadıysan bu emaili görmezden gelebilirsin.</p>
                    <p style="color:#999;font-size:12px;">PDF Reader AI</p>
                </div>
            """
        })
        return True
    except Exception as e:
        print(f"Email gönderme hatası: {e}")
        return False
