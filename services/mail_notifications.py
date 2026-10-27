from flask import current_app
from flask_mail import Message
from markupsafe import escape
from services import portfolio_store as store


def send_enquiry_notification(mailer,message_id,name,phone,email,subject,body):
    recipient=current_app.config.get('MAIL_RECIPIENT','mbuvi@cm.co.ke')
    sender=current_app.config.get('MAIL_DEFAULT_SENDER') or recipient
    message=Message(subject='Website enquiry: '+subject,sender=sender,recipients=[recipient],reply_to=email,
        body=f'New website enquiry\n\nName: {name}\nPhone: {phone}\nEmail: {email}\nSubject: {subject}\n\n{body}',
        html=f'<h2>New website enquiry</h2><p><strong>Name:</strong> {escape(name)}<br><strong>Phone:</strong> {escape(phone)}<br><strong>Email:</strong> {escape(email)}<br><strong>Subject:</strong> {escape(subject)}</p><p style="white-space:pre-wrap">{escape(body)}</p>')
    state='sent'
    try:
        mailer.send(message)
    except Exception:
        current_app.logger.exception('Website enquiry notification could not be sent')
        state='failed'
    if isinstance(message_id,int):
        try:
            with store.db() as connection:
                connection.execute('INSERT INTO notifications(message_id,state,updated) VALUES(?,?,?) ON CONFLICT(message_id) DO UPDATE SET state=excluded.state,updated=excluded.updated', (message_id,state,store.stamp()))
        except Exception:
            current_app.logger.exception('Notification delivery state could not be saved')
    return state=='sent'
