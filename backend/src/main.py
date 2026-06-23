"""Japanese Driver's License Test Trainer — FastAPI backend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.skill_test import router as skill_test_router
from src.api.routes import api_router
from src.api.routes.rag import router as rag_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(skill_test_router)
app.include_router(rag_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
