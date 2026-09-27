import jwt
from dotenv import load_dotenv
import os
from datetime import datetime, timezone,timedelta



load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
\


def createAccessToken(data :dict, expires_at = None):
   """ Generate jwt token using the payloads,
      secret key signs this using algo
   """
   payload = data.copy()

   # time
   expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
   # update payload with the expiry time
   payload.update({'expire':expires_at})


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
      pass

   return payload


