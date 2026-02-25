import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./papers.db")

GOOGLE_SERVICE_ACCOUNT_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY_PATH", "")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
