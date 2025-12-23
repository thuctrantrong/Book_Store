from pathlib import Path
import sys
import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]

# add path trước
sys.path.insert(0, str(BASE_DIR / "search-service"))
sys.path.insert(0, str(BASE_DIR / "recommendation-service"))

load_dotenv(BASE_DIR / ".env")

search_router = importlib.import_module(
    "search_app.routers.search_router").router
admin_search_router = importlib.import_module(
    "search_app.routers.admin_search_router").router

recommend_router = importlib.import_module(
    "recommend_app.routers.recommend_router").router

app = FastAPI(title="BOOK-PLATFORM API")

# Enable CORS để FE gọi được
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://localhost:3000",
        "http://localhost:5173", 
        "https://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend_router)
app.include_router(search_router)
app.include_router(admin_search_router)
