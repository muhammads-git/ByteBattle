from apscheduler.schedulers.background import BackgroundScheduler
from app.jobs.room_poller import advance_rooms_questions

# instantiate schedular
schedular = BackgroundScheduler()

# setup the functions and intervals
schedular.add_job(advance_rooms_questions,'interval',seconds=3)

# start
def start_schedular():
   schedular.start()
# stop
def stop_schedular():
   schedular.shutdown()





