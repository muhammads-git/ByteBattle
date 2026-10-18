import os
import sys

# Insert the parent root directory into Python's module path tree
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import sys
import asyncio

# Force Windows to use the Proactive IOCP event loop instead of SelectorLoop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.templates_configs import templates
from app.life import lifespan
from app.services.room import room_router
from app.auths.authentications import auths_router
from fastapi.exceptions import RequestValidationError

app = FastAPI(lifespan=lifespan)
app.include_router(room_router)
app.include_router(auths_router, prefix='/auth')

# serve style.css, etc. at /static/*
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# 1. FIXED: Changed to async def to keep execution off blocking fallback workers
@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse(request, 'login.html', {'request': request})


# 2. FIXED: Changed to async def to align thread processing constraints
@app.get('/home')
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"request": request})


#########  HANDLING THE WRONG NAME PATTERN EXCEPTIONS.
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # figure out which page to send them back to, based on the path they were on
    if request.url.path.endswith('/register'):
        template = 'signup.html'
    elif request.url.path.endswith('/login'):
        template = 'login.html'
    else:
        template = 'signup.html'  # fallback

    return templates.TemplateResponse(request, template, {
        'request': request,
        'error': 'Please check your details — one of the fields isn\'t in the right format.'
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=8001, 
        loop="asyncio",      
        reload=False,
        backlog=4096,      # Double the size of the operating system connection listener queue
        limit_concurrency=500 # Explicitly reject overloads gracefully before throwing OS errors
    )
