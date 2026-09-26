from fastapi import APIRouter,Depends,Form,Request
from typing import Annotated
from app.models import *
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.room import templates

auths_router = APIRouter()


@auths_router.post('/login')
def login(request:Request,
    db: Session = Depends(get_db),
    username: Annotated[
        str, 
        Form(
            ..., 
            min_length=3, 
            max_length=20, 
            pattern=r"^[a-zA-Z0-9_]+$", # Only allows alphanumeric characters and underscores
            description="The user's unique login username"
        )
    ] = None,
    roll_no: Annotated[str, Form(...)] = None,
    password: Annotated[str, Form(...)] = None
):
    # Your authentication logic goes here
    # check in the db that if roll_no exists in db...
    # and not registered


    registered = db.query(StudentRegistry).filter(StudentRegistry.roll_no == roll_no).first()
    if not registered:
        # return 
        return templates.TemplateResponse(request, 'signup.html',{
            'request':request,
            'error':'This Roll No is not registered in Unviersity.'
        })
    if not registered.is_registered:
        return templates.TemplateResponse(request, 'signup.html',{
            'request': request,
            'error':'An account is already linked to this Roll No.'
        })

    # hash the password
    # insert data into Players and is_registered == True
    