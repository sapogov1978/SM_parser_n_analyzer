from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import asyncio
from db.models import Network, Post
from db.db import SessionLocal, get_db
from utl.logging import logger


router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/posts/save")
def save_posts(payload: dict, db: Session = Depends(get_db)):
    for post in payload["posts"]:
        if not db.query(Post).filter(Post.url == post["url"]).first():
            db.add(Post(**post))
    db.commit()
    return {"status": "ok"}


@router.post("/sync_posts/{network_id}")
async def sync_posts_for_network(network_id: int):
    db = SessionLocal()

    network = db.query(Network).filter(Network.id == network_id).first()
    if not network:
        return {"status": "error", "details": f"Network with id {network_id} not found"}

    name = network.name.lower()

    script_map = {
        "instagram": "parser/instagram.js",
        "tiktok": "parser/tiktok.js",
        "youtube": "parser/youtube.js",
        # другие сети по мере необходимости
    }

    script_path = script_map.get(name)
    if not script_path:
        return {"status": "error", "details": f"No parser defined for network '{name}'"}

    proc = await asyncio.create_subprocess_exec(
        "node", script_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error(f"{name} parser failed: {stderr.decode()}")
        return {"status": "error", "details": stderr.decode()}

    return {"status": "ok"}
