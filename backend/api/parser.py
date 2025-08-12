from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import asyncio
import json

from db.models import Network, Account
from db.db import get_db
from utl.logging import logger

router = APIRouter(prefix="/parser")

async def run_parser_script(network_name: str, accounts_data: list):
    script_map = {
        "instagram": "parser/instagram.js",
        "tiktok": "parser/tiktok.js", 
        "youtube": "parser/youtube.js",
    }
    
    script_path = script_map.get(network_name.lower())
    if not script_path:
        return {"status": "error", "details": f"No parser defined for network '{network_name}'"}
    
    try:
        accounts_json = json.dumps(accounts_data)
        
        proc = await asyncio.create_subprocess_exec(
            "node", script_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate(input=accounts_json.encode())
        
        if proc.returncode != 0:
            logger.error(f"{network_name} parser failed: {stderr.decode()}")
            return {"status": "error", "details": stderr.decode()}
        
        logger.info(f"{network_name} parser completed successfully")
        return {"status": "success", "output": stdout.decode()}
        
    except Exception as e:
        logger.error(f"Failed to run {network_name} parser: {e}")
        return {"status": "error", "details": str(e)}


@router.post("/sync_posts/{network_id}")
async def sync_posts_for_network(network_id: int, db: Session = Depends(get_db)):
    try:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            raise HTTPException(status_code=404, detail="Network not found")
        
        accounts = db.query(Account).filter(Account.network_id == network_id).all()
        
        if accounts:
            accounts_data = [{
                "id": acc.id,
                "url": acc.url,
            } for acc in accounts]
            
            logger.info(f"Manual sync started for {len(accounts_data)} {network.name} accounts")
            result = await run_parser_script(network.name, accounts_data)
            
            if result["status"] == "error":
                logger.error(f"Parser failed for {network.name}: {result.get('details')}")
        
        return RedirectResponse(url=f"/networks/network/{network_id}", status_code=303)
        
    except Exception as e:
        logger.error(f"Manual sync for network {network_id} failed: {e}")
        return RedirectResponse(url=f"/networks/network/{network_id}", status_code=303)


@router.post("/parse-all")
async def parse_all_accounts(db: Session = Depends(get_db)):
    try:
        networks = db.query(Network).all()
        results = {}
        
        for network in networks:
            accounts = db.query(Account).filter(Account.network_id == network.id).all()
            
            if not accounts:
                continue
                
            accounts_data = [{
                "id": acc.id,
                "url": acc.url,
            } for acc in accounts]
            
            logger.info(f"Parsing {len(accounts_data)} {network.name} accounts")
            result = await run_parser_script(network.name, accounts_data)
            results[network.name] = result
        
        return {
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Parse all failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-network/{network_name}")
async def parse_network(network_name: str, db: Session = Depends(get_db)):
    try:
        network = db.query(Network).filter(Network.name == network_name.lower()).first()
        if not network:
            raise HTTPException(status_code=404, detail="Network not found")
        
        accounts = db.query(Account).filter(Account.network_id == network.id).all()
        
        if not accounts:
            return {
                "status": "no_accounts",
                "message": f"No accounts found for {network_name}"
            }
        
        accounts_data = [{
            "id": acc.id,
            "url": acc.url,
        } for acc in accounts]
        
        logger.info(f"Parsing {len(accounts_data)} {network_name} accounts")
        result = await run_parser_script(network_name, accounts_data)
        
        return {
            "network": network_name,
            "accounts_count": len(accounts_data),
            **result
        }
        
    except Exception as e:
        logger.error(f"Parse {network_name} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))