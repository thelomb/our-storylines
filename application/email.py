from flask_mail import Message
# from smtplib import SMTPException
from flask import render_template, current_app
from application import mail
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info('mail sent to ' + str(msg.recipients))
        except ConnectionRefusedError:
            current_app.logger.error('Sending message failed.', exc_info=True)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()


def send_password_reset_email(user):
    """
    Send reset password email to selected user including
    limited validity token
    """
    token = user.get_reset_password_token()
    send_email('Our Storylines - Reset Your Password',
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


def send_general_email(subject, recipients_email, text_body, html_body):
    send_email(subject='Test',
               sender=current_app.config['ADMINS'][0],
               recipients=recipients_email,
               text_body=text_body,
               html_body=html_body)
