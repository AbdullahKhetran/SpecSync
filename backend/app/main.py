"""
main.py — FastAPI application entry point.

Start locally:
    uvicorn backend.app.main:app --reload --port 8000

Environment variables are loaded from .env (python-dotenv).
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()  # load .env before anything else reads os.environ

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="TicketSeed API",
    description="Converts a client PRD into sprint plans and developer tickets.",
    version="0.1.0",
)

# CORS — in production Vercel serves frontend and API on the same origin,
# so this is only needed for local development (Vite dev server on :5173).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router, prefix="/api")
