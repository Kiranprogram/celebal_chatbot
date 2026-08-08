from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.neo4j_client import get_kg
from app.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_kg()  # connect early
    yield
    get_kg().close()


app = FastAPI(
    title="Knowledge Service — Memory-Augmented Chatbot with Knowledge Graph and Hybrid RAG System",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
