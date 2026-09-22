from app.models import Room,RoomPlayer,Player,Question
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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
   # [(),(),()] add integers from tuples to a list 
   list_quest = []
   for question in questions:
      list_quest.append(question[0])

   if not list_quest or len(list_quest) < 3:
      raise ValueError(f'Not enough questions in the database to create a room.')

   # insert into db 
   while True:
      try:
         new_room = Room(
            room_code = code,
            host_id = player_id,
            room_quizes=list_quest # see if the syntax is right as this is: array(int)
         )
         # add and commit() //
         db.add(new_room)
         db.commit()
         break # succes break the loop
      except IntegrityError as e:
         db.rollback() # 
         error_msg = str(e.orig).lower()

         # Case A: IF unique in erros means, its duplication so , retry again...
         if 'unique' in error_msg or 'duplicate' in error_msg:
            code = generate_unique_room_code() # re-generate the code and continue to while loop
            continue # retry, re-generate the code and insert
         # Case B: IF its foreign key or Id error, stop .
         elif 'foreign key' in error_msg or 'violates fk' in error_msg:
            raise ValueError(f"Cannot create room: Host Player ID '{player_id}' does not exist.")

         else:
            raise e
   

def join_room():
   pass


def start_room():
   pass