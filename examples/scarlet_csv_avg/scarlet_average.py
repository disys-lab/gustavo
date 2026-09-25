import os
import time
import uuid
import logging
import numpy as np


# ============================================================
# Suppress known harmless Scarlet / Redis log noise
# ============================================================

class ScarletNoiseFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()

        suppressed_messages = (
            "SCARLET_CONFIG_FILE not specified",
            "Failed to enable maintenance notifications",
        )

        return not any(
            text in message
            for text in suppressed_messages
        )


console_handler = logging.StreamHandler()
console_handler.addFilter(ScarletNoiseFilter())

logging.basicConfig(
    level=logging.WARNING,
    handlers=[console_handler],
    force=True,
)

# Redis/urllib3 DEBUG messages are not useful for this experiment
logging.getLogger("redis").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


# ============================================================
# Configuration
# ============================================================

CSV_FILE = os.environ.get(
    "CSV_FILE",
    "/data/input.csv"
)

SCARLET_NAME = os.environ.get(
    "SCARLET_NAME",
    "scarlet_csv_avg_once"
)

NODE_ID_FILE = os.environ.get(
    "NODE_ID_FILE",
    "/data/.scarlet_node_id"
)

MIN_NODES = int(
    os.environ.get("MIN_NODES", "2")
)

HEARTBEAT_SECONDS = float(
    os.environ.get("HEARTBEAT_SECONDS", "2")
)

NODE_TTL_SECONDS = int(
    os.environ.get("NODE_TTL_SECONDS", "10")
)

DISCOVERY_STABLE_SECONDS = float(
    os.environ.get("DISCOVERY_STABLE_SECONDS", "15")
)


# ============================================================
# Persistent node identity
# ============================================================

def get_or_create_node_id():

    node_directory = os.path.dirname(NODE_ID_FILE)

    if not os.path.isdir(node_directory):
        raise RuntimeError(
            f"Node identity directory does not exist: "
            f"{node_directory}. Check /data mount."
        )

    if os.path.exists(NODE_ID_FILE):

        with open(NODE_ID_FILE, "r") as f:
            node_id = f.read().strip()

        if node_id:
            return node_id

    new_id = f"node-{uuid.uuid4().hex}"

    try:

        with open(NODE_ID_FILE, "x") as f:
            f.write(new_id)

        return new_id

    except FileExistsError:

        with open(NODE_ID_FILE, "r") as f:
            node_id = f.read().strip()

        if not node_id:
            raise RuntimeError(
                f"Node identity file is empty: {NODE_ID_FILE}"
            )

        return node_id


NODE_ID = get_or_create_node_id()


# ============================================================
# Configure Scarlet before Mapper creation
# ============================================================

os.environ["NODE_ADDRESS"] = NODE_ID
os.environ["SCARLET_DATA_EXPIRY"] = str(NODE_TTL_SECONDS)


from scarlets.core.Mapper import Mapper


mapper = Mapper(
    SCARLET_NAME,
    description="One-time distributed CSV averaging experiment"
)


if mapper.super.address != NODE_ID:
    raise RuntimeError(
        f"Scarlet identity mismatch. "
        f"Expected {NODE_ID}, got {mapper.super.address}"
    )


# ============================================================
# Read CSV ONCE
# ============================================================

if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(
        f"CSV file was not found: {CSV_FILE}"
    )


local_array = np.loadtxt(
    CSV_FILE,
    delimiter=","
)

local_array = np.asarray(
    local_array,
    dtype=float
).reshape(-1)


print("=" * 70, flush=True)
print("SCARLET DISTRIBUTED CSV AVERAGE - ONE-TIME VERSION", flush=True)
print(f"Node ID        : {NODE_ID}", flush=True)
print(f"CSV file       : {CSV_FILE}", flush=True)
print(f"Local array    : {local_array}", flush=True)
print(f"Scarlet name   : {SCARLET_NAME}", flush=True)
print("=" * 70, flush=True)


# ============================================================
# Publish helper
# ============================================================

def publish_local_array():

    chunks, success, error = mapper.Map(
        local_array,
        key=NODE_ID
    )

    if (
        not success
        or not chunks
        or not all(bool(chunk) for chunk in chunks)
    ):
        raise RuntimeError(
            f"Could not publish local array. "
            f"success={success}, "
            f"chunks={chunks}, "
            f"error={error}"
        )


publish_local_array()

print(
    f"[{NODE_ID}] Array published successfully.",
    flush=True
)


# ============================================================
# Automatic node discovery
# ============================================================

previous_nodes = set()
stable_since = None
values = {}


while True:

    # Refresh TTL, but DO NOT reread CSV.
    publish_local_array()

    values, success, error = mapper.AllGather()

    if not success:

        print(
            f"[{NODE_ID}] AllGather failed: {error}",
            flush=True
        )

        stable_since = None
        time.sleep(HEARTBEAT_SECONDS)
        continue


    current_nodes = set(values.keys())

    print(
        f"[{NODE_ID}] Active nodes ({len(current_nodes)}): "
        f"{sorted(current_nodes)}",
        flush=True
    )


    if len(current_nodes) < MIN_NODES:

        print(
            f"[{NODE_ID}] Waiting for at least "
            f"{MIN_NODES} nodes...",
            flush=True
        )

        previous_nodes = current_nodes
        stable_since = None

        time.sleep(HEARTBEAT_SECONDS)
        continue


    if current_nodes != previous_nodes:

        print(
            f"[{NODE_ID}] Membership changed. "
            f"Restarting stability timer.",
            flush=True
        )

        previous_nodes = current_nodes
        stable_since = time.time()


    elif stable_since is None:

        stable_since = time.time()


    stable_for = time.time() - stable_since

    print(
        f"[{NODE_ID}] Membership stable for "
        f"{stable_for:.1f}/"
        f"{DISCOVERY_STABLE_SECONDS:.1f} sec",
        flush=True
    )


    if stable_for >= DISCOVERY_STABLE_SECONDS:
        break


    time.sleep(HEARTBEAT_SECONDS)


# ============================================================
# Calculate average ONCE
# ============================================================

active_nodes = sorted(values.keys())

arrays = [
    np.asarray(values[node], dtype=float).reshape(-1)
    for node in active_nodes
]


sizes = {
    len(array)
    for array in arrays
}


if len(sizes) != 1:
    raise ValueError(
        f"Nodes supplied different array sizes: {sizes}"
    )


average = np.mean(
    np.vstack(arrays),
    axis=0
)


print("", flush=True)
print("=" * 70, flush=True)
print(
    f"ACTIVE PARTICIPANTS = {len(active_nodes)}",
    flush=True
)

for node in active_nodes:
    print(
        f"{node}: {np.asarray(values[node])}",
        flush=True
    )

print("", flush=True)
print(f"AVERAGE = {average}", flush=True)
print("=" * 70, flush=True)


# ============================================================
# Keep node alive / refresh TTL
# CSV is intentionally NOT reread
# ============================================================

while True:

    try:
        publish_local_array()

    except Exception as exc:
        print(
            f"[{NODE_ID}] Heartbeat failed: {exc}",
            flush=True
        )

    time.sleep(HEARTBEAT_SECONDS)