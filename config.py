import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask application configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_society_connect_2026')
    DEBUG = os.environ.get('FLASK_ENV') == 'development'

    # Database configuration
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'society_management')

    # Construct SQLAlchemy database URI
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads configuration
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
