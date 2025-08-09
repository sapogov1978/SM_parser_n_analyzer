from fastapi import APIRouter, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from urllib.parse import urlparse

from db.db import SessionLocal
from db.models import Network, Account, Post
from utl.logging import logger
from api.api_globals import templates, LOGOS, BLACKLIST_PERCENTAGE
from api.networks_utl import get_or_create_other, sync_accounts_from_google_sheets

router = APIRouter(prefix="/networks", tags=["Networks"])

@router.get("/", response_class=HTMLResponse)
def show_networks(request: Request):
    db = SessionLocal()
    networks = db.query(Network).all()

    network_data = []
    for net in networks:
        accounts_count = db.query(Account).filter_by(network_id=net.id).count()
        posts_count = db.query(Post).filter_by(network_id=net.id).count()
        logo = LOGOS.get(net.domain, None)
        network_data.append({
            "id": net.id,
            "name": net.name,
            "accounts_count": accounts_count,
            "posts_count": posts_count,
            "logo": logo
        })

    return templates.TemplateResponse("networks.html", {"request": request, "networks": network_data})


@router.post("/remove_network")
def remove_network(network_id: int = Form(...)):
    with SessionLocal() as db:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        other = get_or_create_other(db)

        for acc in network.accounts:
            acc.network_id = other.id

        for post in network.posts:
            post.network_id = other.id

        db.delete(network)
        db.commit()

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)



@router.post("/add_network")
def add_network(network_name: str = Form(...), domain: str = Form(...)):
    with SessionLocal() as db:
        existing = db.query(Network).filter(Network.domain == domain).first()
        if existing:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        new_network = Network(name=network_name, domain=domain)
        db.add(new_network)
        db.commit()
        db.refresh(new_network)

        other_network = get_or_create_other(db)

        accounts_to_move = db.query(Account).filter(Account.network_id == other_network.id).all()
        for acc in accounts_to_move:
            if urlparse(acc.url).netloc == domain:
                acc.network_id = new_network.id

        db.commit()

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/sync_accounts")
def manual_sync():
    try:
        sync_accounts_from_google_sheets()
    except Exception:
        logger.exception("Manual sync failed")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
