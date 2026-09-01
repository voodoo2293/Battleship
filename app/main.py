from fastapi import FastAPI

from app.api.games import router as games_router

app = FastAPI()

app.include_router(games_router)