from fastapi import FastAPI
from app.life import lifespan
from app.services.room import room_router





# instantiate the main app object...
app = FastAPI(lifespan=lifespan)
# include routers
app.include_router(room_router,prefix='/v1')

@app.get('/home')
def home():
   return 'Hello'