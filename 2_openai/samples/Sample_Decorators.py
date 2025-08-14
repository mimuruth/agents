import functools

def logger(func):
    print("step 2")
    @functools.wraps(func)            # keep original name/docstring
    def wrapper(*args, **kwargs):
        print("step 3")
        print(f"→ calling {func.__name__} with args={args}, kwargs={kwargs}")
        print("step 4")
        result = func(*args, **kwargs)
        print("step 5")
        print(f"← {func.__name__} returned {result!r}")
        print("step 6")
        return result
    print("step 7")
    return wrapper

@logger
def add(a, b):
    print("step 1")
    return a + b

add(2, 3)