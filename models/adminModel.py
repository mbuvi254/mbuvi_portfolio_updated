from  config.database import Database
import uuid
import hmac
from werkzeug.security import check_password_hash, generate_password_hash

class AdminClass:
    def __init__(self):
        self.connection=Database().get_connection()
        
    def create_admin_table(self):
        create_table= ''' CREATE TABLE IF NOT EXISTS admin(
                            aid INT(11) PRIMARY KEY AUTO_INCREMENT, 
                            firstName VARCHAR(255) NOT NULL,
                            lastName VARCHAR(255) NOT NULL,  
                            phoneNumber VARCHAR(255) NOT NULL,                         
                            email VARCHAR(255) NOT NULL,
                            profile_picture VARCHAR(255) NOT NULL,
                            password VARCHAR(255) NOT NULL,
                            status INT(11) NOT NULL,
                            regDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                           );
                      '''
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table)
                self.connection.commit()
                print("Admin Table Created")
        except Exception as e:
            print(f"Admin Table Not Created {e}")
    
    def create_password_reset(self):
        create_password_reset='''CREATE TABLE IF NOT EXISTS password_reset(
                                 pid INT(11) PRIMARY KEY AUTO_INCREMENT,
                                 email VARCHAR(255),
                                 reset_code VARCHAR(255),
                                 resetDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                 );
                              '''
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_password_reset)
                self.connection.commit()
                print("Password Reset Table Created")
        except Exception as e:
            print(f"Password Reset Not Created {e}")

    def create_admin_log_table(self):
        create_table='''CREATE TABLE IF NOT EXISTS admin_log(
                                 id INT(11) PRIMARY KEY AUTO_INCREMENT,
                                 email VARCHAR(255),
                                 ip VARCHAR(255),
                                 loginTime TIME NOT NULL,
                                 logoutTime TIME NULL,
                                 logDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                 );
                              '''
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table)
                self.connection.commit()
                print("Admin Log Table  Created")
        except Exception as e:
            print(f"Admin Log Table Not Created {e}")
            
    def register_admin(self,firstName, lastName, phoneNumber,email,profile_picture,password,status):
        try:
           with self.connection.cursor() as cursor:
              query="INSERT INTO admin(firstName, lastName, phoneNumber,email,profile_picture,password,status)VALUES(%s,%s,%s,%s,%s,%s,%s)"
              values=(firstName, lastName, phoneNumber,email,profile_picture,generate_password_hash(password),status)
              cursor.execute(query,values)
              self.connection.commit()
              print("Librarian Registerd")
              return True
        except Exception as e:
            print(f"Admin Not Registered")
            return False
        
    def update_admin(self,firstName, lastName, phoneNumber,email,profile_picture,password, admin_id):
        try: 
            with self.connection.cursor() as cursor:
                query="UPDATE admin SET firstName=%s,lastName=%s,phoneNumber=%s,email=%s,profile_picture=%s,password=%s WHERE aid=%s"
                values=(firstName, lastName, phoneNumber,email,profile_picture,generate_password_hash(password), admin_id)
                cursor.execute(query,values)
                self.connection.commit()
                print("Admin Updated")
        except Exception as e:
                print(f"Admin Not Updated")  
    
    def check_admin(self,email):
        try:
           with self.connection.cursor() as cursor:
              query="SELECT * FROM admin WHERE email=%s"
              values=(email,)
              cursor.execute(query,values)
              librarian=cursor.fetchone()
              return librarian
        except Exception as e:
            print(f"Admin Not Found")

    def login_admin(self,email,password,status):
        if not email or not password:
            return None
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM admin WHERE email=%s AND status=%s",(email,status))
            admin=cursor.fetchone()
            if not admin:
                return None
            stored=admin[6]
            hashed=stored.startswith(('scrypt:', 'pbkdf2:'))
            try:
                valid=check_password_hash(stored,password) if hashed else hmac.compare_digest(stored.encode(),password.encode())
            except ValueError:
                valid=False
            if not valid:
                return None
            if not hashed:
                cursor.execute("UPDATE admin SET password=%s WHERE aid=%s",(generate_password_hash(password),admin[0]))
                self.connection.commit()
            return admin

    def admin_activate(self,status,email):
        try:
            with self.connection.cursor() as cursor:
                query="UPDATE admin SET status=%s WHERE email=%s"
                values=(status,email)
                cursor.execute(query,values)
                self.connection.commit()
                print("Admin Account Activated")
        except Exception as e:
            print(f"Admin Account Not Activated")

    def check_reset(self,email):
        try:
            with self.connection.cursor() as cursor :
                query="SELECT * FROM password_reset WHERE email=%s"
                values=(email,)
                cursor.execute(query,values)
                return cursor.fetchone()
        except Exception as e:
            return False
        

    def password_reset(self, email, reset_code):
        try:
           with self.connection.cursor() as cursor:
            query = "INSERT INTO password_reset (email, reset_code) VALUES (%s, %s)"
            values = (email, reset_code)
            cursor.execute(query, values)
            self.connection.commit()
            print('Password Reset Successful')
        except Exception as e:
            print(f'Password Reset Failed: {str(e)}')

    def check_password_code(self,reset_code):
        try:
            with self.connection.cursor() as cursor :
                query="SELECT * FROM password_reset WHERE reset_code=%s"
                values=(reset_code,)
                cursor.execute(query,values)
                code=cursor.fetchone()
                return code
        except Exception as e:
             print(f"Reset Not Found")   

    def password_update(self,password,aid,pid):
        try:
            with self.connection.cursor() as cursor:
                query = "UPDATE admin SET password=%s WHERE aid=%s"
                values=(password,aid)
                cursor.execute(query,values)
                self.connection.commit()
                print("Admin Password Updated")
                self.delete_reset(pid)
        except Exception as e:
            print("Admin Not Updated")

 
    
    def delete_reset(self,pid):
        try:
            with self.connection.cursor() as cusror:
                query="DELETE FROM password_reset WHERE pid=%s"
                values=(pid,)
                cusror.execute(query,values)
                self.connection.commit()
                print("Password Reset Deleted")
        except Exception as e:
            print(f"Password Reset Not Deleted")

    def get_admin_logs(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id, email, ip, loginTime, logoutTime, logDate FROM admin_log ORDER BY id DESC LIMIT 500")
            return cursor.fetchall()

    def admin_log(self,email,admin_ip,loginTime):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO admin_log(email,ip,loginTime)VALUES(%s,%s,%s)",
                           (email,admin_ip,loginTime))
            sid = cursor.lastrowid
            self.connection.commit()
            return (sid,)

    def logout(self,logoutTime,email,sid):
        try:
            with self.connection.cursor() as cursor:
                query = "UPDATE admin_log SET logoutTime=%s WHERE email=%s AND id=%s"
                values=(logoutTime,email,sid)
                cursor.execute(query,values)
                self.connection.commit()
                print("Log Updated")
        except Exception as e:
            print("Log Not Updated")
            
            
            
    def count_projects(self):
        try:
            with self.connection.cursor() as cursor:
                query = "SELECT COUNT(pid) FROM projects"
                cursor.execute(query)
                count_result = cursor.fetchone()  # Fetch the result
                count = count_result[0] if count_result else None  # Extract count value from result
                print("Projects Counted")
                return count  # Return the count value
        except Exception as e:
            print("Error while counting projects:", e)
            return None
        
        
    def count_log(self):
        try:
            with self.connection.cursor() as cursor:
                query = "SELECT COUNT(DISTINCT user_ip) FROM user_log"
                cursor.execute(query)
                count_result = cursor.fetchone()  # Fetch the result
                count = count_result[0] if count_result else None  # Extract count value from result
                print("Projects Counted")
                return count  
        except Exception as e:
            print("Error while counting projects:", e)
            return None


    def count_rmessages(self):
        try:
            with self.connection.cursor() as cursor:
                query = "SELECT COUNT(id) FROM messages"
                cursor.execute(query)
                count_result = cursor.fetchone()  # Fetch the result
                count = count_result[0] if count_result else None  # Extract count value from result
                print("Projects Counted")
                return count  # Return the count value
        except Exception as e:
            print("Error while counting projects:", e)
            return None
        
    def count_smessages(self):
        try:
            with self.connection.cursor() as cursor:
                query = "SELECT COUNT(id) FROM sent_messages"
                cursor.execute(query)
                count_result = cursor.fetchone()  # Fetch the result
                count = count_result[0] if count_result else None  # Extract count value from result
                print("Projects Counted")
                return count  # Return the count value
        except Exception as e:
            print("Error while counting projects:", e)
            return None
        