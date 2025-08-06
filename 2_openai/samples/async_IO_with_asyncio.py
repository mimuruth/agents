
import asyncio
import random

async def compute_square(x: int) -> int:
    await asyncio.sleep(random.uniform(0.5, 1.0))
    return x * x

async def main():
    square = await compute_square(7)
    print(f"The square result is {square}")

if __name__ == "__main__":
    asyncio.run(main())



print("\n\n======================================================\n\n")


'''
Here’s a complete, minimal example demonstrating how to use async def, await, and asyncio.gather() in Python.
This will help you test and understand asynchronous execution.

🔍 What This Does
   - Each async function simulates "processing" using asyncio.sleep().
   - await is used to get the result of a coroutine.
   - asyncio.gather() runs all tasks concurrently.
   - Output shows how asynchronous execution works in Python.

'''

# Example with Simulated Work Using asyncio.sleep()

import asyncio
import random

# Sample async function that simulates processing
async def do_some_processing() -> str:
    await asyncio.sleep(random.uniform(0.5, 1.5))
    return "Result from do_some_processing"

async def do_other_processing() -> str:
    await asyncio.sleep(random.uniform(0.5, 1.5))
    return "Result from do_other_processing"

async def do_yet_other_processing() -> str:
    await asyncio.sleep(random.uniform(0.5, 1.5))
    return "Result from do_yet_other_processing"

# Main function to run all async code
async def main():
    print("Calling one coroutine...")
    my_coroutine = do_some_processing()
    my_result = await my_coroutine
    print("Single coroutine result:", my_result)

    print("\nCalling multiple coroutines in parallel...")
    results = await asyncio.gather(
        do_some_processing(),
        do_other_processing(),
        do_yet_other_processing()
    )

    print("All results from gather:")
    for idx, res in enumerate(results, 1):
        print(f"  Result {idx}: {res}")

# Run the main async function
if __name__ == "__main__":
    asyncio.run(main())




print("\n\n======================================================\n\n")



'''
async functions that simulate real, meaningful processing and return actual results, not just placeholder strings.

💡 Highlights
   - compute_square(): Simulates a CPU-bound calculation with a delay.
   - fetch_user_name(): Simulates data lookup with network delay.
   - reverse_text(): Does basic string manipulation asynchronously.
   - asyncio.gather(): Runs all three in parallel, giving real, traceable output.

'''

import asyncio
import random
import time

# Async function that simulates computing a square
async def compute_square(x: int) -> int:
    await asyncio.sleep(random.uniform(0.5, 1.0))  # Simulate I/O delay
    return x * x

# Async function that fetches data from a dictionary (like a DB)
async def fetch_user_name(user_id: int) -> str:
    await asyncio.sleep(random.uniform(0.3, 0.7))  # Simulate network latency
    fake_db = {1: "Alice", 2: "Bob", 3: "Charlie"}
    return fake_db.get(user_id, "Unknown")

# Async function that reverses a string
async def reverse_text(text: str) -> str:
    await asyncio.sleep(random.uniform(0.2, 0.5))  # Simulate small task
    return text[::-1]

# Main async function
async def main():
    print("➡️ Running a single coroutine...")
    single_result = await compute_square(7)
    print(f"🔹 Square result: {single_result}")

    print("\n➡️ Running multiple coroutines in parallel with asyncio.gather...")
    results = await asyncio.gather(
        compute_square(5),
        fetch_user_name(2),
        reverse_text("AsyncIO is powerful!")
    )

    print("🔹 Results from gather:")
    print(f"  Square of 5: {results[0]}")
    print(f"  User name for ID 2: {results[1]}")
    print(f"  Reversed text: {results[2]}")

# Run the async main
if __name__ == "__main__":
    asyncio.run(main())



print("\n\n======================================================\n\n")



from pathlib import Path

sample_text = """Hello Async World!
This file is used to test asynchronous file reading.
Each line in this file has meaningful content.
Feel free to modify this content as needed.
Enjoy learning asyncio!
"""

Path("sample.txt").write_text(sample_text)




'''
Here's a complete upgraded version of the second example that includes:

   - ✅ Logging
   - ✅ Exception handling
   - ✅ File I/O
   - ✅ Real API call (via httpx — async-friendly HTTP client)
   
Notes
   - httpx.AsyncClient makes a real API call (to a test public API: https://jsonplaceholder.typicode.com).
   - asyncio.to_thread(...) is used to safely run blocking file I/O inside async code.
   - Exception handling ensures errors are logged and don’t crash the app.
   - Logging gives structured, timestamped output.
   

📁 Sample sample.txt
To test the file read/reverse part, create a file called sample.txt with some content:
   - Hello Async World!

'''

import asyncio
import random
import logging
from pathlib import Path
import httpx  # Make sure to install: pip install httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Async function that simulates computing a square
async def compute_square(x: int) -> int:
    await asyncio.sleep(random.uniform(0.5, 1.0))
    result = x * x
    logging.info(f"Computed square of {x}: {result}")
    return result

# Async function that fetches real user data from an API
async def fetch_user_data(user_id: int) -> dict:
    url = f"https://jsonplaceholder.typicode.com/users/{user_id}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            user_data = response.json()
            logging.info(f"Fetched user data: {user_data['name']}")
            return user_data
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error while fetching user: {e}")
        except httpx.RequestError as e:
            logging.error(f"Request error while fetching user: {e}")
    return {}

# Async function that reads a file and reverses its content
async def reverse_file_contents(file_path: str) -> str:
    try:
        content = await asyncio.to_thread(Path(file_path).read_text)
        reversed_content = content[::-1]
        logging.info(f"Reversed content from file '{file_path}'")
        return reversed_content
    except FileNotFoundError:
        logging.warning(f"File not found: {file_path}")
        return ""
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return ""

# Main async function
async def main():
    logging.info("Starting all tasks in parallel...")
    
    results = await asyncio.gather(
        compute_square(9),
        fetch_user_data(3),
        reverse_file_contents("sample.txt"),  # Create this file locally for test
        return_exceptions=True  # Prevent single failure from breaking the gather
    )

    logging.info("Finished all tasks. Results:")
    for i, res in enumerate(results, 1):
        if isinstance(res, Exception):
            logging.error(f"Task {i} raised an error: {res}")
        else:
            logging.info(f"Task {i} result: {res}")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())


'''
You can create the 📄 sample.txt file by running a simple Python snippet (optional):


from pathlib import Path

sample_text = """Hello Async World!
This file is used to test asynchronous file reading.
Each line in this file has meaningful content.
Feel free to modify this content as needed.
Enjoy learning asyncio!
"""

Path("sample.txt").write_text(sample_text)


'''











