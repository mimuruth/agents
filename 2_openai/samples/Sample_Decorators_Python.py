# Decorators in Python

import time

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function '{func.__name__}' executed in {end_time - start_time:.4f} seconds.")
        return result
    return wrapper


#@timer_decorator
def long_running_function():
    print("Starting long-running computation...")
    start_time = time.time()
    total = sum(range(10_000_000))
    end_time = time.time()
    print(f"Sum computed: {total}")
    print(f"Execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    long_running_function()


