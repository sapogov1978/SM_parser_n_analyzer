from sqlalchemy.orm import Session

from utl.logging import logger
from db.db import SessionLocal
from db.models import Network, Account, Post
from api.api_globals import client

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

def calculate_scores_and_blacklist(db: Session, network_id: int, blacklist_percentage: float):
    accounts = db.query(Account).filter(Account.network_id == network_id).all()

    for acc in accounts:
        posts = db.query(Post).filter(Post.account_id == acc.id).all()
        scores = []
        for post in posts:
            if post.views == 0:
                continue
            engagement_rate = (post.likes + post.comments) / post.views
            score = 0
            if acc.followers > 0:
                score = (post.views / (acc.followers + 100)) * engagement_rate
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0
        acc.score = avg_score  # Добавьте поле score в модель Account, если его нет

    db.commit()

    scores_sorted = sorted(acc.score for acc in accounts)
    index = int(blacklist_percentage * len(scores_sorted))
    threshold_score = scores_sorted[index] if index < len(scores_sorted) else 0

    for acc in accounts:
        acc.blacklisted = acc.score < threshold_score  # Добавьте поле blacklisted в модель Account

    db.commit()
