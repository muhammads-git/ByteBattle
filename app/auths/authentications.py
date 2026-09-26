from fastapi import APIRouter



auths_router = APIRouter()




@auths_router.post('/login')
def login():
   pass