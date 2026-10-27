from config.database import Database

class ResumeModel:
    def __init__(self):
        self.connection=Database().get_connection()
        
        
    def create_resume_table(self):
        try:
            with self.connection.cursor() as cursor:
                create_table='''
                    CREATE TABLE IF NOT EXISTS resumes(
                    id INT(11) PRIMARY KEY AUTO_INCREMENT,
                    resume VARCHAR(255) NOT NULL,
                    resumeDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
                    )         
                    '''
                cursor.execute(create_table)
                self.connection.commit()
                print("Resume Table  Created")
        except Exception as e:
            print(f"Resume Table Not Created : {e}")
            
    def save_resume(self,resume):
        try:
            with self.connection.cursor() as cursor:
                query="INSERT INTO resumes(resume)VALUES(%s)"
                values=(resume,)
                cursor.execute(query,values)
                self.connection.commit()
                print("Resume Saved")
        except Exception as e:
            print(f"Resume Not Saved : {e}")
            
    def get_all_resumes(self):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM resumes"
                cursor.execute(query,)
                resumes=cursor.fetchall()
                print("Resumes Found")
                return resumes
        except Exception as e:
            print(f"Resumes Not Found : {e}")
            
    def get_resume(self,pid):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM resumes WHERE id=%s"
                values=(pid,)
                cursor.execute(query,values)
                resume=cursor.fetchone()
                print("Resume Found")
                return resume
        except Exception as e:
            print(f"Resume Not Found : {e}")
    
    def delete_resume(self,rid):
        try:
            with self.connection.cursor() as cursor:
                query="DELETE FROM resumes WHERE id=%s"
                values=(rid,) 
                cursor.execute(query,values)
                self.connection.commit()
                print ("Resume Deleted")
        except Exception as e:
            print(f"Resume Not Deleted : {e}")   
            
            
    def resume(self):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM resumes ORDER BY resumeDate DESC LIMIT 1"
                #query = "SELECT * FROM resumes ORDER BY resumeDate DESC LIMIT 1"
                cursor.execute(query,)
                resume=cursor.fetchone()
                print("Resume Found")
                return resume
        except Exception as e:
            print(f"Resume Not Found : {e}")
                
        