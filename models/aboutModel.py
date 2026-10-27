from  config.database import Database

class AboutModel:
    def __init__(self):
        self.connection = Database().get_connection()
          
    def create_about_table(self):
        try:
           with self.connection.cursor() as cursor:
            create_table="""
                CREATE TABLE IF NOT EXISTS about(
                  id INT(11) PRIMARY KEY AUTO_INCREMENT,
                  aboutTitle VARCHAR(255) NOT NULL,
                  aboutDetails LONGTEXT NOT NULL,
                  aboutPhoto VARCHAR(255) NOT NULL,
                  aboutDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            cursor.execute(create_table)
            self.connection.commit()
            print("About Table  Created")
        except Exception as e:
           print(f"About Table Not Created : {e}")
        
    def add_about(self,aboutTitle,aboutDetails,aboutPhoto):
        try:
            with self.connection.cursor() as cursor:
                self.create_about_table()
                query="INSERT INTO about(aboutTitle,aboutDetails,aboutPhoto)VALUES(%s,%s,%s)"
                values=(aboutTitle,aboutDetails,aboutPhoto)
                cursor.execute(query,values)
                self.connection.commit()
                print("About Added Successfully")
                return 1
        except Exception as e:
           print(f"About Not Added : {e}")
           return 0
       
    def get_all_about(self):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM about"
                cursor.execute(query,)
                about=cursor.fetchall()
                print("About Found")
                return about
        except Exception as e:
            print(f"About Not Found")   
            
    def about_delete(self,id):
        try:
            with self.connection.cursor() as cursor:
                query="DELETE FROM about WHERE id=%s"
                values=(id,)
                cursor.execute(query,values)
                self.connection.commit()
                print ("About Deleted")
                return 1
        except Exception as e:
            print(f"About Not Deleted : {e}")
            return 0
        
    def get_about(self,id):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM about WHERE id=%s"
                values=(id,)
                cursor.execute(query,values)
                about=cursor.fetchone()
                return about
        except Exception as e:
            print(f"About Not Found")
    
    def edit_about(self,aboutTitle,aboutDetails,aboutPhoto,id):
        try:
            with self.connection.cursor() as cursor:
                query= "UPDATE about SET aboutTitle=%s,aboutDetails=%s,aboutPhoto=%s WHERE id=%s"
                values=(aboutTitle,aboutDetails,aboutPhoto,id)
                cursor.execute(query,values)
                self.connection.commit()
                print("About Updated")
        except Exception as e:
            print(f"Error Updating About : {e}")
        

###############  Education #################
    def create_education_table(self):
        try:
           with self.connection.cursor() as cursor:
            create_table="""
                CREATE TABLE IF NOT EXISTS education(
                  id INT(11) PRIMARY KEY AUTO_INCREMENT,
                  certification VARCHAR(255) NOT NULL,
                  institution LONGTEXT NOT NULL,
                  graduation DATE,
                  educationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            cursor.execute(create_table)
            self.connection.commit()
            print("Education Table  Created")
        except Exception as e:
           print(f"Education Table Not Created : {e}") 
           
    def add_education(self,certification,institution,graduation):
        try:
            with self.connection.cursor() as cursor:
                self.create_about_table()
                query="INSERT INTO education(certification,institution,graduation)VALUES(%s,%s,%s)"
                values=(certification,institution,graduation)
                cursor.execute(query,values)
                self.connection.commit()
                print("Education Added Successfully")
                return 1
        except Exception as e:
           print(f"Education Not Added : {e}")
           return 0   
       
    def edit_education(self,certification,institution,graduation,eid):
        try:
            with self.connection.cursor() as cursor:
                query="UPDATE education SET certification=%s,institution=%s,graduation=%s WHERE id=%s"
                values=(certification,institution,graduation,eid)
                cursor.execute(query,values)
                self.connection.commit()
                print("Education Updated Successfully")
                return 1
        except Exception as e:
           print(f"Education Not Updated : {e}")
           return 0  
       
    def get_all_education(self):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM education"
                cursor.execute(query,)
                education=cursor.fetchall()
                print("Education Found")
                return education
        except Exception as e:
            print(f"Education Not Found")
            
    def get_education(self,eid):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM education WHERE id=%s"
                values=(eid,)
                cursor.execute(query,values)
                education=cursor.fetchone()
                print("Education Found")
                return education
        except Exception as e:
            print(f"Education Not Found : {e}")
            
            
    def delete_education(self,eid):
        try:
            with self.connection.cursor() as cursor:
                query="DELETE FROM education WHERE id=%s"
                values=(eid,)
                cursor.execute(query,values)
                self.connection.commit()
                print ("Education Deleted")
                return 1
        except Exception as e:
            print(f"Education Not Deleted : {e}")
                
    