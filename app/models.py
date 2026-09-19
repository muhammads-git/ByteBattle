from app.database import Base
from sqlalchemy import Column,Integer,String,ForeignKey,Text,DateTime
from datetime import datetime, timedelta,timezone

class Room(Base):
   __tablename__ = 'rooms'
   id = Column(Integer, primary_key=True,autoincrement=True)
   host_id = Column(Integer,nullable=False)
   room_code = Column(String(255),nullable=False,unique=True)
   room_state = Column(String,default='waiting')
   created_at = Column(DateTime)
   room_started_at = Column()
   expires_at = Column(DateTime)
   current_question_started_at = Column()
   current_question_index = Column(Integer,default=0)




class Player(Base):
   __tablename__ = 'players'

class RoomPlayer(Base):
   __tablename__ = 'room_players'

