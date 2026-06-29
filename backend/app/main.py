import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database.db import engine

from app.api.users import router as users_router
from app.api.clubs import router as clubs_router
from app.api.reports import router as reports_router
from app.api.upload import router as upload_router
from app.api.parser import router as parser_router
from app.api.auth import router as auth_router
from app.api.club_memberships import router as club_memberships_router
from app.api import compliance
from app.api import templates
from app.api.events import router as events_router
from app.api import reviews
from app.api.feedback import (
    router as feedback_router
)
from app.api.event_records import (
    router as event_records_router
)
from app.api.google_drive import (
    router as google_drive_router
)
from app.api.dashboard import (
    router as dashboard_router
)
from app.api.notifications import (
    router as notifications_router
)

from app.api.repository import (
    router as repository_router
)
from app.api import system

app = FastAPI(
    title="AI Report Compliance System"
)

FRONTEND_URL = os.getenv("FRONTEND_URL")

origins = [
    "http://localhost:5173",
]

if FRONTEND_URL and FRONTEND_URL not in origins:
    origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(clubs_router)
app.include_router(reports_router)
app.include_router(upload_router)
app.include_router(parser_router)
app.include_router(auth_router)
app.include_router(club_memberships_router)
app.include_router(compliance.router)
app.include_router(templates.router)
app.include_router(events_router)
app.include_router(
    reviews.router
)
app.include_router(
    feedback_router
)
app.include_router(
    event_records_router
)
app.include_router(
    google_drive_router
)
app.include_router(
    dashboard_router
)
app.include_router(
    notifications_router
)
app.include_router(
    repository_router
)
app.include_router(
    system.router
)


@app.get("/")
def root():
    return {"message": "Backend is running"}    

@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database_status": result.scalar()}
