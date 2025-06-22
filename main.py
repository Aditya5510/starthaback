import os
import datetime
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.background import BackgroundScheduler
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Wellness Concierge API")

# Scopes & paths
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CLIENT_SECRETS_FILE = "client_secret.json"
CRED_STORE = "token.json"  

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://startha.vercel.app"  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


checkins = []


@app.post("/checkins/trigger")
async def trigger_checkin():
    morning_checkin_job()
    return {"status": "triggered"}

def morning_checkin_job():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  
    creds = None
    if os.path.exists(CRED_STORE):
        creds = Credentials.from_authorized_user_file(CRED_STORE, SCOPES)
 
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        with open(CRED_STORE, "w") as token:
            token.write(creds.to_json())

    if not creds:
        print(f"[{now}] ❗ No valid Google credentials—skip event fetch.")
        checkins.append({"time": now, "note": "Please connect Calendar."})
        return

  
    service = build("calendar", "v3", credentials=creds)
    start = datetime.datetime.utcnow().isoformat() + "Z"
    end_dt = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)
    end = end_dt.isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary", timeMin=start, timeMax=end, singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])
    summary = [e["summary"] for e in events]
    checkins.append({"time": now, "events": summary})
    print(f"[{now}] ✅ Fetched {len(summary)} events.")

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.add_job(morning_checkin_job, "cron", hour=8, minute=0, id="morning_checkin")
scheduler.start()

@app.get("/")
async def root():
    return {"message": "👋 Backend live!"}

@app.get("/checkins")
async def get_checkins():
    return {"checkins": checkins}


@app.get("/auth/google/login")
def google_login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=f"https://starthaback-1.onrender.com/auth/google/callback"
    )
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return RedirectResponse(auth_url)


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=f"https://starthaback-1.onrender.com/auth/google/callback"
    )
    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials
    with open(CRED_STORE, "w") as token:
        token.write(creds.to_json())
    return RedirectResponse("https://startha.vercel.app") 
