import os
import smtplib
import requests

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

        provider = (
            os.getenv("EMAIL_PROVIDER", "smtp")
            .strip()
            .lower()
        )

        if provider == "brevo":
            EmailService._send_brevo(
                recipients,
                subject,
                body
            )
        else:
            EmailService._send_smtp(
                recipients,
                subject,
                body
            )

    @staticmethod
    def _send_smtp(
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

            print("Using SMTP provider...")

            with smtplib.SMTP(
                "smtp.gmail.com",
                587,
                timeout=30
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

            print("Email sent successfully via SMTP.")

        except Exception as e:

            print(
                f"SMTP Email failed "
                f"({type(e).__name__}): {e}"
            )

            raise

    @staticmethod
    def _send_brevo(
        recipients,
        subject,
        body
    ):

        api_key = os.getenv("BREVO_API_KEY")

        sender_email = os.getenv(
            "BREVO_SENDER_EMAIL"
        )

        sender_name = os.getenv(
            "BREVO_SENDER_NAME"
        )

        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": email
                }
                for email in recipients
            ],
            "subject": subject,
            "textContent": body
        }

        try:

            print("Using Brevo provider...")

            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code not in (
                200,
                201
            ):
                raise RuntimeError(
                    f"Brevo Error: "
                    f"{response.status_code} "
                    f"{response.text}"
                )

            print("Email sent successfully via Brevo.")

        except Exception as e:

            print(
                f"Brevo Email failed "
                f"({type(e).__name__}): {e}"
            )

            raise