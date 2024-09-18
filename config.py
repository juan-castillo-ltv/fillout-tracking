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

TFX_META_APP_ID = os.getenv('TFX_META_APP_ID')
TFX_META_APP_SECRET = os.getenv('TFX_META_APP_SECRET')
TFX_META_LONG_LIVED_TOKEN = os.getenv('TFX_META_LONG_LIVED_TOKEN')
TFX_META_AD_ACCOUNT_ID = os.getenv('TFX_META_AD_ACCOUNT_ID')
TFX_META_CUSTOM_AUDIENCE_ID = os.getenv('TFX_META_CUSTOM_AUDIENCE_ID')

BREVO_API_TOKEN = os.getenv("BREVO_API_TOKEN")

# Configurations for multiple apps
APPS_CONFIG = [
     {
      "app_name": os.getenv("APP1_Name"),
      "api_icm_token": os.getenv("APP1_API_TOKEN"),
      "app_icm_id": os.getenv("APP1_ID"),
      "brevo_active_list": os.getenv("APP1_BREVO_ACTIVE_LIST_ID") ,
      "brevo_paid_list": os.getenv("APP1_BREVO_PAID_LIST_ID"),
      "brevo_free_list": os.getenv("APP1_BREVO_FREE_LIST_ID"),
      "brevo_inactive_list": os.getenv("APP1_BREVO_INACTIVE_LIST_ID")
     },
    {
      "app_name": os.getenv("APP2_Name"),
      "api_icm_token": os.getenv("APP2_API_TOKEN"),
      "app_icm_id": os.getenv("APP2_ID"),
      "brevo_active_list": os.getenv("APP2_BREVO_ACTIVE_LIST_ID"),
      "brevo_paid_list": os.getenv("APP2_BREVO_PAID_LIST_ID"),
      "brevo_free_list": os.getenv("APP2_BREVO_FREE_LIST_ID"),
      "brevo_inactive_list": os.getenv("APP2_BREVO_INACTIVE_LIST_ID")
    },
    {
      "app_name": os.getenv("APP3_Name"),
      "api_icm_token": os.getenv("APP3_API_TOKEN"),
      "app_icm_id": os.getenv("APP3_ID"),
      "brevo_active_list": os.getenv("APP3_BREVO_ACTIVE_LIST_ID"),
      "brevo_paid_list": os.getenv("APP3_BREVO_PAID_LIST_ID"),
      "brevo_free_list": os.getenv("APP3_BREVO_FREE_LIST_ID"),
      "brevo_inactive_list": os.getenv("APP3_BREVO_INACTIVE_LIST_ID")
    },
    {
      "app_name": os.getenv("APP4_Name"),
      "api_icm_token": os.getenv("APP4_API_TOKEN"),
      "app_icm_id": os.getenv("APP4_ID"),
      "brevo_active_list": os.getenv("APP4_BREVO_ACTIVE_LIST_ID"),
      "brevo_paid_list": os.getenv("APP4_BREVO_PAID_LIST_ID"),
      "brevo_free_list": os.getenv("APP4_BREVO_FREE_LIST_ID"),
      "brevo_inactive_list": os.getenv("APP4_BREVO_INACTIVE_LIST_ID")
    },
     {
      "app_name": os.getenv("APP5_Name"),
      "api_icm_token": os.getenv("APP5_API_TOKEN"),
      "app_icm_id": os.getenv("APP5_ID"),
      "brevo_active_list": os.getenv("APP5_BREVO_ACTIVE_LIST_ID"),
      "brevo_paid_list": os.getenv("APP5_BREVO_PAID_LIST_ID"),
      "brevo_free_list": os.getenv("APP5_BREVO_FREE_LIST_ID"),
      "brevo_inactive_list": os.getenv("APP5_BREVO_INACTIVE_LIST_ID")
     },
]