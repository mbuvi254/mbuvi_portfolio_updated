from config.database import Database

class ContactModel:
    def __init__(self):
        self.connection=Database().get_connection()
        
        
    def create_messages_table(self):
        try:
            with self.connection.cursor() as cursor:
                create_table='''
                    CREATE TABLE IF NOT EXISTS messages(
                    id INT(11) PRIMARY KEY AUTO_INCREMENT,
                    fname VARCHAR(255) NOT NULL,
                    phone VARCHAR(255) NOT NULL, 
                    email VARCHAR(255) NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    message LONGTEXT NOT NULL,
                    status VARCHAR(255) NOT NULL,
                    messageDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
                    )         
                    '''
                cursor.execute(create_table)
                self.connection.commit()
                print("Messages Table  Created")
        except Exception as e:
            print(f"Messages Table Not Created : {e}")
            
    def save_message(self,fname,phone,email,subject,message,status):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO messages(fname,phone,email,subject,message,status)VALUES(%s,%s,%s,%s,%s,%s)",(fname,phone,email,subject,message,status))
            self.connection.commit()
            return cursor.lastrowid

    def inbox_messages(self):
        try:
             with self.connection.cursor() as cursor:
                 status=0
                 query="SELECT * FROM messages WHERE status=%s"
                 values=(status,)
                 cursor.execute(query,values)
                 messages=cursor.fetchall()
                 print("Messages Found")
                 return messages
        except Exception as e:
            print(f"Messages Not Found : {e}")
    
    def read_messages(self):
        try:
             with self.connection.cursor() as cursor:
                 status=1
                 query="SELECT * FROM messages WHERE status=%s"
                 values=(status,)
                 cursor.execute(query,values)
                 messages=cursor.fetchall()
                 print("Messages Found")
                 return messages
        except Exception as e:
            print(f"Messages Not Found : {e}")
            
    def status_update(self,status):
        try:
             with self.connection.cursor() as cursor:
                 query="UPDATE messages SET status=%s"
                 values=(status,)
                 cursor.execute(query,values)
                 self.connection.commit()
                 print("Message Status Updated ")
        except Exception as e:
            print(f"Message Status Not Found : {e}")
            
    def get_messages(self):
        try:
             with self.connection.cursor() as cursor:
                 query="SELECT * FROM messages"
                 cursor.execute(query,)
                 messages=cursor.fetchall()
                 print("Messages Found")
                 return messages
        except Exception as e:
            print(f"Messages Not Found : {e}")
        
    def get_message(self,mid):
        try:
             with self.connection.cursor() as cursor:
                 query="SELECT * FROM messages WHERE id=%s"
                 values=(mid,)
                 cursor.execute(query,values)
                 message=cursor.fetchone()
                 print("Message Found")
                 return message
        except Exception as e:
            print(f"Message Not Found : {e}")
            
###################### Sent Messages ################      
    def create_send_messages_table(self):
        try:
            with self.connection.cursor() as cursor:
                create_table='''
                    CREATE TABLE IF NOT EXISTS sent_messages(
                    id INT(11) PRIMARY KEY AUTO_INCREMENT,
                    email VARCHAR(255) NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    message LONGTEXT NOT NULL,
                    messageDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
                    )         
                    '''
                cursor.execute(create_table)
                self.connection.commit()
                print("Sent Messages Table  Created")
        except Exception as e:
            print(f"Sent Messages Table Not Created : {e}")
     
    def send_reply(self,email,subject,message):
        try:
            with self.connection.cursor() as cursor:
                self.create_send_messages_table()
                query="INSERT INTO sent_messages(email,subject,message)VALUES(%s,%s,%s)"
                values=(email,subject,message)
                cursor.execute(query,values)
                self.connection.commit()
                print("Message Send")
        except Exception as e:
            print(f"Message Sent :{e}")            
     
    def sent_messages(self):
        try:
             with self.connection.cursor() as cursor:
                 query="SELECT * FROM sent_messages"
                 cursor.execute(query,)
                 messages=cursor.fetchall()
                 print("Sent Messages Found")
                 return messages
        except Exception as e:
            print(f"Sent Messages Not Found : {e}")
     
     
     
################  User Log #####################            
    def create_user_log_table(self):
        try:
            with self.connection.cursor() as cursor:
                create_table='''
                    CREATE TABLE IF NOT EXISTS user_log(
                    id INT(11) PRIMARY KEY AUTO_INCREMENT,
                    user_ip VARCHAR(255) NOT NULL,
                    page VARCHAR(255) NOT NULL, 
                    logDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
                    )         
                    '''
                cursor.execute(create_table)
                self.connection.commit()
                print("User Log Table  Created")
        except Exception as e:
            print(f"User Log Table Not Created : {e}")
            
    def save_log(self,user_ip,page):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO user_log(user_ip,page)VALUES(%s,%s)", (user_ip,page))
            self.connection.commit()

    def get_user_logs(self):
        try:
             with self.connection.cursor() as cursor:
                 query="SELECT * FROM user_log"
                 cursor.execute(query,)
                 user_logs=cursor.fetchall()
                 print("Logs Found")
                 return user_logs
        except Exception as e:
            print(f"Logs Not Found : {e}")
            
   
        