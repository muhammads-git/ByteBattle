from contextlib import asynccontextmanager
from app.jobs.schedular import start_schedular,stop_schedular
from fastapi import FastAPI
import redis.asyncio as aioredis 
from dotenv import load_dotenv
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app:FastAPI):
   # start the redis connection

   #
   print("Connecting to local Redis server...")


   redis_client = aioredis.from_url(
      os.getenv('REDIS_URL'),
      decode_responses=True
   
   )
   # store in the app.state
   app.state.redis = redis_client
   

   # schedular start
   start_schedular()
   yield
   # schedular stpp
   stop_schedular()

   # stop redis
   print("Closing Redis connection pool...")

   await redis_client.close()