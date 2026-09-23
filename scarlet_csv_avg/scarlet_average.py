import os
import time
import numpy as np

from scarlets.core.Mapper import Mapper


# ============================================================
# Configuration
# ============================================================

CSV_FILE = os.environ.get(
    "CSV_FILE",
    "/data/input.csv"
)

SCARLET_NAME = os.environ.get(
    "SCARLET_NAME",
    "kazi_csv_average_test1"
)

EXPECTED_NODES = int(
    os.environ.get("EXPECTED_NODES", "2")
)


# ============================================================
# Create Scarlet Mapper
# ============================================================

mapper = Mapper(
    SCARLET_NAME,
    description="Two-node distributed CSV averaging experiment"
)

# Gustavo/Scarlet gives every physical node its own identity.
NODE_ID = mapper.super.address


print("=" * 60, flush=True)
print("Starting Scarlet distributed average experiment", flush=True)
print(f"Node ID      : {NODE_ID}", flush=True)
print(f"CSV file     : {CSV_FILE}", flush=True)
print(f"Scarlet name : {SCARLET_NAME}", flush=True)
print("=" * 60, flush=True)


# ============================================================
# Read LOCAL data
# ============================================================

if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(
        f"CSV file was not found: {CSV_FILE}"
    )

local_array = np.loadtxt(
    CSV_FILE,
    delimiter=","
)

# Make sure we always have a 1-D array
local_array = np.asarray(
    local_array,
    dtype=float
).reshape(-1)


print(
    f"[{NODE_ID}] Local array = {local_array}",
    flush=True
)


# ============================================================
# Publish local array to shared Scarlet
# ============================================================

chunks, success, error = mapper.Map(
    local_array,
    key=NODE_ID
)

if not success:
    raise RuntimeError(
        f"Could not publish local array: {error}"
    )

print(
    f"[{NODE_ID}] Array published to Scarlet/Redis.",
    flush=True
)


# ============================================================
# Wait asynchronously for both devices
# ============================================================

while True:

    values, success, error = mapper.AllGather()

    if not success:
        print(
            f"[{NODE_ID}] AllGather failed: {error}",
            flush=True
        )
        time.sleep(2)
        continue

    print(
        f"[{NODE_ID}] Nodes currently available: "
        f"{list(values.keys())}",
        flush=True
    )

    if len(values) >= EXPECTED_NODES:
        break

    print(
        f"[{NODE_ID}] Waiting for other device...",
        flush=True
    )

    time.sleep(2)


# ============================================================
# Verify same array size
# ============================================================

arrays = [
    np.asarray(value, dtype=float).reshape(-1)
    for value in values.values()
]

sizes = {len(array) for array in arrays}

if len(sizes) != 1:
    raise ValueError(
        f"Nodes provided different array sizes: {sizes}"
    )


# ============================================================
# Calculate distributed average
# ============================================================

combined = np.vstack(arrays)

average = np.mean(
    combined,
    axis=0
)


print("", flush=True)
print("=" * 60, flush=True)
print("ALL NODE DATA RECEIVED", flush=True)

for node, value in values.items():
    print(
        f"{node}: {np.asarray(value)}",
        flush=True
    )

print("", flush=True)
print(f"AVERAGE = {average}", flush=True)
print("=" * 60, flush=True)


# Keep container running so logs remain easy to inspect
while True:
    time.sleep(60)