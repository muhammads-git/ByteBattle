from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.life import lifespan
from app.services.room import room_router

app = FastAPI(lifespan=lifespan)
app.include_router(room_router, prefix='/v1')

# serve style.css, etc. at /static/*
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# point Jinja2 at your templates/ folder
templates = Jinja2Templates(directory="app/templates")

@app.get('/home')
def home(request: Request):
    return templates.TemplateResponse(request,"home.html", {"request": request})