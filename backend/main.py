import os
import asyncio

from datetime import datetime, timedelta
from fastapi import FastAPI, status
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from db.db import init_db, wait_for_db
from api import networks, accounts, posts, posts_utl, parser
from api.accounts_utl import sync_accounts_from_google_sheets
from utl.logging import logger


async def nightly_sync_task():
    while True:
        now = datetime.now()
        midnight = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
        seconds_until_midnight = (midnight - now).total_seconds()
        await asyncio.sleep(seconds_until_midnight)

        try:
            logger.info("🌙 Daily tasks started")
            await asyncio.to_thread(sync_accounts_from_google_sheets)
            await posts_utl.parse_instagram_posts()
            logger.info("✅ Daily tasks completed")
        except Exception:
            logger.exception("❌ Nightly sync failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("🔄 Initializing database...")
        wait_for_db()
        init_db()
        logger.info("✅ Database initialized")
    except Exception:
        logger.exception("❌ Database initialization failed")
        raise
    
    task = asyncio.create_task(nightly_sync_task())
    
    yield
    
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
app.include_router(networks.router)
app.include_router(accounts.router)
app.include_router(posts.router)
app.include_router(parser.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/networks/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/sync_accounts")
def manual_sync():
    try:
        sync_accounts_from_google_sheets()
    except Exception:
        logger.exception("Manual sync failed")
    return RedirectResponse(url="/networks/", status_code=status.HTTP_303_SEE_OTHER)


# wait_for_db()
# init_db()
