from app.database import Base
from sqlalchemy import Column,Integer,String,ForeignKey,Text,DateTime
from datetime import datetime, timedelta,timezone
from sqlalchemy.dialects.postgresql import ARRAY

class Room(Base):
   __tablename__ = 'rooms'
   id = Column(Integer, primary_key=True, autoincrement=True)
   host_id = Column(Integer, ForeignKey('players.id'), nullable=False)
   room_code = Column(String(255), nullable=False, unique=True)
   room_state = Column(String, default='waiting')
   created_at = Column(DateTime, default=datetime.utcnow)
   room_started_at = Column(DateTime)  # null until host clicks start
   expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
   current_question_started_at = Column(DateTime)
   current_question_index = Column(Integer, default=0)


class Player(Base):
   __tablename__ = 'players'
   id = Column(Integer,primary_key=True,autoincrement=True)




class RoomPlayer(Base):
   __tablename__ = 'room_players'

class Question(Base):
   __tablename__ = 'questions'
   id = Column(Integer, primary_key=True,autoincrement=True)
   question = Column(String(255),nullable=False) # store the question as strings...
   options = Column(ARRAY(String),nullable=False)
   correct_option = Column(Integer,nullable=False)
   