from app.models import Room,RoomPlayer,Player,Question
from app.database import get_db
from sqlalchemy.orm import Session
import uuid
import random

def generate_unique_room_code():
   code = uuid.uuid4()
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

   # fetch the questions for the room
   random_questions = random.sample(range(40),k=3)  # in the range of 40
   questions = db.query(Question).filter(Question.id == random_questions[0])
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