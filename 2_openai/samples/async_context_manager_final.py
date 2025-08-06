
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
   

Updated and cleaned-up code:

✅ Fixes Included:
   - Removed unused Path import
   - Renamed shadowed variables (f, users)
   - Specified encoding in open()
   - Added error type to log message
   - Kept structlog and async patterns intact
   
Updated script with clean printing using tabulate

'''

import asyncio
import csv
import json
import httpx
import aiofiles
import backoff
import structlog
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
    async with aiofiles.open(path, mode='r', encoding='utf-8') as config_file:
        content = await config_file.read()
    return json.loads(content)

# Read user info from CSV file
async def read_user_csv(path: str) -> list:
    async with aiofiles.open(path, mode='r', encoding='utf-8') as csv_file:
        lines = await csv_file.readlines()
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
        result = await asyncio.wait_for(
            fetch_user(client, config["api_base_url"], user_id),
            timeout=config["timeout_per_task"]
        )
        if isinstance(result, dict):
            async with aiofiles.open(output_file, mode='a', encoding='utf-8') as out_file:
                await out_file.write(json.dumps(result) + "\n")
            log.info("Fetched and saved user", user_id=user_id, name=result.get("name"))
            return result
    except asyncio.TimeoutError:
        log.warning("Task timed out", user_id=user_id)
    except Exception as e:
        log.error("Failed to fetch or store user", user_id=user_id, error=str(e), error_type=str(type(e)))
    return {}

# Main async runner
async def main():
    config = await load_config("config.json")
    user_list = await read_user_csv("users.csv")
    log.info("Starting parallel user fetch tasks", count=len(user_list))

    async with AsyncExitStack() as stack:
        client = await stack.enter_async_context(httpx.AsyncClient(timeout=5.0))
        output_file = config["output_file"]
        await stack.enter_async_context(aiofiles.open(output_file, mode='w', encoding='utf-8'))

        tasks = [
            fetch_and_store_user(user, config, client, output_file)
            for user in user_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    log.info("Completed all user tasks", success_count=len([r for r in results if isinstance(r, dict)]))

# Entry point
if __name__ == "__main__":
    try:
        with open("user_results.json", encoding="utf-8") as result_file:
            user_results = []
            for line in result_file:
                line = line.strip()
                if not line:
                    continue
                try:
                    user_results.append(json.loads(line))
                except json.JSONDecodeError:
                    log.warning("Skipping invalid JSON line", line=line)

            if user_results:
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
            else:
                print("user_results.json is empty or contained only invalid lines.")

    except FileNotFoundError:
        print("user_results.json not found. Starting fresh.")
        print("\n\n--------------------\n\n")

    asyncio.run(main())
