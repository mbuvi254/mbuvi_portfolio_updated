from models.projectModel import ProjectModel

project_model=ProjectModel()

def add_project(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub):
    project_model.add_project(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub)

def edit_project(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub,pid):
    project_model.edit_project(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub,pid)

def get_projects():
    projects=project_model.get_all_projects()
    return projects

def get_project(pid):
    project=project_model.get_project(pid)
    return project
     
def delete_project(pid):
    project_model.delete_project(pid)
 
 
##################  Category ################
    
def add_category(categoryName,categoryDetails):
    project_model.add_category(categoryName,categoryDetails)

def edit_category(categoryName,categoryDetails,cid):
    project_model.edit_category(categoryName,categoryDetails,cid)
    
def get_category(cid):
    category=project_model.get_category(cid)
    return category    
    
def get_categories():
    categories=project_model.get_categories()
    return categories

def delete_category(cid):
    project_model.delete_category(cid)
    
    
def category_projects(cid):
    projects=project_model.get_category_projects(cid)
    return projects
    

    