import os
from dotenv import load_dotenv

# Load environment variables from .env file
#load_dotenv("config.env")
load_dotenv()

# Database configurations remain the same
DB_CREDENTIALS = {
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_DATABASE"),
    "sslmode": os.getenv("DB_SSLMODE")
}

LTV_SAAS_GOOGLE_ADS_ID = os.getenv("LTV_SAAS_GOOGLE_ADS_ID")

PC_GOOGLE_ADS_ID = os.getenv("PC_GOOGLE_ADS_ID")
PC_USER_LIST = os.getenv("PC_USER_LIST")
ICU_GOOGLE_ADS_ID = os.getenv("ICU_GOOGLE_ADS_ID")
ICU_USER_LIST = os.getenv("ICU_USER_LIST")
TFX_GOOGLE_ADS_ID = os.getenv("TFX_GOOGLE_ADS_ID")
TFX_USER_LIST = os.getenv("TFX_USER_LIST")
COD_GOOGLE_ADS_ID = os.getenv("COD_GOOGLE_ADS_ID")
COD_USER_LIST = os.getenv("COD_USER_LIST")

GOOGLE_ADS_CONFIG = os.getenv("GOOGLE_ADS_CONFIG")
