from fastapi import APIRouter,Depends,Form,Request,Response,HTTPException
from fastapi.responses import RedirectResponse
from typing import Annotated
from app.models import *
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.room import templates
from app.security import PasswordManager
from app.auths.jwt import createAccessToken,getRefreshToken,get_current_user
import os
import jwt
from dotenv import load_dotenv

load_dotenv()


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
    access_token = createAccessToken({'sub':player.player_name})
    # create/return refresh_token
    refresh_token = getRefreshToken({'sub':player.player_name})

    #creaste response obj
    response = RedirectResponse(url=f"/home", status_code=303)


    # Set the short-lived Access Token Cookie
    response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,       # Prevents JavaScript from reading the token (XSS Protection)
    samesite="lax",      # Protects against CSRF attacks for normal navigation
    secure=False,        # Set to True in production (forces HTTPS only)
    max_age=1800          # 30 minutes in seconds (expires automatically)
    )

    #Set the long-lived Refresh Token Cookie
    response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    samesite="lax", # protect against csrf attacks any requets GET?POST
    secure=False,
    path="/auths/refresh", #  Only sends this cookie when hitting the refresh endpoint!
    max_age=604800        # 7 days in seconds
    )

    # Return the configured response object
    return response



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



##### refresh tokennnn..  request
@auths_router.post('/refresh')
def get_refresh_token(request:Request,response:Response,db:Session=Depends(get_db)):
    """
    fetch the refresh token from httpOnly and db where user is this.
    match both
    check if the refreh of db revoked=False and == to httpOnly
    
    then:
        revoked=True old refresh expired..
        create:
                refresh
                access
    return both to where they need to be, for the same rotations.. and valdiations...
    """
    #fetrch the refresh token from httpOnly
    http_only_refresh_token = request.cookies.get('refresh_token')
    if not http_only_refresh_token:
        raise HTTPException(status_code='401',message='Session has expired, please login again.')
        
    # fetch the refresh token from db 
    db_refresh_token = db.query(RefreshToken).filter(RefreshToken.token == http_only_refresh_token).first()
    if not db_refresh_token:
        raise HTTPException(status_code='401',message='Invalid session token')
    
    # if is_revoked, means token is stolen... Terminate all the sessions related this user...
    if db_refresh_token.is_revoked:
        # somthin gis wrong
        db.query(RefreshToken).filter(RefreshToken.player_id == db_refresh_token.player_id).update({'is_revoked':True})
        # db.commit()
        raise HTTPException(status_code=401,message='Security Alert! All sessions are terminated.')

    # check if token expired by time
    if db_refresh_token.expires_at > datetime.now(timezone.utc):
        raise HTTPException(status_code=401,message='Session has expired, please login again.')

    try:
        # fetch username from decoding the token
        payload = jwt.decode(http_only_refresh_token,os.getenv('SECRET_KEY'),os.getenv('JWT_ALGORITHM'))
        player_name = payload.get('sub')
        # create fresh access and refresh token
        fresh_access = createAccessToken({'sub':player_name})
        fresh_refresh = getRefreshToken({'sub':player_name})

        # // revok the OLD refrsh token in database
        db_refresh_token.is_revoked = True
        
        # insert new refresh token in db
        new_refresh_token = RefreshToken(
            player_id=db_refresh_token.player_id,
            token=fresh_refresh,
            expire_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(new_refresh_token)
        db.commit()


        # Return both fresh tokens to the browser by overwriting the cookies completely
        response.set_cookie(
        key="access_token", 
        value=fresh_access, 
        httponly=True, 
        samesite="lax",
        secure=False,
        max_age=1800          # 15 minutes fresh countdown (in seconds)
        )

        response.set_cookie(
        key="refresh_token", 
        value=fresh_refresh, 
        httponly=True, 
        samesite="lax", 
        path="/auths/refresh",
        secure=False,
        max_age=604800       # 7 days fresh countdown (in seconds)
        )

        return {"status": "success", "message": "Tokens rotated successfully"}


    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token signature.")