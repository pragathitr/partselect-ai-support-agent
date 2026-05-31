"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.persistence import init_table
from backend.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_table()
    yield


app = FastAPI(title="PartSelect Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
