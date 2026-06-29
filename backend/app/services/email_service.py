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

        try:
            with smtplib.SMTP(
                "smtp.gmail.com",
                587,
                timeout=30
            ) as server:

                print("Connecting to Gmail SMTP...")

                server.starttls()

                print("TLS established.")

                server.login(
                    sender,
                    password
                )

                print("Logged in successfully.")

                server.sendmail(
                    sender,
                    recipients,
                    msg.as_string()
                )

                print("Email sent successfully.")

        except Exception as e:
            print(
                f"Email sending failed "
                f"({type(e).__name__}): {e}"
            )
            raise