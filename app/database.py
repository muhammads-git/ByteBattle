from sqlalchemy.orm import sessionmaker,declarative_base
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

# CREATE CONNECTION WITH DB...
DATABASE_URL= os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

# create sessions
SessionLocal = sessionmaker(autoflush=False,autocommit=False,bind=engine)

Base = declarative_base()


def get_db():
   db = SessionLocal()
   try:
      yield db
   finally:
      db.close()