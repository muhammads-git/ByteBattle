from app.database import SessionLocal  # Import your session factory directly
from app.models import Room
from datetime import datetime, timezone
from sqlalchemy.future import select

async def advance_rooms_questions():
    # Create an isolated, dedicated session context for this specific 1-second tick
    async with SessionLocal() as db:
        try:
            stmt = select(Room).filter(Room.room_state == 'in_progress')
            result = await db.execute(stmt)
            rooms = result.scalars().all()

            for room in rooms:
                current_time = datetime.now(timezone.utc)
                started_at = room.current_question_started_at.replace(tzinfo=timezone.utc) if room.current_question_started_at.tzinfo is None else room.current_question_started_at
                
                time_elapsed = current_time - started_at
                
                if time_elapsed.total_seconds() >= 15:
                    total_question_index = len(room.room_quizes) - 1
                    
                    if room.current_question_index == total_question_index:
                        room.room_state = 'ended'
                    else:
                        room.current_question_index += 1
                        room.current_question_started_at = datetime.now(timezone.utc)
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            print(f"Error updating rooms: {e}")
