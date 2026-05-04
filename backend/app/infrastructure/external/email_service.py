from flask import current_app, has_app_context
from flask_mail import Mail, Message


class EmailService:
    def __init__(self, app=None):
        self.mail = Mail(app)
        self._initialized_from_context = app is not None

    def send_email(self, subject: str, recipients: list[str], body: str, html_body: str | None = None):
        if not self._initialized_from_context and has_app_context():
            self.mail.init_app(current_app)
            self._initialized_from_context = True
        msg = Message(subject, recipients=recipients)
        msg.body = body
        if html_body:
            msg.html = html_body
        self.mail.send(msg)
