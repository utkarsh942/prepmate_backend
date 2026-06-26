from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.home import router as home_router

from app.routes.user_routes import router as user_router
from app.routes.notes_routes import router as notes_router
from app.routes.analytics_routes import router as analytics_router
from app.routes.google_auth import router as google_auth_router


app = FastAPI()

# CORS — allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(home_router)
app.include_router(user_router)
app.include_router(notes_router)
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(google_auth_router, tags=["Google Auth"])
