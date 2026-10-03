from app.models import Room, RoomPlayer, Player, Question
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import random
import string
from datetime import datetime,timezone
from fastapi import APIRouter, Depends, Form, Request,HTTPException,status,Form
from fastapi.responses import RedirectResponse
from app.templates_configs import templates
from app.engine import calculateScore
from app.auths.jwt import get_current_user
room_router = APIRouter()



def generate_unique_room_code(length=6):
    chars_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars_digits, k=length))


@room_router.post('/rooms')
def create_room(player_id: int = Form(...), db: Session = Depends(get_db)):
    code = generate_unique_room_code()

    # 1. Safely calculate random questions pool bounds
    question_count = db.query(Question).count()
    if question_count < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Not enough questions in the database to seed a match."
        )
        
    random_questions = random.sample(range(1, question_count + 1), k=3)
    questions = db.query(Question.id).filter(Question.id.in_(random_questions)).all()
    list_quest = [q[0] for q in questions]

    while True:
        try:
            # Explicitly force host_id as integer matching your model schema constraint
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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Host Player ID '{player_id}' does not exist inside registry reference."
                )
            else:
                raise e

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
        raise HTTPException(status_code=404, detail="Target match lobby does not exist.")

    # 2. Fix the name-access trap using an inner join mapping to the Players table
    # This cleanly extracts the player_name string directly into your template dataset
    joined_players = db.query(Player.player_name, RoomPlayer.score, Player.id).\
        join(RoomPlayer, RoomPlayer.player_id == Player.id).\
        filter(RoomPlayer.room_id == room.id).all()

    # (Future Authentication integration point to swap out this placeholder boolean)
    is_viewer_host = False 

    return templates.TemplateResponse(request, "lobby.html", {
        "request": request,
        "room_code": room.room_code,
        "players": joined_players,  # Template access loops now process: player.player_name and player.score cleanly
        "is_host": is_viewer_host,
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



@room_router.get('/rooms/{room_code}/play')
def play_arena(request:Request, room_code : str,db:Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_code == room_code).first()
    if not room:
        raise HTTPException(status_code=404,detail="Room doesn't exist.")


    """ fetch the questions from question, by first finding the current_room's
    quiz index....
    """
    question_ID = room.room_quizes[room.current_question_index]

    question = db.query(Question).filter(Question.id == question_ID).first()


    return templates.TemplateResponse(request, 'arena.html',
    {
        'request':request,
        'question':question.question,
        'options': question.options,
        'correct_option':question.correct_option
    })

    """ """


from datetime import datetime
from fastapi import Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

@room_router.post('/rooms/{room_code}/answer')
def submit_answer(
    request: Request,
    room_code: str,
    option_index: int = Form(...), 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # <--- Aapki dependency
):
    # 1. Room fetch karein
    room = db.query(Room).filter(Room.room_code == room_code).first()

    # 2. Current question nikalen
    current_question_id = room.room_quize[room.current_question_index]
    question = db.query(Question).filter(Question.id == current_question_id).first()

    # 3. Time taken calculate karein
    submission_time = datetime.utcnow()
    time_delta = submission_time - room.question_started_at 
    time_taken = time_delta.total_seconds() 

    # 4. Check correctness & calculate score
    is_correct = (question.correct_option == option_index)
    score_earned = calculateScore(time_taken=time_taken, is_correct=is_correct)
    
    # 5. Player ko username se fetch karke score INCREMENT karein
    player = db.query(RoomPlayer).filter(
        RoomPlayer.room_id == room.id,
        RoomPlayer.username == current_user.username  # Temporary approach
    ).first()
    
    if player:
        player.total_score += score_earned
        db.commit()

    # 6. RETURN / REDIRECT 
    all_players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).order_by(RoomPlayer.score.desc()).all()

    return templates.TemplateResponse(request,
        "room_scores.html", 
        {
            "request": request, 
            "room_code": room_code,
            "players": all_players,
            "your_score_earned": score_earned,
            "was_correct": is_correct
        }
    )

