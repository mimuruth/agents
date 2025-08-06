
'''
Here's a combined view that demonstrates:
   - ✅ Creating coroutine objects
   - ✅ Starting tasks concurrently using asyncio.create_task(...)
   - ✅ Streaming results as they complete using asyncio.as_completed(...)

   - ✅ Then collecting all results using asyncio.gather(...) at the end
   
   
This pattern is useful when you:
   - Want to process early results immediately (e.g., display to user)
   - But still collect all final results together

'''

import asyncio
import time

# Simulated async task with variable delays
async def sleeper(name, delay):
    print(f"[{name}] coroutine created")
    await asyncio.sleep(delay)
    print(f"[{name}] completed after {delay}s")
    return f"{name} done"

async def main():
    start = time.time()

    # Step 1: Define coroutine functions
    tasks = [
        asyncio.create_task(sleeper("task1", 2)),
        asyncio.create_task(sleeper("task2", 1)),
        asyncio.create_task(sleeper("task3", 3)),
    ]
    print(f"🌀 Tasks created but not yet awaited. Elapsed: {time.time() - start:.2f}s")

    # Step 2: Stream results as each task completes (as_completed)
    print("\n📡 Streaming early results as they complete:\n")
    completed_results = []
    for task in asyncio.as_completed(tasks):
        result = await task
        elapsed = time.time() - start
        print(f"✔️  {result} at +{elapsed:.2f}s")
        completed_results.append(result)

    # Step 3: (Optional) gather all results for summary
    print("\n📦 Gathering all task results using asyncio.gather()")
    all_results = await asyncio.gather(*tasks)
    print(f"📊 Final result list (in order of original tasks): {all_results}")

    print(f"\n✅ All done in {time.time() - start:.2f}s")

asyncio.run(main())

