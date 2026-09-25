from app.database import get_db
from app.models import *
from datetime import datetime


def advance_rooms_questions():
   db = next(get_db)

   """
   fetch the in_progress rooms   
   """
   rooms = db.query(Room).filter(Room.room_state == 'in_progress').all()
   if not rooms:
      raise ValueError(f'No in_progress rooms found.')

   for room in rooms:
      # current_question_started_time = room.current_question_started_at
      # calculate the time if >< to 15
      # act accordinlgly   
      time = datetime.utcnow() - room.current_question_started_at.total_seconds()
      if time >= 15:
         # check if the question is last or last index
         last_index = room.current_question_index 
         if last_index == len(room.room_quizes) - 1:
            pass
