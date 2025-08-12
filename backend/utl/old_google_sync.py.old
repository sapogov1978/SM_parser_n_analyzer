import os
import sys
import gspread

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from db.models import Network, Account
from db.db import SessionLocal
from utl.logging import logger

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

SPREADSHEET_ID = '1NwTFkaD6JPtMpjZUf40f5NgcaOFAv3mVHRlpIpCAxog'

def get_sheet_values(sheet_name: str):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=sheet_name).execute()
    values = result.get('values', [])
    return values

def sync_accounts_for_network(db: Session, network_name: str):
    network = db.query(Network).filter(Network.name == network_name).first()
    if not network:
        logger.error(f"Network '{network_name}' not found in DB.")
        return

    rows = get_sheet_values(network_name) 
    existing_urls = set(acc.url for acc in db.query(Account).filter(Account.network_id == network.id).all())

    new_accounts = []
    for row in rows:
        if not row:
            continue
        url = row[0].strip()
        if url and url not in existing_urls:
            new_accounts.append(Account(url=url, network_id=network.id, just_added=True))
            existing_urls.add(url)

    if new_accounts:
        db.add_all(new_accounts)
        db.commit()
        logger.info(f"Added {len(new_accounts)} new accounts to network '{network_name}'")
    else:
        logger.info(f"No new accounts found for network '{network_name}'")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.warning("Usage: python sync.py NETWORK_NAME")
        sys.exit(1)
    network_name = sys.argv[1]
    with SessionLocal() as db:
        sync_accounts_for_network(db, network_name)
