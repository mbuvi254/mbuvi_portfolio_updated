from models.resumeModel import ResumeModel

resume_model=ResumeModel()

def add_resume(resume):
    resume_model.save_resume(resume)
    
def get_resumes():
    resumes=resume_model.get_all_resumes()
    return resumes

def get_resume(pid):
    resume=resume_model.get_resume(pid)
    return resume

def delete_resume(rid):
    resume=resume_model.delete_resume(rid)
    
def resume():
    resume=resume_model.resume()
    return resume