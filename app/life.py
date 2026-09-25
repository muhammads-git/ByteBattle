from contextlib import asynccontextmanager
from app.life import start_schedular,stop_schedular

@asynccontextmanager
async def lifespan():
   start_schedular()
   yield
   stop_schedular()