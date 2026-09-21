from app.models import Room,RoomPlayer,Player,Question
from app.database import get_db
from sqlalchemy.orm import Session
import uuid
import random
import string


# a 6 lenght room_code e.g XB73H3
def generate_unique_room_code(lenght = 6):
   chars_digits = string.ascii_uppercase + string.digits
   code = random.choices(chars_digits,k=lenght)
   return code


def create_room(player_id : str):
   """
   create_room, allows a user/player to create_room..
   : insertion in db
   a: generate room_code unique
   b: attach that to url/unique_code
   c: player copies and shares, the link....

   """
   db : Session = get_db()
   # generate unique code using python uuid
   code = generate_unique_room_code()

   # count question and fetched random according to the
   question_count = db.query(Question).count()
   random_questions = random.sample(range(1, question_count + 1), k=3) 
   questions = db.query(Question.id).filter(Question.id.in_(random_questions)).all()
   if not questions:
      print('No question found.')

   # insert into db 
   while True:
      try:
         new_room = Room(
            room_code = code,
            host_id = player_id,

         )
      except Exception as e:
         print('Code exists, re-generate.')
         # again call the function
         code = generate_unique_room_code()
   


   pass





def join_room():
   pass


def start_room():
   pass