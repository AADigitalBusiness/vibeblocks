import json
from taskchain.core.context import ExecutionContext

def test_repro():
    print("Starting reproduction...")
    # Case 1: JSON is not a dict
    try:
        print("\nTesting Case 1: JSON list...")
        ExecutionContext.from_json("[]")
        print("Case 1 Failed: Should have raised an error but didn't")
    except AttributeError:
        print("Case 1 Passed: Raised AttributeError (but we want a better error)")
    except Exception as e:
        print(f"Case 1 Unexpected error: {type(e).__name__}: {e}")

    # Case 2: JSON is a dict but 'trace' is not a list
    try:
        print("\nTesting Case 2: 'trace' is not a list...")
        ExecutionContext.from_json('{"trace": "not_a_list", "data": {}, "metadata": {}, "completed_steps": []}')
        print("Case 2 Failed: Should have raised an error but didn't")
    except Exception as e:
        print(f"Case 2 Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_repro()
