from config.database import Database

class ProjectModel:
    def __init__(self):
        self.connection=Database().get_connection()
        
        
    def create_projects_table(self):
        try:
            with self.connection.cursor() as cursor:
                create_table='''
                  CREATE TABLE IF NOT EXISTS projects(
                      pid INT(11) PRIMARY KEY AUTO_INCREMENT,
                      projectTitle VARCHAR(255) NOT NULL,
                      projectDetails LONGTEXT NOT NULL,
                      projectImage VARCHAR(255) NOT NULL,
                      projectCategory VARCHAR(255) NOT NULL,
                      projectWebsite VARCHAR(255) NOT NULL,
                      projectGithub VARCHAR(255) NOT NULL,
                      projectDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                  )
                '''
                cursor.execute(create_table)
                self.connection.commit()
                print("Projects Table Created")
        except Exception as e:
            print(f"Projects Table Not Created : {e}")
            
    def add_project(self,projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub):
        try:
            with self.connection.cursor() as cursor:
                 query="INSERT INTO projects(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub)VALUES(%s,%s,%s,%s,%s,%s)"
                 values=(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub)
                 cursor.execute(query,values)
                 self.connection.commit()
                 print("Project Added")
        except Exception as e:
            print(f"Project Not Added : {e}")
            
    def edit_project(self,projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub,pid):
        try:
            with self.connection.cursor() as cursor:
                 query="UPDATE projects SET projectTitle=%s,projectDetails=%s,projectImage=%s ,projectCategory=%s,projectWebsite=%s,projectGithub=%s WHERE pid=%s"
                 values=(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub,pid)
                 cursor.execute(query,values)
                 self.connection.commit()
                 print("Project Updated")
        except Exception as e:
            print(f"Project Not Updated : {e}")
      
    def get_all_projects(self):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT projects.pid,projects.projectTitle,projects.projectDetails,projects.projectImage,projects.projectCategory,projects.projectWebsite,projects.projectGithub,projects.projectDate,category.cid,category.categoryName  FROM projects JOIN category ON category.cid=projects.projectCategory"
                cursor.execute(query)
                projects=cursor.fetchall()
                print("Projects Found")
                return projects
        except Exception as e:
            print(f"Projects Not Found : {e}")
            
    def get_project(self,pid):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT projects.pid,projects.projectTitle,projects.projectDetails,projects.projectImage,projects.projectCategory,projects.projectWebsite,projects.projectGithub,projects.projectDate,category.cid,category.categoryName  FROM projects JOIN category ON category.cid=projects.projectCategory WHERE projects.pid=%s"
                values=(pid,)
                cursor.execute(query,values)
                project=cursor.fetchone()
                print("Project Found")
                return project
        except Exception as e:
            print(f"Project Not Found : {e}")
            
    def delete_project(self,pid):
        try:
            with self.connection.cursor() as cursor:
                query="DELETE FROM projects WHERE pid=%s"
                values=(pid,)
                cursor.execute(query,values)
                self.connection.commit()
                print("Project Deleted")
        except Exception as e:
            print(f"Project Not Deleted : {e}")
            
####################  Category  ################## 
    def create_category_table(self):
        try:
           with self.connection.cursor() as cursor:
            create_table="""
                CREATE TABLE IF NOT EXISTS category(
                  cid INT(11) PRIMARY KEY AUTO_INCREMENT,
                  categoryName VARCHAR(255) NOT NULL,
                  categoryDetails LONGTEXT NOT NULL,
                  categoryDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            cursor.execute(create_table)
            self.connection.commit()
            print("Category Table  Created")
        except Exception as e:
           print(f"Category Table Not Created : {e}")
        
    def add_category(self,categoryName,categoryDetails):
        try:
            with self.connection.cursor() as cursor:
                query="INSERT INTO category(categoryName,categoryDetails)VALUES(%s,%s)"
                values=(categoryName,categoryDetails)
                cursor.execute(query,values)
                self.connection.commit()
                print("Category Added Successfully")
                return 1
        except Exception as e:
           print(f"Category Not Added : {e}")
           return 0
       
    def get_categories(self):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM category"
                cursor.execute(query,)
                categories=cursor.fetchall()
                print("Categories Found")
                return categories
        except Exception as e:
            print(f"Categories Not Found : {e}")   
            
    def delete_category(self,cid):
        try:
            with self.connection.cursor() as cursor:
                query="DELETE FROM category WHERE cid=%s"
                values=(cid,)
                cursor.execute(query,values)
                self.connection.commit()
                print ("Category Deleted")
                return 1
        except Exception as e:
            print(f"Category Not Deleted : {e}")
            return 0
        
    def get_category(self,cid):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT * FROM category WHERE cid=%s"
                values=(cid,)
                cursor.execute(query,values)
                category=cursor.fetchone()
                print("Category Found ")
                return category
        except Exception as e:
            print(f"Category Not Found : {e}")
    
    def edit_category(self,categoryName,categoryDetails,cid):
        try:
            with self.connection.cursor() as cursor:
                query= "UPDATE category SET categoryName=%s,categoryDetails=%s WHERE id=%s"
                values=(categoryName,categoryDetails,cid)
                cursor.execute(query,values)
                self.connection.commit()
                print("Category Updated")
        except Exception as e:
            print(f"Error Updating Category : {e}")
            
            
    def get_category_projects(self,cid):
        try:
            with self.connection.cursor() as cursor:
                query="SELECT projects.pid,projects.projectTitle,projects.projectDetails,projects.projectImage,projects.projectCategory,projects.projectWebsite,projects.projectGithub,projects.projectDate,category.cid,category.categoryName  FROM projects JOIN category ON category.cid=projects.projectCategory WHERE projects.projectCategory=%s"
                values=(cid,)
                cursor.execute(query,values)
                projects=cursor.fetchall()
                print("Category Projects Found")
                return projects
        except Exception as e:
            print(f"Category Projects Not Found : {e}")
                  
                  