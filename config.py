import os
import tempfile
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

    # Allow full connection string override (e.g. cloud MySQL on Vercel)
    _db_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
    if _db_url:
        if _db_url.startswith('mysql://'):
            _db_url = _db_url.replace('mysql://', 'mysql+pymysql://', 1)
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        # Construct SQLAlchemy database URI
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Complaint workflow configuration
    COMPLAINT_OVERDUE_HOURS = int(os.environ.get('COMPLAINT_OVERDUE_HOURS', 24))

    # Uploads configuration
    # Serverless platforms (Vercel, AWS Lambda) have read-only filesystems outside /tmp.
    IS_SERVERLESS = bool(
        os.environ.get('VERCEL')
        or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        or os.environ.get('SERVERLESS')
    )

    if os.environ.get('UPLOAD_FOLDER'):
        UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
    elif IS_SERVERLESS:
        UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'society_connect_uploads')
    else:
        UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test_secret_key_society_connect'
    WTF_CSRF_ENABLED = False
    COMPLAINT_OVERDUE_HOURS = 24
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'society_connect_test_uploads')
