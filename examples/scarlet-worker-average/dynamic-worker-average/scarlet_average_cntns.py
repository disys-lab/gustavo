import os
import time
import uuid
import hashlib
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
    "scarlet_csv_avg_continuous"
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
# Configure Scarlet
# ============================================================

os.environ["NODE_ADDRESS"] = NODE_ID
os.environ["SCARLET_DATA_EXPIRY"] = str(NODE_TTL_SECONDS)


from scarlets.core.Mapper import Mapper


mapper = Mapper(
    SCARLET_NAME,
    description="Continuous distributed CSV averaging experiment"
)


if mapper.super.address != NODE_ID:
    raise RuntimeError(
        f"Scarlet identity mismatch. "
        f"Expected {NODE_ID}, got {mapper.super.address}"
    )


# ============================================================
# Helpers
# ============================================================

def read_local_array():

    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(
            f"CSV file not found: {CSV_FILE}"
        )

    array = np.loadtxt(
        CSV_FILE,
        delimiter=","
    )

    return np.asarray(
        array,
        dtype=float
    ).reshape(-1)


def publish_local_array(array):

    chunks, success, error = mapper.Map(
        array,
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


def create_state_signature(values):

    digest = hashlib.sha256()

    for node in sorted(values.keys()):

        array = np.asarray(
            values[node],
            dtype=np.float64
        ).reshape(-1)

        digest.update(node.encode("utf-8"))
        digest.update(str(array.shape).encode("utf-8"))
        digest.update(array.tobytes())

    return digest.hexdigest()


# ============================================================
# Start
# ============================================================

print("=" * 70, flush=True)
print("SCARLET DISTRIBUTED CSV AVERAGE - CONTINUOUS VERSION", flush=True)
print(f"Node ID          : {NODE_ID}", flush=True)
print(f"CSV file         : {CSV_FILE}", flush=True)
print(f"Scarlet name     : {SCARLET_NAME}", flush=True)
print(f"Minimum nodes    : {MIN_NODES}", flush=True)
print(f"Heartbeat        : {HEARTBEAT_SECONDS} sec", flush=True)
print(f"Node TTL         : {NODE_TTL_SECONDS} sec", flush=True)
print("=" * 70, flush=True)


last_state_signature = None
last_nodes = tuple()


# ============================================================
# Continuous distributed loop
# ============================================================

while True:

    # --------------------------------------------------------
    # 1. Reread local CSV every cycle
    # --------------------------------------------------------

    try:

        local_array = read_local_array()

    except Exception as exc:

        print(
            f"[{NODE_ID}] Could not read CSV: {exc}",
            flush=True
        )

        time.sleep(HEARTBEAT_SECONDS)
        continue


    # --------------------------------------------------------
    # 2. Publish latest local values
    # --------------------------------------------------------

    try:

        publish_local_array(local_array)

    except Exception as exc:

        print(
            f"[{NODE_ID}] Publish failed: {exc}",
            flush=True
        )

        time.sleep(HEARTBEAT_SECONDS)
        continue


    # --------------------------------------------------------
    # 3. Discover latest active nodes and values
    # --------------------------------------------------------

    values, success, error = mapper.AllGather()

    if not success:

        print(
            f"[{NODE_ID}] AllGather failed: {error}",
            flush=True
        )

        time.sleep(HEARTBEAT_SECONDS)
        continue


    current_nodes = tuple(
        sorted(values.keys())
    )


    # Only print membership when it changes
    if current_nodes != last_nodes:

        print("", flush=True)

        print(
            f"[{NODE_ID}] MEMBERSHIP CHANGED",
            flush=True
        )

        print(
            f"[{NODE_ID}] Active nodes "
            f"({len(current_nodes)}): "
            f"{list(current_nodes)}",
            flush=True
        )

        last_nodes = current_nodes

        # Force recalculation
        last_state_signature = None


    # --------------------------------------------------------
    # 4. Require minimum number of nodes
    # --------------------------------------------------------

    if len(current_nodes) < MIN_NODES:

        if last_state_signature is not None:
            last_state_signature = None

        time.sleep(HEARTBEAT_SECONDS)
        continue


    # --------------------------------------------------------
    # 5. Detect ANY data/membership change
    # --------------------------------------------------------

    current_signature = create_state_signature(
        values
    )


    if current_signature == last_state_signature:

        # Nothing changed anywhere.
        time.sleep(HEARTBEAT_SECONDS)
        continue


    # --------------------------------------------------------
    # 6. Validate array sizes
    # --------------------------------------------------------

    arrays = {
        node: np.asarray(
            values[node],
            dtype=float
        ).reshape(-1)
        for node in current_nodes
    }


    sizes = {
        len(array)
        for array in arrays.values()
    }


    if len(sizes) != 1:

        print(
            f"[{NODE_ID}] Cannot calculate average. "
            f"Different array sizes found: {sizes}",
            flush=True
        )

        last_state_signature = current_signature

        time.sleep(HEARTBEAT_SECONDS)
        continue


    # --------------------------------------------------------
    # 7. Calculate new distributed average
    # --------------------------------------------------------

    combined = np.vstack(
        list(arrays.values())
    )

    average = np.mean(
        combined,
        axis=0
    )


    # --------------------------------------------------------
    # 8. Print only when something actually changed
    # --------------------------------------------------------

    print("", flush=True)
    print("=" * 70, flush=True)
    print("DISTRIBUTED STATE UPDATED", flush=True)

    print(
        f"ACTIVE NODES = {len(current_nodes)}",
        flush=True
    )


    for node in current_nodes:

        print(
            f"{node}: {arrays[node]}",
            flush=True
        )


    print("", flush=True)

    print(
        f"NEW AVERAGE = {average}",
        flush=True
    )

    print("=" * 70, flush=True)


    last_state_signature = current_signature


    time.sleep(HEARTBEAT_SECONDS)