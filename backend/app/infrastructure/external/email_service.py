import logging

from flask import current_app, has_app_context
from flask_mail import Mail, Message

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, app=None):
        self.mail = Mail(app)
        self._initialized_from_context = app is not None

    def validate_configuration(self):
        if not has_app_context():
            raise RuntimeError('Email service requires a Flask application context')

        missing = []
        for key in ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_DEFAULT_SENDER']:
            if not current_app.config.get(key):
                missing.append(key)

        if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
            missing.extend(['MAIL_USERNAME', 'MAIL_PASSWORD'])

        if missing:
            raise RuntimeError(f"Email service is not configured. Missing: {', '.join(sorted(set(missing)))}")

    def send_email(self, subject: str, recipients: list[str], body: str, html_body: str | None = None):
        if not self._initialized_from_context and has_app_context():
            self.mail.init_app(current_app)
            self._initialized_from_context = True

        self.validate_configuration()
        recipients = [recipient.strip() for recipient in recipients if recipient and recipient.strip()]
        if not recipients:
            raise ValueError('At least one email recipient is required')

        msg = Message(subject, recipients=recipients)
        msg.body = body
        if html_body:
            msg.html = html_body
        try:
            self.mail.send(msg)
        except Exception:
            logger.exception('SMTP send failed for subject=%r recipients=%r', subject, recipients)
            raise
