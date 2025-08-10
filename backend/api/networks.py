from fastapi import APIRouter, Request, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse, JSONResponse
from urllib.parse import urlparse
from sqlalchemy.exc import SQLAlchemyError

from db.db import SessionLocal
from db.models import Network, Account, Post
from utl.logging import logger
from api.api_globals import templates, LOGOS
from api.networks_utl import get_or_create_other

router = APIRouter(prefix="/networks", tags=["Networks"])

@router.get("/", response_class=HTMLResponse)
def show_networks(request: Request):
    with SessionLocal() as db:
        try:
            networks = db.query(Network).all()

            network_data = []
            for net in networks:
                accounts_count = db.query(Account).filter_by(network_id=net.id).count()
                posts_count = db.query(Post).filter_by(network_id=net.id).count()
                logo = LOGOS.get(net.domain, None)
                network_data.append({
                    "id": net.id,
                    "name": net.name,
                    "domain": net.domain,
                    "accounts_count": accounts_count,
                    "posts_count": posts_count,
                    "logo": logo
                })

            return templates.TemplateResponse("networks.html", {"request": request, "networks": network_data})
        except SQLAlchemyError as e:
            logger.error(f"Database error in show_networks: {e}")
            return templates.TemplateResponse("error.html", {"request": request, "error": "Database error"})

@router.post("/add_network")
def add_network(network_name: str = Form(...), domain: str = Form(...)):
    if not network_name.strip() or not domain.strip():
        return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

    with SessionLocal() as db:
        try:
            existing = db.query(Network).filter(Network.domain == domain.strip()).first()
            if existing:
                return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

            new_network = Network(name=network_name.strip(), domain=domain.strip())
            db.add(new_network)
            db.commit()
            db.refresh(new_network)

            other_network = get_or_create_other(db)

            accounts_to_move = db.query(Account).filter(Account.network_id == other_network.id).all()
            for acc in accounts_to_move:
                if urlparse(acc.url).netloc == domain.strip():
                    acc.network_id = new_network.id

            db.commit()
            logger.info(f"Network {network_name} added successfully")

        except SQLAlchemyError as e:
            logger.error(f"Database error in add_network: {e}")
            db.rollback()

    return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/edit/{network_id}")
def get_network_for_edit(network_id: int):
    with SessionLocal() as db:
        try:
            network = db.query(Network).filter(Network.id == network_id).first()
            if not network:
                raise HTTPException(status_code=404, detail="Network not found")

            return JSONResponse({
                "id": network.id,
                "name": network.name,
                "domain": network.domain
            })
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_network_for_edit: {e}")
            raise HTTPException(status_code=500, detail="Database error")


@router.post("/edit_network")
def edit_network(
        network_id: int = Form(...),
        network_name: str = Form(...),
        domain: str = Form(...)
):
    if not network_name.strip():
        return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

    if not domain.strip():
        return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

    with SessionLocal() as db:
        try:
            network = db.query(Network).filter(Network.id == network_id).first()
            if not network:
                return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

            old_domain = network.domain

            existing = db.query(Network).filter(
                Network.domain == domain.strip(),
                Network.id != network_id
            ).first()
            if existing:
                logger.warning(f"Network with domain {domain} already exists")
                return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

            network.name = network_name.strip()
            network.domain = domain.strip()

            if old_domain != domain.strip():
                other_network = get_or_create_other(db)

                accounts_to_move = db.query(Account).filter(Account.network_id == other_network.id).all()
                for acc in accounts_to_move:
                    if urlparse(acc.url).netloc == domain.strip():
                        acc.network_id = network.id

                network_accounts = db.query(Account).filter(Account.network_id == network.id).all()
                for acc in network_accounts:
                    if urlparse(acc.url).netloc != domain.strip():
                        acc.network_id = other_network.id

            db.commit()
            logger.info(f"Network {network_id} updated successfully")

        except SQLAlchemyError as e:
            logger.error(f"Database error in edit_network: {e}")
            db.rollback()
            return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/remove_network")
def remove_network(network_id: int = Form(...)):
    with SessionLocal() as db:
        try:
            network = db.query(Network).filter(Network.id == network_id).first()
            if not network:
                return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)

            other = get_or_create_other(db)

            for acc in network.accounts:
                acc.network_id = other.id

            for post in network.posts:
                post.network_id = other.id

            db.delete(network)
            db.commit()
            logger.info(f"Network {network_id} removed successfully")

        except SQLAlchemyError as e:
            logger.error(f"Database error in remove_network: {e}")
            db.rollback()

    return RedirectResponse(url="/networks", status_code=status.HTTP_303_SEE_OTHER)