import os
import smtplib

from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


class EmailService:

    @staticmethod
    def send_email(
        recipients,
        subject,
        body
    ):

        sender = os.getenv("SMTP_EMAIL")
        password = os.getenv("SMTP_APP_PASSWORD")

        msg = MIMEText(body)

        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as server:

            server.starttls()

            server.login(
                sender,
                password
            )

            server.sendmail(
                sender,
                recipients,
                msg.as_string()
            )

