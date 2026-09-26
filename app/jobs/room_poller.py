from app.database import get_db
from app.models import *
from datetime import datetime,timezone

def advance_rooms_questions():
   db = next(get_db())

   """
   fetch the in_progress rooms 
   returns None  
   """
   rooms = db.query(Room).filter(Room.room_state == 'in_progress').all()

   for room in rooms:
      # current_question_started_time = room.current_question_started_at
      # calculate the time if >< to 15
      # act accordinlgly   
      time = datetime.now(timezone.utc) - room.current_question_started_at
      if time.total_seconds() >= 15:
         # check if the question is last or last index
         total_question_index = len(room.room_quizes) - 1
         if room.current_question_index == total_question_index:
            # Last question
            """ change the question state to ended as the question ended...""" 
            room.room_state = 'ended'
         else:
            # increment the curr ques index
            room.current_question_index += 1
            # reset the curr ques timer to now
            room.current_question_started_at = datetime.utcnow()
   # commit the changes 
   db.commit()

   # returns nothing


