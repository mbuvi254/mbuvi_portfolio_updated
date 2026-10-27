from models.contactModel import ContactModel

contact_model=ContactModel()

def send_message(fname,phone,email,subject,message,status):
    return contact_model.save_message(fname,phone,email,subject,message,status)
    
def inbox_messages():
    messages=contact_model.inbox_messages()
    return messages

def read_messages():
    messages=contact_model.read_messages()
    return messages

def sent_messages():
    messages=contact_model.sent_messages()
    return messages

def send_reply(email,subject,message):
    contact_model.send_reply(email,subject,message)

def status_update(status):
    contact_model.status_update(status)
    
def get_messages():
    messages=contact_model.get_messages()
    return messages

def get_message(mid):
    message=contact_model.get_message(mid)
    return message     

    
def user_log(user_ip,page):
    contact_model.save_log(user_ip,page)
    
def get_user_logs():
    user_logs=contact_model.get_user_logs()
    return user_logs
    
    