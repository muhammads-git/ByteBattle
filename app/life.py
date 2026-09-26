from contextlib import asynccontextmanager
from app.jobs.schedular import start_schedular,stop_schedular
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app:FastAPI):
   start_schedular()
   yield
   stop_schedular()