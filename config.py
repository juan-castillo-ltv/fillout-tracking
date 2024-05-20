import os
from dotenv import load_dotenv

# Load environment variables from .env file
#load_dotenv("config.env")
load_dotenv()

UPDATE_INTERVAL = os.getenv("UPDATE_INTERVAL")
TIME_DELAY = os.getenv("TIME_DELAY")
OFFSET_BT_SCRIPTS = os.getenv("OFFSET_BT_SCRIPTS")

# Database configurations remain the same
DB_CREDENTIALS = {
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_DATABASE"),
    "sslmode": os.getenv("DB_SSLMODE")
}