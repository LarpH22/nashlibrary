from flask_mail import Mail, Message


class EmailService:
    def __init__(self, app=None):
        self.mail = Mail(app)

    def send_email(self, subject: str, recipients: list[str], body: str, html_body: str | None = None):
        msg = Message(subject, recipients=recipients)
        msg.body = body
        if html_body:
            msg.html = html_body
        self.mail.send(msg)
