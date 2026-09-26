from app.models import Room, RoomPlayer, Player, Question
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import random
import string
from datetime import datetime,timezone
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

room_router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def generate_unique_room_code(length=6):
    chars_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars_digits, k=length))


@room_router.post('/rooms')
def create_room(player_id: str = Form(...), db: Session = Depends(get_db)):
    code = generate_unique_room_code()

    question_count = db.query(Question).count()
    random_questions = random.sample(range(1, question_count + 1), k=3)
    questions = db.query(Question.id).filter(Question.id.in_(random_questions)).all()
    list_quest = [q[0] for q in questions]

    if len(list_quest) < 3:
        raise ValueError('Not enough questions in the database to create a room.')

    while True:
        try:
            new_room = Room(room_code=code, host_id=player_id, room_quizes=list_quest)
            db.add(new_room)
            db.commit()
            break
        except IntegrityError as e:
            db.rollback()
            error_msg = str(e.orig).lower()
            if 'unique' in error_msg or 'duplicate' in error_msg:
                code = generate_unique_room_code()
                continue
            elif 'foreign key' in error_msg or 'violates fk' in error_msg:
                raise ValueError(f"Cannot create room: Host Player ID '{player_id}' does not exist.")
            else:
                raise e

    # room created -> send the host straight to their new lobby
    return RedirectResponse(url=f"/rooms/{new_room.room_code}", status_code=303)


@room_router.post('/rooms/{room_code}/players')
def join_room(room_code: str, player_id: int = Form(...), db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_code == room_code).first()
    if not room:
        raise ValueError("Room doesn't exist.")

    player_exists = db.query(RoomPlayer).filter(
        RoomPlayer.player_id == player_id, RoomPlayer.room_id == room.id
    ).first()
    if player_exists:
        raise ValueError('Player has already joined the room.')

    if room.room_state == 'in_progress':
        raise ValueError('Room has already started.')
    elif room.room_state == 'ended':
        raise ValueError('Room has already ended.')

    if room.expires_at < datetime.now(timezone.utc):
      raise ValueError('Room is expired.')

    join = RoomPlayer(player_id=player_id, room_id=room.id)
    db.add(join)
    db.commit()

    # joined successfully -> land in the same lobby everyone else sees
    return RedirectResponse(url=f"/rooms/{room_code}", status_code=303)


@room_router.get('/rooms/{room_code}')
def view_lobby(request: Request, room_code: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_code == room_code).first()
    if not room:
        raise ValueError("Room doesn't exist.")

    players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()

    return templates.TemplateResponse(request,"lobby.html", {
        "request": request,
        "room_code": room.room_code,
        "players": players,       # template expects .name / .is_host — see note below
        "is_host": False,         # placeholder until auth tells you who's viewing
    })


@room_router.post('/rooms/{room_code}/start')
def start_room(room_code: str, host_id: int = Form(...), db: Session = Depends(get_db)):
    room_exists = db.query(Room).filter(Room.room_code == room_code).first()
    if not room_exists:
        raise ValueError('Room does not exist.')
    if room_exists.host_id != host_id:
        raise ValueError('Unauthorized action.')
    if room_exists.room_state == 'in_progress':
        raise ValueError('Room already started.')
    if room_exists.room_state == 'ended':
        raise ValueError('Room is ended.')
    if room_exists.expires_at < datetime.now(timezone.utc):
      raise ValueError('Room is expired.')

    now = datetime.now(timezone.utc)
    room_exists.room_started_at = now
    room_exists.current_question_started_at = now
    room_exists.room_state = 'in_progress'
    db.commit()

    # game is live -> send everyone into the arena
    return RedirectResponse(url=f"/rooms/{room_code}/play", status_code=303)