import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import HttpUrl
from sqlalchemy.exc import IntegrityError

from sqlalchemy.ext.asyncio import AsyncSession  # asyncsessions for asynchronous handling event loop
from sqlalchemy import func, select

from app.auths.jwt import get_current_user
from app.database import get_db          # Assumes this now yields an AsyncSession
from app.engine import calculateScore
from app.models import Player, Question, Room, RoomPlayer
from app.templates_configs import templates

QUESTION_SECONDS = 15

# Router-level dependency manages the user context execution sequence safely
room_router = APIRouter(dependencies=[Depends(get_current_user)])


#  ASYNC HELPER FUNCTIONS (Non-blocking coroutines)

def generate_unique_room_code(length=6):
    chars_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars_digits, k=length))


async def get_room_or_404(db: AsyncSession, room_code: str) -> Room:
    # Expression execution strategy replaces old sequential db.query chains
    stmt = select(Room).filter(Room.room_code == room_code)
    result = await db.execute(stmt)
    room = result.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Room doesn't exist.")
    return room


async def get_membership(db: AsyncSession, room: Room, user_id) -> RoomPlayer | None:
    stmt = select(RoomPlayer).filter(
        RoomPlayer.room_id == room.id, RoomPlayer.player_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def require_member(db: AsyncSession, room: Room, user) -> RoomPlayer:
    member = await get_membership(db, room, user)
    if not member:
        raise HTTPException(status_code=403, detail="You haven't joined this room.")
    return member


async def get_player_id(db: AsyncSession, username):
    stmt = select(Player).filter(Player.player_name == username)
    result = await db.execute(stmt)
    return result.scalars().first()


# 🎮 COROUTINE POST/GET ROUTES (Event loop never freezes on these)

@room_router.post('/rooms')
async def create_room(request: Request, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    count_stmt = select(func.count(Question.id))
    question_count = await db.scalar(count_stmt)
    
    if question_count < 3:
        raise HTTPException(status_code=400, detail="Not enough questions in the database to seed a match.")

    random_questions = random.sample(range(1, question_count + 1), k=3)
    
    quest_stmt = select(Question.id).filter(Question.id.in_(random_questions))
    quest_result = await db.execute(quest_stmt)
    list_quest = [q_id for q_id in quest_result.scalars()]
    
    if len(list_quest) < 3:
        raise HTTPException(status_code=400, detail="Could not pick 3 questions.")

    code = generate_unique_room_code()
    player = await get_player_id(db, username=current_user)

    while True:
        try:
            new_room = Room(room_code=code, host_id=player.id, room_quizes=list_quest)
            db.add(new_room)
            await db.flush()  # Non-blocking context sync captures memory key ID
            
            db.add(RoomPlayer(room_id=new_room.id, player_id=player.id))
            await db.commit() # Database save released instantly!
            break
        except IntegrityError as e:
            await db.rollback()
            error_msg = str(e.orig).lower()
            if 'unique' in error_msg or 'duplicate' in error_msg:
                code = generate_unique_room_code()
                continue
            raise

    return RedirectResponse(url=f"/rooms/{code}", status_code=303)


@room_router.post('/rooms/players')
async def join_room(room_code: str = Form(...), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    room = await get_room_or_404(db, room_code)
    
    user_stmt = select(Player).filter(Player.player_name == current_user)
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()
    user_id = user.id
    
    if await get_membership(db, room, user_id):
        return RedirectResponse(url=f"/rooms/{room_code}", status_code=303)

    if room.room_state == 'in_progress':
        raise HTTPException(status_code=400, detail="Room has already started.")
    if room.room_state == 'ended':
        raise HTTPException(status_code=400, detail="Room has already ended.")
    if room.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Room is expired.")

    db.add(RoomPlayer(player_id=user_id, room_id=room.id))
    await db.commit()

    return RedirectResponse(url=f"/rooms/{room_code}", status_code=303)


@room_router.get('/rooms/{room_code}')
async def view_lobby(
    request: Request,
    room_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    room = await get_room_or_404(db, room_code)
    player = await get_player_id(db, username=current_user)

    membership = await get_membership(db, room, player.id)

    if not membership:
        if room.room_state == 'in_progress':
            raise HTTPException(status_code=400, detail="Cannot join via link. Game already started.")
        if room.room_state == 'ended':
            raise HTTPException(status_code=400, detail="This room has already ended.")
        if room.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="This room link has expired.")

        db.add(RoomPlayer(player_id=player.id, room_id=room.id))
        await db.commit()
        print(f"Player {player.player_name} successfully auto-enrolled via shared link.")

    rows_stmt = (
        select(Player.player_name, Player.id)
        .join(RoomPlayer, RoomPlayer.player_id == Player.id)
        .filter(RoomPlayer.room_id == room.id)
    )
    rows_result = await db.execute(rows_stmt)
    rows = rows_result.all()

    players = [{"name": name, "is_host": pid == room.host_id} for name, pid in rows]
    is_member = any(pid == player.id for _, pid in rows)

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
async def start_room(room_code: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    room = await get_room_or_404(db, room_code)
    player = await get_player_id(db, current_user)
    
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
    await db.commit()

    return RedirectResponse(url=f"/rooms/{room_code}/play", status_code=303)

@room_router.get('/rooms/{room_code}/play')
async def play_arena(
    request: Request,
    room_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    player = await get_player_id(db, current_user)
    room = await get_room_or_404(db, room_code)
    member = await require_member(db, room, player.id)

    if room.room_state == 'waiting':
        return RedirectResponse(url=f"/rooms/{room_code}", status_code=303)
    if room.room_state == 'ended':
        return RedirectResponse(url=f"/rooms/{room_code}/scores", status_code=303)

    # Expression parsing style handles the question retrieval dynamically
    q_stmt = select(Question).filter(
        Question.id == room.room_quizes[room.current_question_index]
    )
    q_result = await db.execute(q_stmt)
    question = q_result.scalars().first()

    elapsed = (datetime.now(timezone.utc) - room.current_question_started_at).total_seconds()
    seconds_left = max(0, QUESTION_SECONDS - int(elapsed))

    # Optimizing counts: Replacing separate queries with efficient expression execution
    total_players_stmt = select(func.count(RoomPlayer.id)).filter(RoomPlayer.room_id == room.id)
    total_players = await db.scalar(total_players_stmt)

    answered_stmt = select(func.count(RoomPlayer.id)).filter(
        RoomPlayer.room_id == room.id,
        RoomPlayer.last_answered_index == room.current_question_index
    )
    answered_count = await db.scalar(answered_stmt)

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
async def submit_answer(
    room_code: str,
    option_index: int = Form(...),
    question_index: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    player_info = await get_player_id(db, current_user)
    room = await get_room_or_404(db, room_code)
    if room.room_state != 'in_progress':
        raise HTTPException(status_code=400, detail="Room is not in progress.")

    play_url = f"/rooms/{room_code}/play"

    if question_index != room.current_question_index:
        return RedirectResponse(url=play_url, status_code=303)
    
    # 💥 THE ROW LOCK REWRITE: 
    # Standard .with_for_update() must now be wrapped inside an awaited select statement.
    # While the DB holds this lock, the thread immediately yields control back to the event loop!
    lock_stmt = (
        select(RoomPlayer)
        .filter(RoomPlayer.room_id == room.id, RoomPlayer.player_id == player_info.id)
        .with_for_update()
    )
    lock_result = await db.execute(lock_stmt)
    room_player = lock_result.scalars().first()
    
    if not room_player:
        raise HTTPException(status_code=403, detail="You haven't joined this room.")

    if room_player.last_answered_index == room.current_question_index:
        return RedirectResponse(url=play_url, status_code=303)    

    q_stmt = select(Question).filter(
        Question.id == room.room_quizes[room.current_question_index]
    )
    q_result = await db.execute(q_stmt)
    question = q_result.scalars().first()

    time_taken = (datetime.now(timezone.utc) - room.current_question_started_at).total_seconds()
    is_correct = (option_index == question.correct_option)

    room_player.score += calculateScore(time_taken, is_correct)
    room_player.last_answered_index = room.current_question_index
    
    # Non-blocking async commit context synchronization
    await db.commit()

    return RedirectResponse(url=play_url, status_code=303)


@room_router.get('/rooms/{room_code}/scores')
async def room_scores(
    request: Request,
    room_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):  
    player = await db.query(Player).filter(Player.player_name == current_user).first()
    # Using explicit mapping fallback:
    stmt_p = select(Player).filter(Player.player_name == current_user)
    res_p = await db.execute(stmt_p)
    player = res_p.scalars().first()
    
    room = await get_room_or_404(db, room_code)
    await require_member(db, room, player.id)

    if room.room_state != 'ended':
        return RedirectResponse(url=f"/rooms/{room_code}/play", status_code=303)

    rows_stmt = (
        select(RoomPlayer, Player.player_name)
        .join(Player, Player.id == RoomPlayer.player_id)
        .filter(RoomPlayer.room_id == room.id)
        .order_by(RoomPlayer.score.desc())
    )
    rows_result = await db.execute(rows_stmt)
    rows = rows_result.all()

    players = [
        {"name": name, "score": rp.score, "is_you": rp.player_id == player.id}
        for rp, name in rows
    ]

    return templates.TemplateResponse(request, "room_score.html", {
        "request": request,
        "room_code": room_code,
        "players": players,
    })


@room_router.get('/rooms/{room_code}/time')
async def get_time_left(room_code: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    stmt = select(Room).filter(Room.room_code == room_code)
    result = await db.execute(stmt)
    room = result.scalars().first()
    
    if not room:
        raise HTTPException(status_code=404, detail='Room not found.')

    current_question_index = room.current_question_index
    question_started_time = room.current_question_started_at
    elapsed = (datetime.now(timezone.utc) - question_started_time).total_seconds()

    time_left = max(0, 15 - int(elapsed))

    return {
        'time_left': time_left,
        'current_question_index': current_question_index,
        'room_state': room.room_state
    }


@room_router.get('/leaderboard')
async def leaderboard(request: Request, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    user_stmt = select(Player).filter(Player.player_name == current_user)
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()

    # 📊 THE HEAVY QUERY REWRITE: 
    # Executing the aggregate query asynchronously ensures that the event loop can juggle 
    # other player ticks while Postgres/MySQL performs sorting and grouping operations.
    leaderboard_stmt = (
        select(
            Player.id,
            Player.player_name,
            func.sum(RoomPlayer.score).label('total_score'),
        )
        .join(RoomPlayer, RoomPlayer.player_id == Player.id)
        .join(Room, RoomPlayer.room_id == Room.id)
        .filter(Room.room_state == 'ended')
        .group_by(Player.id, Player.player_name)
        .order_by(func.sum(RoomPlayer.score).desc(), Player.player_name)
        .limit(20)
    )
    leaderboard_result = await db.execute(leaderboard_stmt)
    rows = leaderboard_result.all()

    return templates.TemplateResponse(request, "leaderboard.html", {
        'players': rows,
        'current_user_id': user.id,
        'request': request
    })
