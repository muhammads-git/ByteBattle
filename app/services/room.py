import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auths.jwt import get_current_user
from app.database import get_db
from app.engine import calculateScore
from app.models import Player, Question, Room, RoomPlayer
from app.templates_configs import templates

QUESTION_SECONDS = 15

# Router-level dependency: every route in this file requires a logged-in user,
# and a route added later cannot forget it. Routes that need the user object
# still declare `current_user` themselves; FastAPI runs the dependency once per request.
room_router = APIRouter(dependencies=[Depends(get_current_user)])


def generate_unique_room_code(length=6):
    chars_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars_digits, k=length))


def get_room_or_404(db: Session, room_code: str) -> Room:
    room = db.query(Room).filter(Room.room_code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room doesn't exist.")
    return room


def get_membership(db: Session, room: Room, user_id) -> RoomPlayer | None:
    return db.query(RoomPlayer).filter(
        RoomPlayer.room_id == room.id, RoomPlayer.player_id == user_id
    ).first()


def require_member(db: Session, room: Room, user) -> RoomPlayer:
    member = get_membership(db, room, user)
    if not member:
        raise HTTPException(status_code=403, detail="You haven't joined this room.")
    return member

def get_player_id(db:Session,username):
    return db.query(Player).filter(Player.player_name == username).first()


@room_router.post('/rooms')
def create_room(request : Request,db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    question_count = db.query(Question).count()
    if question_count < 3:
        raise HTTPException(status_code=400, detail="Not enough questions in the database to seed a match.")

    random_questions = random.sample(range(1, question_count + 1), k=3)
    questions = db.query(Question.id).filter(Question.id.in_(random_questions)).all()
    list_quest = [q[0] for q in questions]
    if len(list_quest) < 3:
        raise HTTPException(status_code=400, detail="Could not pick 3 questions.")

    code = generate_unique_room_code()
    player = get_player_id(db,username=current_user)

    # handle if not user return no user found//
    while True:
        try:
            new_room = Room(room_code=code, host_id=player.id, room_quizes=list_quest)
            db.add(new_room)
            db.flush()  # gives new_room.id without committing yet
            # the host plays too, so the host needs a RoomPlayer row as well
            db.add(RoomPlayer(room_id=new_room.id, player_id=player.id))
            db.commit()
            break
        except IntegrityError as e:
            db.rollback()
            error_msg = str(e.orig).lower()
            if 'unique' in error_msg or 'duplicate' in error_msg:
                code = generate_unique_room_code()
                continue
            raise

    return RedirectResponse(url=f"/rooms/{code}", status_code=303)
    # return templates.TemplateResponse(request,'lobby.html',{
    #     'request':request,
    #     'room_code':code
    # })


@room_router.post('/rooms/players')
def join_room(room_code: str= Form(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    room = get_room_or_404(db, room_code)
    # Get user -> user_id
    user = db.query(Player).filter(Player.player_name == current_user).first()
    user_id = user.id
    # re-clicking the link is not an error, just land in the lobby again
    if get_membership(db, room, user_id):
        return RedirectResponse(url=f"/rooms/{room_code}", status_code=303)

    if room.room_state == 'in_progress':
        raise HTTPException(status_code=400, detail="Room has already started.")
    if room.room_state == 'ended':
        raise HTTPException(status_code=400, detail="Room has already ended.")
    if room.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Room is expired.")

    db.add(RoomPlayer(player_id=user_id, room_id=room.id))
    db.commit()

    return RedirectResponse(url=f"/rooms/{room_code}", status_code=303)


@room_router.get('/rooms/{room_code}')
def view_lobby(
    request: Request,
    room_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    room = get_room_or_404(db, room_code)

    rows = (
        db.query(Player.player_name, Player.id)
        .join(RoomPlayer, RoomPlayer.player_id == Player.id)
        .filter(RoomPlayer.room_id == room.id)
        .all()
    )
    # fetch user 
    player = get_player_id(db,username=current_user)
    players = [{"name": name, "is_host": pid == room.host_id} for name, pid in rows]
    is_member = any(pid == player.id for _, pid in rows)

    # a member opening the link after the game began goes straight to the right page
    if is_member and room.room_state == 'in_progress':
        return RedirectResponse(url=f"/rooms/{room_code}/play", status_code=303)
    if is_member and room.room_state == 'ended':
        return RedirectResponse(url=f"/rooms/{room_code}/scores", status_code=303)

    return templates.TemplateResponse(request, "lobby.html", {
        "request": request,
        "room_code": room.room_code,
        "players": players,
        "is_host": room.host_id == player.id,
        "is_member": is_member,
    })


@room_router.post('/rooms/{room_code}/start')
def start_room(room_code: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    room = get_room_or_404(db, room_code)
    # get player ID, name etc
    player = get_player_id(db,current_user)
    
    if room.host_id != player.id:
        raise HTTPException(status_code=403, detail="Only the host can start the game.")
    if room.room_state == 'in_progress':
        raise HTTPException(status_code=400, detail="Room already started.")
    if room.room_state == 'ended':
        raise HTTPException(status_code=400, detail="Room has ended.")
    if room.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Room is expired.")

    now = datetime.now(timezone.utc)
    room.room_started_at = now
    room.current_question_started_at = now
    room.room_state = 'in_progress'
    db.commit()

    return RedirectResponse(url=f"/rooms/{room_code}/play", status_code=303)


@room_router.get('/rooms/{room_code}/play')
def play_arena(
    request: Request,
    room_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    
    player = get_player_id(db,current_user)
    room = get_room_or_404(db, room_code)
    member = require_member(db, room, player.id)

    if room.room_state == 'waiting':
        return RedirectResponse(url=f"/rooms/{room_code}", status_code=303)
    if room.room_state == 'ended':
        return RedirectResponse(url=f"/rooms/{room_code}/scores", status_code=303)

    question = db.query(Question).filter(
        Question.id == room.room_quizes[room.current_question_index]
    ).first()

    elapsed = (datetime.now(timezone.utc) - room.current_question_started_at).total_seconds()
    seconds_left = max(0, QUESTION_SECONDS - int(elapsed))

    players_q = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id)
    total_players = players_q.count()
    answered_count = players_q.filter(
        RoomPlayer.last_answered_index == room.current_question_index
    ).count()

    # note: correct_option is deliberately NOT sent to the browser
    return templates.TemplateResponse(request, 'arena.html', {
        'request': request,
        'room_code': room_code,
        'question_number': room.current_question_index + 1,
        'total_questions': len(room.room_quizes),
        'question_index': room.current_question_index,
        'code_snippet': question.question,
        'options': question.options,
        'seconds_left': seconds_left,
        'total_seconds': QUESTION_SECONDS,
        'answered_count': answered_count,
        'total_players': total_players,
        'already_answered': member.last_answered_index == room.current_question_index,
    })


@room_router.post('/rooms/{room_code}/answer')
def submit_answer(
    room_code: str,
    option_index: int = Form(...),
    question_index: int = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    player = get_player_id(db,current_user)
    room = get_room_or_404(db, room_code)
    if room.room_state != 'in_progress':
        raise HTTPException(status_code=400, detail="Room is not in progress.")

    play_url = f"/rooms/{room_code}/play"

    # stale submit: the round moved on while the player was answering
    if question_index != room.current_question_index:
        return RedirectResponse(url=play_url, status_code=303)

    # row lock: a double-click cannot add the score twice
    player = (
        db.query(RoomPlayer)
        .filter(RoomPlayer.room_id == room.id, RoomPlayer.player_id == player.id)
        .with_for_update() # with_for_update
        .first()
    )
    if not player:
        raise HTTPException(status_code=403, detail="You haven't joined this room.")

    if player.last_answered_index == room.current_question_index:
        return RedirectResponse(url=play_url, status_code=303)

    question = db.query(Question).filter(
        Question.id == room.room_quizes[room.current_question_index]
    ).first()

    time_taken = (datetime.now(timezone.utc) - room.current_question_started_at).total_seconds()
    is_correct = (option_index == question.correct_option)

    player.score += calculateScore(time_taken, is_correct)
    player.last_answered_index = room.current_question_index
    db.commit()

    return RedirectResponse(url=play_url, status_code=303)


@room_router.get('/rooms/{room_code}/scores')
def room_scores(
    request: Request,
    room_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):  
    player = db.query(Player).filter(Player.player_name == current_user).first()
    room = get_room_or_404(db, room_code)
    require_member(db, room, player.id)

    if room.room_state != 'ended':
        return RedirectResponse(url=f"/rooms/{room_code}/play", status_code=303)

    rows = (
        db.query(RoomPlayer, Player.player_name)
        .join(Player, Player.id == RoomPlayer.player_id)
        .filter(RoomPlayer.room_id == room.id)
        .order_by(RoomPlayer.score.desc())
        .all()
    )
    players = [
        {"name": name, "score": rp.score, "is_you": rp.player_id == player.id}
        for rp, name in rows
    ]

    return templates.TemplateResponse(request, "room_score.html", {
        "request": request,
        "room_code": room_code,
        "players": players,
    })