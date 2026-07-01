import os

dirs = [
    "frontend/components",
    "frontend/hooks",
    "frontend/lib",
    "frontend/services",
    "frontend/styles"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, ".gitkeep"), "w") as f:
        pass

print("Successfully created extra frontend directories.")
