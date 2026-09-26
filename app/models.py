from app.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime,Boolean
from datetime import datetime, timedelta, timezone
from sqlalchemy.dialects.postgresql import ARRAY




class StudentRegistry(Base):
    __tablename__ = 'student_registry'
    
    # Using roll_no as the primary key since it is unique per student
    roll_no = Column(String(50), primary_key=True)
    is_registered = Column(Boolean, default=False, nullable=False)

class Room(Base):
   __tablename__ = 'rooms'
   id = Column(Integer, primary_key=True, autoincrement=True)
   host_id = Column(Integer, ForeignKey('players.id'), nullable=False)
   room_code = Column(String(255), nullable=False, unique=True)
   room_quizes = Column(ARRAY(Integer), nullable=False)
   room_state = Column(String, default='waiting')
   created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
   room_started_at = Column(DateTime(timezone=True))
   expires_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(minutes=10))
   current_question_index = Column(Integer, default=0)
   current_question_started_at = Column(DateTime(timezone=True))

class RoomPlayer(Base):
   __tablename__ = 'room_players'
   id = Column(Integer, primary_key=True, autoincrement=True)
   room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
   player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
   score = Column(Integer, default=0, nullable=False)
   joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
   # --- ADD THESE TWO COLUMNS FOR THE FAKE OUT ---
   # current_round_lie = Column(Text, nullable=True)     # Stores the fake answer they invented
   # current_round_vote = Column(Integer, nullable=True) # Stores the option index they voted for

class Player(Base):
   __tablename__ = 'players'
   id = Column(Integer, primary_key=True, autoincrement=True)
   player_name = Column(String(255), nullable=False, unique=True)
   roll_no = Column(String(50), unique=True, nullable=False)
   password_hash = Column(String(255), nullable=False)

class Question(Base):
   __tablename__ = 'questions'
   id = Column(Integer, primary_key=True, autoincrement=True)
   question = Column(Text, nullable=False)
   options = Column(ARRAY(String), nullable=False)
   correct_option = Column(Integer, nullable=False)