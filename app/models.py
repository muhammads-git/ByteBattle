from app.database import Base
from sqlalchemy import Column,Integer,String,ForeignKey,Text,DateTime
from datetime import datetime, timedelta,timezone
from sqlalchemy.dialects.postgresql import ARRAY


class Room(Base):
   __tablename__ = 'rooms'
   id = Column(Integer, primary_key=True, autoincrement=True)
   host_id = Column(Integer, ForeignKey('players.id'), nullable=False)
   room_code = Column(String(255), nullable=False, unique=True)
   room_quizes = Column(ARRAY(Integer),nullable=False)  # every room has its own assigned 3 quizes..
   room_state = Column(String, default='waiting')  # waiting -> in_progress -> ended
   created_at = Column(DateTime, default=datetime.utcnow)
   room_started_at = Column(DateTime)  # null until host clicks start
   expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10)) # link expiry
   current_question_index = Column(Integer, default=0)
   current_question_started_at = Column(DateTime) # null until room starts
   
class RoomPlayer(Base):
   __tablename__ = 'room_players'
   id = Column(Integer,primary_key=True,autoincrement=True)
   room_id = Column(Integer,ForeignKey('rooms.id'),nullable=False)
   player_id = Column(Integer,ForeignKey('players.id'),nullable=False)
   score = Column(Integer,default=0,nullable=False)
   joined_at = Column(DateTime,default=datetime.utcnow)

class Player(Base):
   __tablename__ = 'players'
   id = Column(Integer,primary_key=True,autoincrement=True)
   player_name = Column(String(255),nullable=False,unique=True)
   roll_no = Column(Integer,unique=True,nullable=False)
   password_hash = Column(String(255),nullable=False)

class Question(Base):
   __tablename__ = 'questions'
   id = Column(Integer, primary_key=True,autoincrement=True)
   question = Column(Text,nullable=False) # store the question as strings...
   options = Column(ARRAY(String),nullable=False)
   correct_option = Column(Integer,nullable=False)
