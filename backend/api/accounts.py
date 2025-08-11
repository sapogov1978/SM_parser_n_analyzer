from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse

from db.db import SessionLocal
from db.models import Network, Account
from db.db import get_db
from api.api_globals import templates

router = APIRouter(prefix="/networks/{network_id}/accounts")

@router.get("/", response_class=HTMLResponse)
def show_accounts_for_network(request: Request, network_id: int):
    with SessionLocal() as db:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

        accounts = db.query(Account).filter(Account.network_id == network.id).order_by(Account.score.desc()).all()

        account_stats = [{
            "account": acc,
            "score": acc.score if hasattr(acc, "score") else 0,
            "blacklisted": getattr(acc, "blacklisted", False)
        } for acc in accounts]

        return templates.TemplateResponse("accounts.html", {
            "request": request,
            "network": network,
            "accounts": account_stats
        })

@router.get("/for-parsing")
def get_accounts_for_parsing(db: Session = Depends(get_db)):
    accs = db.query(Account).filter(
        Account.network.has(name="instagram")
    ).all()
    return [{
        "id": a.id,
        "url": a.url,
        "network_id": a.network_id
    } for a in accs]

@router.post("/{account_id}/followers")
def update_followers(account_id: int, payload: dict, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404)
    acc.followers = payload["followers"]
    db.commit()
    return {"status": "ok"}

@router.post("/{account_id}/parsed")
def mark_account_parsed(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if acc:
        acc.just_added = False
        db.commit()
    return {"status": "ok"}
