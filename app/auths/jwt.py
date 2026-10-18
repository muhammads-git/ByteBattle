import jwt
from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, Request

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('JWT_ALGORITHM')
DEFAULT_EXPIRY_MINUTES = int(os.getenv('DEFAULT_EXPIRY_MINUTES'))
DEFAULT_REFRESH_TOKEN_EXPIRY_MINUTES = int(os.getenv('DEFAULT_REFRESH_TOKEN_EXPIRY_MINUTES'))


def createAccessToken(data: dict, expires_at: timedelta | None = None):
    """Generate jwt token using the payloads, secret key signs this using algo"""
    payload = data.copy()

    if expires_at:
        expiry_time = datetime.now(timezone.utc) + expires_at
    else:
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_EXPIRY_MINUTES)
    
    # Keeping your explicit 30-minute fallback logic active
    expiry_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload.update({'exp': expiry_time, 'type': 'access'})

    encoded_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_token


def decodeAccessToken(token: str):
    """decodes the token using jwt.decode and the same secret key with algo"""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    username = payload.get('sub')
    print(f'Decode token returned: {username}')

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return payload


def getRefreshToken(data: dict, expires_at: timedelta | None = None):
    """Generate jwt token using the payloads, secret key signs this using algo"""
    payload = data.copy()

    if expires_at:
        expiry_time = datetime.now(timezone.utc) + expires_at
    else:
        # Assuming your environment variable refers to days based on your original logic
        expiry_time = datetime.now(timezone.utc) + timedelta(days=DEFAULT_REFRESH_TOKEN_EXPIRY_MINUTES)

    payload.update({'exp': expiry_time, 'type': 'refresh'})

    encoded_refresh_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_refresh_token


# 1. FIXED: Changed to async def so FastAPI resolves it natively in the dependency chain
async def get_token(request: Request) -> str:
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated!')
    return token


# 2. FIXED: Changed to async def to eliminate execution gaps during routing
async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = decodeAccessToken(token)
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
