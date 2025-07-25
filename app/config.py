import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = APP_DIR / 'instance'
INSTANCE_DIR.mkdir(exist_ok=True)


class Config:
    APP_TITLE = "Cafés List Website"
    APP_VERSION = "0.1.0"
    APP_DESCRIPTION = "A simple CRUD app for listing and managing cafés with categories."
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR / 'cafes.db'}"
    ASYNC_SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('sqlite', 'sqlite+aiosqlite')
    SQLALCHEMY_ECHO = True if os.getenv("ENV") == "development" else False
    DEBUG = os.getenv("DEBUG", "True") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_placeholder")
    CORS_ORIGINS = ["http://localhost:63343"]
    ENV = os.getenv("ENV", "development")
