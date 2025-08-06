
'''
Updated script with all enhancements:
✅ Summary of Enhancements
   - ✅ Writes results to a file using aiofiles
   - ✅ Applies timeouts per task using asyncio.wait_for()
   - ✅ Uses AsyncExitStack for managing multiple async resources (API client and output file)
   - ✅ Keeps: structured logging (structlog), retry logic (backoff), parallel API calls, CSV + JSON input


🔍 Advanced Usage Highlights
   - AsyncExitStack ensures all resources (e.g., HTTP client, file handles) are cleaned up properly.
   - asyncio.wait_for() wraps each API call with a timeout guard.
   - aiofiles.open() is used with append ('a') mode to save results safely per task.
   - backoff handles automatic retries for transient network errors.


Updated script with clean printing using tabulate

'''


import asyncio
import csv
import json
import httpx
import aiofiles
import backoff
import structlog
from pathlib import Path
from contextlib import AsyncExitStack
from tabulate import tabulate
from contextlib import AsyncExitStack

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

# Read user info from CSV file
async def read_user_csv(path: str) -> list:
    async with aiofiles.open(path, mode='r') as f:
        lines = await f.readlines()
    reader = csv.DictReader(lines)
    return [row for row in reader]

# Retryable async API call
@backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3)
async def fetch_user(client: httpx.AsyncClient, base_url: str, user_id: str) -> dict:
    response = await client.get(f"{base_url}/{user_id}")
    response.raise_for_status()
    return response.json()

# Orchestrates a single user fetch and write
async def fetch_and_store_user(user, config, client, output_file):
    user_id = user["user_id"]
    try:
        # Apply timeout to each task
        result = await asyncio.wait_for(
            fetch_user(client, config["api_base_url"], user_id),
            timeout=config["timeout_per_task"]
        )
        async with aiofiles.open(output_file, mode='a') as f:
            await f.write(json.dumps(result) + "\n")
        log.info("Fetched and saved user", user_id=user_id, name=result.get("name"))
        return result
    except asyncio.TimeoutError:
        log.warning("Task timed out", user_id=user_id)
    except Exception as e:
        log.error("Failed to fetch or store user", user_id=user_id, error=str(e))
    return {}

# Main async runner
async def main():
    config = await load_config("config.json")
    users = await read_user_csv("users.csv")
    log.info("Starting parallel user fetch tasks", count=len(users))

    async with AsyncExitStack() as stack:
        client = await stack.enter_async_context(httpx.AsyncClient(timeout=5.0))
        # Clear or create output file
        output_file = config["output_file"]
        await stack.enter_async_context(aiofiles.open(output_file, mode='w'))

        tasks = [
            fetch_and_store_user(user, config, client, output_file)
            for user in users
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    log.info("Completed all user tasks", success_count=len([r for r in results if isinstance(r, dict)]))

# Entry point
if __name__ == "__main__":
    try:
        with open("user_results.json", encoding="utf-8") as result_file:
            user_results = [json.loads(line) for line in result_file]
            
            # Prepare data for tabulate
            table = [
                {
                    "ID": user["id"],
                    "Name": user["name"],
                    "Email": user["email"],
                    "Company": user["company"]["name"]
                }
                for user in user_results
            ]

            print("\n📄 Previously saved results:")
            print(tabulate(table, headers="keys", tablefmt="fancy_grid"))

            print("\n\n--------------------\n\n")
    except FileNotFoundError:
        print("user_results.json not found. Starting fresh.")
        print("\n\n--------------------\n\n")
        
    asyncio.run(main())


