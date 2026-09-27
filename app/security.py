import bcrypt
import hashlib
import os
from dotenv import load_dotenv
import hmac

load_dotenv()

PEPPER_KEY = os.getenv('SECRET_KEY','asecret').encode('utf-8')
BCRYPT_ROUNDS = os.getenv('BCRYPT_ROUNDS','12')


class PasswordManager():
   @staticmethod
   def pre_hash_pass(plain_password : str) -> bytes:
      """
        Mixes the password with the secret key (pepper) using HMAC-SHA256.
        Reason: This makes the hash immune to database leaks and safely 
        bypasses bcrypt's 72-character limit.
      """
      hmac_obj = hmac.new(PEPPER_KEY,plain_password.encode('utf-8'),hashlib.sha256)
      return hmac_obj.digest() # returns raw 32 bytes
   
   @classmethod    
   def hash_Pass(cls,plain_password):
      """
        Hashes the peppered password using bcrypt with a unique salt.
        Reason: Returns a clean 'str' text format so you can easily 
        save it to any database (SQLAlchemy, PostgreSQL, MongoDB, etc.).
      """
      peppered_bytes = cls.pre_hash_pass(plain_password)
      salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
      hashed_pss = bcrypt.hashpw(peppered_bytes,salt)
      return hashed_pss.decode('utf-8')

   
   @classmethod
   def verifyPassword(cls,plain_password : str, hashed_password: str)-> bool:
      """
        Verifies the user's login attempt.
        Reason: Bcrypt reads the salt directly out of the hashed_password string, 
        so we don't need a separate database column for salts.
      """
      peppered_bytes = cls._pre_hash_with_pepper(plain_password)
      hash_bytes = hashed_password.encode("utf-8")
        
      # Compares them safely in a way that prevents 'timing attacks'
      return bcrypt.checkpw(peppered_bytes, hash_bytes)