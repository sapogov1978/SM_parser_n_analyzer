from sqlalchemy.orm import Session

from db.models import Network
from utl.logging import logger
from db.db import SessionLocal
from db.models import Network, Account
from api.api_globals import client

def get_or_create_other(db: Session):
    other = db.query(Network).filter(Network.name == "other").first()
    if not other:
        other = Network(name="other", domain="other.local")
        db.add(other)
        db.commit()
        db.refresh(other)
    return other

def sync_accounts_from_google_sheets():
    logger.info("Starting sync with Google Sheets")

    with SessionLocal() as db:
        try:
            sheet = client.open("IVSisters_Links")
            sheet_names = sheet.worksheets()
            sheet_names = [w.title for w in sheet_names]
        except Exception as e:
            logger.error(f"Cannot open Google sheet: {e}")
            return

        for sheet_name in sheet_names:
            network = db.query(Network).filter(Network.name == sheet_name).first()
            if not network:
                network = Network(name=sheet_name, domain=sheet_name+".com")
                db.add(network)
                db.commit()
                db.refresh(network)

        for network in db.query(Network).all():
            try:
                sheet = client.open("IVSisters_Links").worksheet(network.name)
                rows = sheet.col_values(1)
            except Exception as e:
                logger.warning(f"Sheet not found for network {network.name}: {e}")
                continue

            for url in rows:
                url = url.strip()
                if not url:
                    continue

                exists = db.query(Account).filter(Account.url == url).first()
                if not exists:
                    db.add(Account(
                        url=url,
                        network_id=network.id,
                        just_added=True
                    ))

        db.commit()
    logger.info("Finished sync with Google Sheets")
