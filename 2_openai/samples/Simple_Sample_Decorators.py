
import functools

def logger(func):
    print("[step 1 – decorate] logger called for:", func.__name__)
    @functools.wraps(func)  # keep original name/docstring
    def wrapper(*args, **kwargs):
        print("[step 3 – call] wrapper entered")
        print(f"[step 4 – call] about to call {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"[step 6 – call] {func.__name__} returned {result!r}")
        print("[step 7 – call] wrapper exiting")
        return result
    print("[step 2 – decorate] logger returning wrapper")
    return wrapper

@logger
def add(a, b):
    print("[step 5 – func ] inside add()")
    return a + b

# Call site
add(2, 3)
