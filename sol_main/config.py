import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///solomon.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'profile_pics')
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB upload limit


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False          # disabled by default; CSRF-specific tests re-enable it
    SECRET_KEY = 'test-secret-key'
    # UPLOAD_FOLDER is overridden per-test via a tmp dir fixture so tests never
    # write into static/profile_pics/.
