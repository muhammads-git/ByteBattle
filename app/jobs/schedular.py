# 1. Import AsyncIOScheduler instead of BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.room_poller import advance_rooms_questions

# 2. Instantiate the async scheduler
# It hooks right into FastAPI's running asyncio event loop
schedular = AsyncIOScheduler()

# Setup the functions and intervals (the rest stays exactly the same)
# Add max_instances=1 to ensure task execution does not stack up on slow database ticks
schedular.add_job(advance_rooms_questions, 'interval', seconds=1, max_instances=1)

# Start
def start_schedular():
   schedular.start()

# Stop
def stop_schedular():
   schedular.shutdown()
