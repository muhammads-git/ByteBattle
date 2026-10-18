import os
from dotenv import load_dotenv
# Use the asyncio variations
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# 1. Your DATABASE_URL must use an async driver (e.g., postgresql+asyncpg://...)
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_async_engine(
    DATABASE_URL,
    pool_size=50,          # Maintain up to 50 persistent open connections
    max_overflow=100,      # Allow up to 100 extra burst connections under load
    pool_timeout=10,       # Fail faster! Drop request if no DB connection in 10s (prevents 30s lockups)
    pool_recycle=1800
)

# 3. Configure the sessionmaker to use AsyncSession
SessionLocal = sessionmaker(
    autoflush=False, 
    autocommit=False, 
    bind=engine, 
    class_=AsyncSession  # <--- Crucial step
)

Base = declarative_base()

# 4. Change your dependency to use 'async def' and 'async with' or regular await closure
async def get_db():
   async with SessionLocal() as db:
      yield db
