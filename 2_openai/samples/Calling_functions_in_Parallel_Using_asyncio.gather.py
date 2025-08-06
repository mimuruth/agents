
'''
Let's contrast asyncio.gather() with your original scenario and show how it behaves differently from asyncio.as_completed().

✅ Key Difference
   - asyncio.gather(): Runs all tasks concurrently and returns results in the order of the inputs.
   - asyncio.as_completed(): Yields tasks as they complete, regardless of input order.

✅ Visual Example Using asyncio.gather
Below is an annotated version of your function using asyncio.gather() to help visualize coroutine creation, scheduling, and completion:


🧠 Key Takeaways
   - Calling sleeper(...) returns a coroutine object — nothing runs yet.
   - Only after asyncio.create_task(...) or await does the coroutine get scheduled and executed.
   - gather() shows the definition order.
   
   
✅ Summary
   - ✅ This example demonstrates the difference between calling vs awaiting.
   - ✅ It adds visual time gaps and shows when coroutines are created vs when they are actually scheduled.
   - ✅ gather() makes it clear which task finishes first — useful when durations vary.

'''

import asyncio
import time

# Simulated async task
async def sleeper(name, delay):
    print(f"[{name}] coroutine created")
    await asyncio.sleep(delay)
    print(f"[{name}] completed after {delay} seconds")
    return f"{name} done"

async def main():
    start = time.time()

    # Just create coroutine objects (not yet started)
    coro1 = sleeper("task1", 2)
    coro2 = sleeper("task2", 1)
    coro3 = sleeper("task3", 3)
    print(f"Coroutines created, elapsed = {time.time() - start:.2f}s")

    # Await all of them concurrently
    results = await asyncio.gather(coro1, coro2, coro3)
    print(f"\nAll coroutines completed in {time.time() - start:.2f}s")

    # Results are returned in the order of the coroutines
    for idx, res in enumerate(results, 1):
        print(f"Result {idx}: {res}")

asyncio.run(main())







