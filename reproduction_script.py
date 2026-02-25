from taskchain import Chain, Task, ExecutionContext
import sys

# 1. Define your tasks
def extract(ctx: ExecutionContext):
    print("Extracting data...")
    ctx.data["raw"] = [1, 2, 3, 4, 5]
    return ctx.data["raw"]

def transform(ctx: ExecutionContext):
    print("Transforming data...")
    data = ctx.data["raw"]
    ctx.data["processed"] = [x * 2 for x in data]
    return ctx.data["processed"]

def load(ctx: ExecutionContext):
    print(f"Loading data: {ctx.data['processed']}")
    return True

# 2. Create the Chain (Workflow)
pipeline = Chain("ETL_Pipeline", [
    Task("Extract", extract),
    Task("Transform", transform),
    Task("Load", load)
])

# 3. Execute
initial_context = ExecutionContext(data={})
result = pipeline.execute(initial_context)

if result.status == "SUCCESS":
    print("Pipeline completed successfully!")
else:
    print(f"Pipeline failed: {result.errors}")
    sys.exit(1)
