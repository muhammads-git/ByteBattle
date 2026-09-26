from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.templates_configs import templates
from app.life import lifespan
from app.services.room import room_router
from app.auths.authentications import auths_router

app = FastAPI(lifespan=lifespan)
app.include_router(room_router, prefix='/v1')
app.include_router(auths_router,prefix='/auths')

# serve style.css, etc. at /static/*
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get('/home')
def home(request: Request):
    return templates.TemplateResponse(request,"home.html", {"request": request})