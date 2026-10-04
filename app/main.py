from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.templates_configs import templates
from app.life import lifespan
from app.services.room import room_router
from app.auths.authentications import auths_router

app = FastAPI(lifespan=lifespan)
app.include_router(room_router)
app.include_router(auths_router,prefix='/auth')

# serve style.css, etc. at /static/*
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get('/')
def root(request: Request):
    return templates.TemplateResponse(request, 'login.html', {'request': request})

@app.get('/home')
def home(request: Request):
    return templates.TemplateResponse(request,"home.html", {"request": request})


#########  HANDLING THE WRONG NAME PATTERN EXCEPTIONS.
from fastapi.exceptions import RequestValidationError
from fastapi import Request

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