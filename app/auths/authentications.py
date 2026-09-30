from fastapi import APIRouter,Depends,Form,Request
from fastapi.responses import RedirectResponse
from typing import Annotated
from app.models import *
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.room import templates
from app.security import PasswordManager
from app.auths.jwt import createAccessToken,getRefreshToken

auths_router = APIRouter()


@auths_router.post('/register')
def register(request:Request,
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
    if registered.is_registered:
        return templates.TemplateResponse(request, 'signup.html',{
            'request': request,
            'error':'An account is already linked to this Roll No.'
        })

    # hash the password
    hash_password = PasswordManager.hash_Pass(password)
    # insert data into Players and is_registered == True
    new_player = Player(
        player_name = username,
        roll_no = roll_no,
        password_hash = hash_password # hashed_password

    )
    db.add(new_player)

    # Student_registry  -> True
    registered.is_registered = True
    # atomic commit
    db.commit()

    # redirect to login until session management isnt implemented
    return RedirectResponse(url=f"/login", status_code=303)

@auths_router.post('/login')
def login(request:Request,
    db: Session = Depends(get_db),
    roll_no: Annotated[str, Form(...)] = None,
    password: Annotated[str, Form(...)] = None
):

    player = db.query(Player).filter(Player.roll_no == roll_no).first()
    if not player:
        return templates.TemplateResponse(request,'signup.html',{
            'request':request,
            'error':'Player not found.'
        })
    # check passs
    if not PasswordManager.verifyPassword(password,player.password_hash):
        return templates.TemplateResponse(request,'signup.html',{
            'request':request,
            'error':'Invalid Password.'
        })

    # login success
    # create/return  jwt token
    token = createAccessToken({'sub':player.player_name})

    # logged in
    return RedirectResponse(url=f"/home", status_code=303)



    # GET
@auths_router.get('/register-page')
def register_page(request: Request):
    return templates.TemplateResponse(request, 'signup.html', {
        'request': request
    })


@auths_router.get('/login-page')
def login_page(request: Request):
    return templates.TemplateResponse(request, 'login.html', {
        'request': request
    })




@auths_router.post('/refresh')
def get_refresh_token(db:Session=Depends(get_db),refresh_token=str):
    pass