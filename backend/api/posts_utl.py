import asyncio
from utl.logging import logger

async def parse_instagram_posts():
    proc = await asyncio.create_subprocess_exec(
            "node", "parser/instagram.js",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
            )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(f"Parser failed: {stderr.decode()}")
