
'''

Here's a complete, production-style async Python script that demonstrates:

   - ✅ CSV + JSON file processing
   - ✅ Parallel API calls
   - ✅ Retry logic with exponential backoff
   - ✅ Structured logging with structlog in JSON format

Required Dependencies (install first)

pip install httpx structlog aiofiles backoff


'''

import asyncio
import csv
import json
import httpx
import aiofiles
import backoff
import structlog
from pathlib import Path

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
log = structlog.get_logger()

# Load config from JSON file
async def load_config(path: str) -> dict:
    async with aiofiles.open(path, mode='r') as f:
        content = await f.read()
    return json.loads(content)

# Read CSV file with user IDs
async def read_user_csv(path: str) -> list:
    async with aiofiles.open(path, mode='r') as f:
        lines = await f.readlines()

    reader = csv.DictReader(lines)
    return [row for row in reader]

# Retryable async function to call API
@backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3)
async def fetch_user(api_base_url: str, user_id: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{api_base_url}/{user_id}")
        response.raise_for_status()
        return response.json()

# Main orchestrator
async def main():
    config = await load_config("config.json")
    users = await read_user_csv("users.csv")

    log.info("Starting parallel API calls", user_count=len(users))

    async def fetch_and_log(user):
        try:
            user_data = await fetch_user(config["api_base_url"], user["user_id"])
            log.info("User data retrieved", user_id=user["user_id"], name=user_data.get("name"))
            return user_data
        except Exception as e:
            log.error("Failed to fetch user", user_id=user["user_id"], error=str(e))
            return {}

    results = await asyncio.gather(
        *(fetch_and_log(user) for user in users),
        return_exceptions=True
    )

    log.info("All API calls completed", successful=len([r for r in results if isinstance(r, dict)]))

if __name__ == "__main__":
    asyncio.run(main())
    with open("config.json") as f:
        json.load(f)  # Will raise an error if JSON is invalid
