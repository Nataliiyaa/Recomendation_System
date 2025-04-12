from fastapi import FastAPI
from src.api import main_router

app = FastAPI(
    title="Movie Recommender API"
)

app.include_router(main_router)
