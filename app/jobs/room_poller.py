from app.database import get_db
from app.models import *



def fetch_in_progress_rooms():
   db = next(get_db)

   # fetch the in_progress rooms
   rooms = db.query(Room).filter(Room.room_state == 'in_progress').all()
   if not rooms:
      raise ValueError(f'No in_progress rooms found.')

   

   return rooms

