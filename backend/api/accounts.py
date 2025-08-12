from fastapi import APIRouter, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func

from db.db import SessionLocal
from db.models import Network, Account, Post
from api.api_globals import templates

router = APIRouter(prefix="/networks/{network_id}/accounts")

@router.get("/", response_class=HTMLResponse)
def show_accounts_for_network(request: Request, network_id: int):
    with SessionLocal() as db:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

        accounts = (
            db.query(Account)
            .filter(Account.network_id == network.id)
            .order_by(Account.score.desc().nullslast())
            .all()
        )

        acc_ids = [a.id for a in accounts]
        post_counts = dict(
            db.query(Post.account_id, func.count(Post.id))
              .filter(Post.account_id.in_(acc_ids))
              .group_by(Post.account_id)
              .all()
        )

        view_model = [{
            "account": acc,
            "posts_count": post_counts.get(acc.id, 0),
        } for acc in accounts]

        return templates.TemplateResponse(
            "accounts.html",
            {"request": request, "network": network, "accounts": view_model}
        )

@router.post("/edit")
def edit_account(
    network_id: int,
    account_id: int = Form(...),
    url: str = Form(...),
):
    with SessionLocal() as db:
        account = db.query(Account).filter(Account.id == account_id, Account.network_id == network_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        account.url = url
        db.commit()
    return RedirectResponse(url=f"/networks/{network_id}/accounts", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{account_id}/delete")
def delete_account(network_id: int, account_id: int):
    with SessionLocal() as db:
        account = db.query(Account).filter(Account.id == account_id, Account.network_id == network_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        db.delete(account)
        db.commit()
    return RedirectResponse(url=f"/networks/{network_id}/accounts", status_code=status.HTTP_303_SEE_OTHER)
