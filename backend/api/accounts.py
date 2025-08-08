from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse

from db.db import SessionLocal
from db.models import Network, Account, Post
from db.db import get_db
from api.api_globals import templates, BLACKLIST_PERCENTAGE

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get("/network/{network_id}", response_class=HTMLResponse)
def show_accounts_for_network(request: Request, network_id: int):
    with SessionLocal() as db:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

        accounts = db.query(Account).filter(Account.network_id == network.id).all()
        account_stats = []

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

            account_stats.append({
                "account": acc,
                "score": avg_score,
                "posts": posts,
            })

        if account_stats:
            scores_sorted = sorted([a["score"] for a in account_stats])
            index = int(BLACKLIST_PERCENTAGE * len(scores_sorted))
            threshold_score = scores_sorted[index] if index < len(scores_sorted) else 0

            for stat in account_stats:
                stat["account"].blacklisted = stat["score"] < threshold_score

        db.commit()

        sorted_accounts = sorted(account_stats, key=lambda x: x["score"], reverse=True)

        return templates.TemplateResponse("accounts.html", {
            "request": request,
            "network": network,
            "accounts": sorted_accounts
        })


@router.get("/accounts/for-parsing")
def get_accounts_for_parsing(db: Session = Depends(get_db)):
    accs = db.query(Account).filter(
        Account.network.has(name="instagram")
    ).all()
    return [{
        "id": a.id,
        "url": a.url,
        "network_id": a.network_id
    } for a in accs]

@router.post("/accounts/{account_id}/followers")
def update_followers(account_id: int, payload: dict, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404)
    acc.followers = payload["followers"]
    db.commit()
    return {"status": "ok"}

@router.post("/accounts/{account_id}/parsed")
def mark_account_parsed(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if acc:
        acc.just_added = False
        db.commit()
    return {"status": "ok"}
