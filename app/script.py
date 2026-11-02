import os
import random
import uuid
import asyncio
from datetime import datetime, timezone
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import *
# Import your models here
# from app.database import Base
# from app.models import StudentRegistry, Player, RoomPlayer

# --- CONFIGURATION ---
# Note: Use asyncpg driver for asynchronous SQLAlchemy operations
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:muhammadpostdb@localhost/bytebattle")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

TARGET_ROOM_ID = 1          # Active room context for room_players
NUM_PLAYERS = 5000          # Number of rows/players to generate

async def seed_load_test_data():
    print(f"🚀 Starting data generation for {NUM_PLAYERS} players...")
    
    # 1. Initialize DB and Redis connections
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    
    # Generate random unique student data structures upfront
    generated_data = []
    for i in range(NUM_PLAYERS):
        unique_id = str(uuid.uuid4())[:8]
        roll_no = f"ROLL-{i:05d}-{unique_id}"
        player_name = f"Player_{i:05d}_{unique_id}"
        fake_password_hash = "scrypt:32768:8:1$fakehashvalue"
        generated_data.append((roll_no, player_name, fake_password_hash))

    async with AsyncSessionLocal() as session:
        try:
            # 2. Bulk Seed Student Registry
            print("📝 Seeding StudentRegistry...")
            student_registries = [
                {"roll_no": row[0], "is_registered": True} for row in generated_data
            ]
            await session.execute(
                StudentRegistry.__table__.insert(), student_registries
            )
            
            # 3. Bulk Seed Players
            print("👤 Seeding Players...")
            players_payload = [
                {"player_name": row[1], "roll_no": row[0], "password_hash": row[2]} 
                for row in generated_data
            ]
            await session.execute(
                Player.__table__.insert(), players_payload
            )
            await session.commit()
            
            # Fetch the generated IDs to tie RoomPlayer records and Redis maps correctly
            print("🔄 Fetching newly created Player accounts...")
            from sqlalchemy import select
            result = await session.execute(select(Player.id, Player.player_name, Player.roll_no))
            db_players = result.all()
            
            # Filter down to the players we just created in this execution batch
            target_roll_nos = {row[0] for row in generated_data}
            created_players = [p for p in db_players if p.roll_no in target_roll_nos]

            # 4. Process RoomPlayers and Redis Data Structures via Pipeline
            print("🏆 Mapping profiles into RoomPlayer rows & structuring Redis cache...")
            room_players = []
            
            # Establish an async Redis pipeline execution buffer
            redis_pipeline = redis_client.pipeline()
            
            for player in created_players:
                random_score = random.randint(100, 2500)
                
                # SQL tracking setup
                room_players.append({
                    "room_id": TARGET_ROOM_ID,
                    "player_id": player.id,
                    "score": random_score,
                    "last_answered_index": -1,
                    "joined_at": datetime.now(timezone.utc)
                })
                
                # Match your application's architecture rules exactly:
                # Rule A: update global:leaderboard (ZSET) using stringified player_id
                redis_pipeline.zadd("global:leaderboard", {str(player.id): random_score})
                
                # Rule B: Map player_id back to plaintext names in user:name (HASH)
                redis_pipeline.hset("user:name", str(player.id), player.player_name)

            # Fire off batch statements to save database trip overhead
            await session.execute(RoomPlayer.__table__.insert(), room_players)
            await session.commit()
            
            print("⚡ Executing Redis storage structures...")
            await redis_pipeline.execute()
            
            print(f"✅ Success! {NUM_PLAYERS} profiles populated cleanly in PostgreSql and Redis cache sets.")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Pipeline generation failed: {e}")
            raise e
        finally:
            await redis_client.close()
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_load_test_data())
