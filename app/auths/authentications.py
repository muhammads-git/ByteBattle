from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from typing import Annotated
from app.models import StudentRegistry, Player, RefreshToken
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.services.room import templates
from app.security import PasswordManager
from app.auths.jwt import createAccessToken, getRefreshToken, get_current_user
from datetime import datetime, timezone, timedelta
import os
import jwt
from dotenv import load_dotenv

load_dotenv()

auths_router = APIRouter()


@auths_router.post('/register')
async def register(request: Request,
    db: AsyncSession = Depends(get_db),
    username: Annotated[
        str, 
        Form(
            ..., 
            min_length=3, 
            max_length=20, 
            pattern=r"^[a-zA-Z0-9_]+$", 
            description="The user's unique login username"
        )
    ] = None,
    roll_no: Annotated[str, Form(...)] = None,
    password: Annotated[str, Form(...)] = None
):
    # Fetch StudentRegistry using async select
    stmt = select(StudentRegistry).filter(StudentRegistry.roll_no == roll_no)
    res = await db.execute(stmt)
    registered = res.scalars().first()

    if not registered:
        return templates.TemplateResponse(request, 'signup.html', {
            'request': request,
            'error': 'This Roll No is not registered in University.'
        })
        
    if registered.is_registered:
        return templates.TemplateResponse(request, 'signup.html', {
            'request': request,
            'error': 'An account is already linked to this Roll No.'
        })

    hash_password = PasswordManager.hash_Pass(password)
    
    new_player = Player(
        player_name=username,
        roll_no=roll_no,
        password_hash=hash_password
    )
    db.add(new_player)

    registered.is_registered = True
    await db.commit()



    return RedirectResponse(url="/login", status_code=303)


@auths_router.post('/login')
async def login(request: Request,
    db: AsyncSession = Depends(get_db),
    roll_no: Annotated[str, Form(...)] = None,
    password: Annotated[str, Form(...)] = None
):
    # Fetch player using async select
    stmt = select(Player).filter(Player.roll_no == roll_no)
    res = await db.execute(stmt)
    player = res.scalars().first()

    if not player:
        return templates.TemplateResponse(request, 'signup.html', {
            'request': request,
            'error': 'Player not found.'
        })
        
    if not PasswordManager.verifyPassword(password, player.password_hash):
        return templates.TemplateResponse(request, 'signup.html', {
            'request': request,
            'error': 'Invalid Password.'
        })

    access_token = createAccessToken({'sub': player.player_name})
    refresh_token = getRefreshToken({'sub': player.player_name})

    response = RedirectResponse(url="/home", status_code=303)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,       
        samesite="lax",      
        secure=False,        
        max_age=1800          
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax", 
        secure=False,
        path="/auth/refresh", 
        max_age=604800        
    )

    new_refresh_token = RefreshToken(
        player_id=player.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(new_refresh_token)

        #### add ID:Name to REDIS HASHSET....
    redis = request.app.state.redis
    await redis.hset('user:name',str(player.id),player.player_name)

    await db.commit()

    return response


@auths_router.get('/register-page')
async def register_page(request: Request):
    return templates.TemplateResponse(request, 'signup.html', {
        'request': request
    })


@auths_router.get('/login-page')
async def login_page(request: Request):
    return templates.TemplateResponse(request, 'login.html', {
        'request': request
    })


@auths_router.post('/refresh')
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get('refresh_token')
    if not token:
        raise HTTPException(status_code=401, detail='refresh: no cookie')

    stmt = select(RefreshToken).filter(RefreshToken.token == token)
    res = await db.execute(stmt)
    row = res.scalars().first()

    if not row:
        raise HTTPException(status_code=401, detail='refresh: unknown token')

    if row.is_revoked:
        # Secure execution option using an explicit update statement query
        upd_stmt = (
            update(RefreshToken)
            .filter(RefreshToken.player_id == row.player_id)
            .values(is_revoked=True)
        )
        await db.execute(upd_stmt)
        await db.commit()   
        raise HTTPException(status_code=401, detail='refresh: reuse detected, all sessions ended')

    if row.expires_at.replace(tzinfo=timezone.utc) if row.expires_at.tzinfo is None else row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail='refresh: expired')

    player_stmt = select(Player).filter(Player.id == row.player_id)
    player_res = await db.execute(player_stmt)
    player = player_res.scalars().first()
    
    if not player:
        raise HTTPException(status_code=401, detail='refresh: no such player')

    fresh_access = createAccessToken({'sub': player.player_name})
    fresh_refresh = getRefreshToken({'sub': player.player_name})

    row.is_revoked = True
    
    db.add(RefreshToken(
        player_id=player.id,
        token=fresh_refresh,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    ))
    await db.commit()

    response.set_cookie(key='access_token', value=fresh_access, httponly=True,
                        samesite='lax', secure=False, max_age=1800)
    response.set_cookie(key='refresh_token', value=fresh_refresh, httponly=True,
                        samesite='lax', secure=False, path='/auth/refresh', max_age=604800)
    
    return {'status': 'success', 'message': 'Token rotated successfully!'}



