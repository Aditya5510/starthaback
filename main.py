from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = FastAPI(title="Wellness Concierge API")

checkins = []

def morning_checkin_job():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  
    checkins.append({"time": now, "question": "How did you sleep?"})
    print(f"[{now}] 🔔 Morning Check-In triggered.")


scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.add_job(
    morning_checkin_job,
    trigger="cron",
    hour=8,
    minute=0,
    id="morning_checkin"
)
scheduler.start()

@app.get("/")
async def root():
    return {"message": "👋 Wellness  Backend is live!"}

@app.get("/checkins")
async def get_checkins():
    return {"checkins": checkins}
