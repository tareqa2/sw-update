"""Generate realistic traffic against a deployed SW Update Manager, to fill the Grafana dashboard.

Each round picks a random device and component, reads its current version, then asks for an
upgrade, a downgrade or the same version (no change). Some rounds also send bad requests on
purpose (invalid version -> 400, unknown device -> 404), so error panels have data too.

Uses only the Python standard library - no venv needed.

    python scripts/demo_traffic.py --base-url http://127.0.0.1:57813 --rounds 60
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request
from collections import Counter

COMPONENTS = ["OS", "BE", "DB", "FW"]
DEVICES = [f"lab{i}" for i in range(1, 11)]


def call(base, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as err:
        return err.code, {}


def bump(version, direction):
    """Return version moved up or down by one step on its last non-zero part."""
    parts = [int(p) for p in version.split(".")]
    if direction > 0:
        parts[-1] += 1
        return ".".join(map(str, parts))
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] > 0:
            parts[i] -= 1
            return ".".join(map(str, parts))
    return version  # already 0.0.0 - nothing lower exists


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base-url", required=True, help="e.g. http://127.0.0.1:57813 (the minikube tunnel)")
    ap.add_argument("--rounds", type=int, default=60)
    ap.add_argument("--delay", type=float, default=0.3, help="seconds between rounds")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    status, _ = call(base, "GET", "/healthz")
    if status != 200:
        raise SystemExit(f"{base}/healthz returned {status} - is the tunnel open?")

    actions, statuses = Counter(), Counter()
    for n in range(1, args.rounds + 1):
        device, component = random.choice(DEVICES), random.choice(COMPONENTS)
        status, info = call(base, "GET", f"/api/v1/devices/{device}")
        statuses[status] += 1
        current = info["components"][component]["version"]

        roll = random.random()
        if roll < 0.08:                                   # bad input on purpose
            status, _ = call(base, "POST", f"/api/v1/devices/{device}/updates",
                             {"versions": {component: "not-a-version"}})
        elif roll < 0.12:                                 # unknown device on purpose
            status, _ = call(base, "GET", "/api/v1/devices/lab99")
        else:
            direction = random.choices([1, -1, 0], weights=[55, 25, 20])[0]
            target = bump(current, direction) if direction else current
            status, result = call(base, "POST", f"/api/v1/devices/{device}/updates",
                                  {"versions": {component: target}, "branch": "main",
                                   "commit_id": f"{random.getrandbits(28):07x}"})
            if status == 201:
                actions[result["changes"][component]["action"]] += 1
        statuses[status] += 1
        if n % 10 == 0:
            call(base, "GET", f"/api/v1/devices/{device}/history?limit=5")
            print(f"round {n}/{args.rounds}")
        time.sleep(args.delay)

    print("\nupdates by action:", dict(actions))
    print("responses by status:", dict(sorted(statuses.items())))


if __name__ == "__main__":
    main()
