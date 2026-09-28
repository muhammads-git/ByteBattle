import jwt
from dotenv import load_dotenv
import os
from datetime import datetime, timezone,timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
DEFAULT_EXPIRY_MINUTES = int(os.getenv('DEFAULT_EXPIRY_MINUTES'))

def createAccessToken(data :dict, expires_at : timedelta | None = None):
   """ Generate jwt token using the payloads,
      secret key signs this using algo
   """
   payload = data.copy()

   if expires_at:
      expires_at = datetime.now(timezone.utc) + expires_at
   else:
      expires_at = datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_EXPIRY_MINUTES)
   # time
   expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
   # update payload with the expiry time
   payload.update({'exp':expires_at})


   encoded_token = jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

   return encoded_token


def decodeAccessToken(token : str):
   """ decodes the token using jwt.decode:
      and the same secret key with algo
   """
   payload = jwt.decode(token,SECRET_KEY,ALGORITHM)

   username = payload.get('sub')

   if not username:
      # raise Exception
      raise HTTPException(status_code=401, detail="Invalid token payload")

   return payload


# refresh token
def getRefreshToken(token : str):
   pass


# get current user
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')
# FastAPI automatically extracts the token string from the headers and gives it to 'token'
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Now you decode the token that the client provided
        payload = decodeAccessToken(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