# ##### refresh tokennnn..  request
# @auths_router.post('/refresh')
# def get_refresh_token(request:Request,response:Response,db:Session=Depends(get_db)):
#     """
#     fetch the refresh token from httpOnly and db where user is this.
#     match both
#     check if the refreh of db revoked=False and == to httpOnly
    
#     then:
#         revoked=True old refresh expired..
#         create:
#                 refresh
#                 access
#     return both to where they need to be, for the same rotations.. and valdiations...
#     """
#     # fetch the access token from httpOnly
#     http_only_access_token = request.cookies.get('access_token')
#     #fetrch the refresh token from httpOnly
#     http_only_refresh_token = request.cookies.get('refresh_token')

#     if not http_only_refresh_token:
#         raise HTTPException(status_code=401,detail='Session has expired, please login again.')
#     print(f'REFRESH TOKEN COOKIE:',http_only_refresh_token)

#     # fetch the refresh token from db 
#     db_refresh_token = db.query(RefreshToken).filter(RefreshToken.token == http_only_refresh_token).first()
#     if not db_refresh_token:
#         raise HTTPException(status_code=401,detail='The refresh token is not found in db.')
    
#     # if is_revoked, means token is stolen... Terminate all the sessions related this user...
#     if db_refresh_token.is_revoked:
#         # somthing is wrong token is already USED so this can be compormised TOKEN,.. terminate all //
#         db.query(RefreshToken).filter(RefreshToken.player_id == db_refresh_token.player_id).update({'is_revoked':True})
#         # db.commit()
#         raise HTTPException(status_code=401,detail='Security Alert! All sessions are terminated.')

#     # check if token expired by time
#     if db_refresh_token.expires_at < datetime.now(timezone.utc):
#         raise HTTPException(status_code=401,detail='Session has expired, please login again.')

#     try:
#         # fetch username from decoding the token
#         payload = jwt.decode(
#             http_only_access_token,
#             os.getenv('SECRET_KEY'),
#             os.getenv('JWT_ALGORITHM'),
#             options={"verify_exp":False})
        
#         player_name = payload.get('sub')
#         # create fresh access and refresh token
#         fresh_access = createAccessToken({'sub':player_name})
#         fresh_refresh = getRefreshToken({'sub':player_name})

#         # // revok the OLD refrsh token in database
#         db_refresh_token.is_revoked = True
        
#         # insert new refresh token in db
#         new_refresh_token = RefreshToken(
#             player_id=db_refresh_token.player_id,
#             token=fresh_refresh,
#             expire_at=datetime.now(timezone.utc) + timedelta(days=7)
#         )
#         db.add(new_refresh_token)
#         db.commit()


#         # Return both fresh tokens to the browser by overwriting the cookies completely
#         response.set_cookie(
#         key="access_token", 
#         value=fresh_access, 
#         httponly=True, 
#         samesite="lax",
#         secure=False,
#         max_age=1800          # 15 minutes fresh countdown (in seconds)
#         )

#         response.set_cookie(
#         key="refresh_token", 
#         value=fresh_refresh, 
#         httponly=True, 
#         samesite="lax", 
#         path="/auth/refresh",
#         secure=False,
#         max_age=604800       # 7 days fresh countdown (in seconds)
#         )

#         return {"status": "success", "message": "Tokens rotated successfully"}


#     except jwt.PyJWKError:
#         raise HTTPException(status_code=401, detail="Invalid token signature.")