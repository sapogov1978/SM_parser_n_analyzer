from fastapi.templating import Jinja2Templates
import os
from google.oauth2.service_account import Credentials
import gspread

from utl.logging import logger

templates = Jinja2Templates(directory="/app/backend/templates")

LOGOS = {
    "instagram.com": "https://upload.wikimedia.org/wikipedia/commons/9/95/Instagram_logo_2022.svg",
    "tiktok.com": "https://cdn.sanity.io/images/w9oq2e5b/production/4133f3a63cf4e14470189dece716b8a38f7da147-2880x548.png?w=1920&fit=min&auto=format",
    "youtube.com": "https://lh3.googleusercontent.com/DMPqTbcN-R_kPwzF0qg9zZH8UPLtVBoqrDQ_63zhmIq5NUBrllM5Xkj2h7Bi0X_KPzJ6_sTvRFIXWB2HIEeFd2EtnRyUbs0uWTPey3MYtSICaibNBfcA=v0-s1050"
}

BLACKLIST_PERCENTAGE = 0.2

SERVICE_ACCOUNT_FILE = 'credentials.json'
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    logger.error("Missing credentials.json")
    raise RuntimeError("Missing credentials.json")

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)
