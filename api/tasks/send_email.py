from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from api.core.celery_app import celery_app
from api.core.config import Config
import asyncio


mail_config = ConnectionConfig(
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,  # type: ignore
    MAIL_PORT=Config.MAIL_PORT,
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    MAIL_FROM=Config.MAIL_FROM,
)

mail = FastMail(mail_config)


@celery_app.task
def send_verification_email(recipients: list[str], subject: str, body: str):
    message = MessageSchema(
        recipients=recipients,  # type: ignore
        subject=subject,
        body=body,
        subtype=MessageType.html,
    )

    asyncio.run(mail.send_message(message))
