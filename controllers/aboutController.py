from flask import Flask,redirect,url_for,render_template
from models.aboutModel import AboutModel

about_model=AboutModel()

def add_about(aboutTitle,aboutDetails,aboutPhoto):
    try:
        about_model.add_about(aboutTitle,aboutDetails,aboutPhoto)
        print("About Added")
    except Exception as e:
        print(f"{e}")
        
def get_all_about():
    try:
        about=about_model.get_all_about()
        return about
    except Exception as e:
        print(f"{e}")
    
def delete_about(id):
    try:
        deleteAbout=about_model.about_delete(id)
    except Exception as e:
        print(f"{e}")
        
def get_about(id):
    about=about_model.get_about(id)
    return about
    
def edit_about(aboutTitle,aboutDetails,aboutPhoto,id):
    about_model.edit_about(aboutTitle,aboutDetails,aboutPhoto,id)
    
    
#################### Education ###########################

def add_education(certification,institution,graduation):
    about_model.add_education(certification,institution,graduation)

def edit_education(certification,institution,graduation,eid):
    about_model.edit_education(certification,institution,graduation,eid)


def get_all_education():
    education=about_model.get_all_education()
    return education

def get_education(eid):
    education=about_model.get_education(eid)
    return education


def delete_education(eid):
    about_model.delete_education(eid)
  