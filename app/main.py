from fastapi import FastAPI
from app.life import lifespan



app = FastAPI(lifespan=lifespan)

@app.get('/home')
def home():
   return 'Hello'