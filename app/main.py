from fastapi import FastAPI
from app.routes.home import router as home_router

from app.routes.user_routes import router as user_router
from app.routes.notes_routes import router as notes_router

app = FastAPI()


app.include_router(home_router)
app.include_router(user_router)
app.include_router(notes_router)
