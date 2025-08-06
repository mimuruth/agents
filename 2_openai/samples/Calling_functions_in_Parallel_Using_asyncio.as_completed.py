
'''
Calling an async function like asyncio.sleep(2) returns a coroutine object, which is essentially a placeholder — it does nothing until it is awaited or scheduled with asyncio.create_task() or similar.

To visualize this behavior more clearly, and also incorporate asyncio.as_completed() to demonstrate parallel execution and completion order, here's a better-annotated and enhanced version of your code:

🧠 Key Takeaways
   - Calling sleeper(...) returns a coroutine object — nothing runs yet.
   - Only after asyncio.create_task(...) or await does the coroutine get scheduled and executed.
   - as_completed() shows the true order of task completion, not definition order.
   
   
✅ Summary
   - ✅ This example demonstrates the difference between calling vs awaiting.
   - ✅ It adds visual time gaps and shows when coroutines are created vs when they are actually scheduled.
   - ✅ as_completed() makes it clear which task finishes first — useful when durations vary.

'''

import asyncio
import time

# Simulated async task with an artificial delay
async def sleeper(name, delay):
    print(f"[{name}] coroutine created (but not yet sleeping)")
    await asyncio.sleep(delay)
    print(f"[{name}] woke up after {delay} seconds")
    return name

async def main():
    start = time.time()

    # Create coroutine objects (nothing happens yet)
    coro1 = sleeper("task1", 2)
    coro2 = sleeper("task2", 1)
    print(f"Coroutines created, elapsed = {time.time() - start:.2f}s")

    # Wait one second before scheduling them (they still haven’t executed!)
    await asyncio.sleep(1)
    print(f"Waited before awaiting coroutines, elapsed = {time.time() - start:.2f}s")

    # Now execute them concurrently
    tasks = [asyncio.create_task(c) for c in (coro1, coro2)]

    # Use as_completed to observe order of completion
    for completed in asyncio.as_completed(tasks):
        result = await completed
        print(f"{result} completed at t+{time.time() - start:.2f}s")

    print(f"All done in {time.time() - start:.2f}s")

# Run the main async function
if __name__ == "__main__":
    asyncio.run(main())
