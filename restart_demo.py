"""Demonstrates the volatility flaw of keeping the ledger in memory.

Deposits money, shows the balance, runs `docker compose restart`, then asks the
Balance API for the same account again. Because mongodb-store keeps /data/db on
a tmpfs (host RAM), stopping the container tears that filesystem down and every
account record disappears with it.

Run from the project root, on the host where Docker is running:

    python3 restart_demo.py

If your Docker needs elevated rights:

    COMPOSE_CMD="sudo docker compose" python3 restart_demo.py
"""

import os
import shlex
import subprocess
import sys
import time

import requests

from atm_client import send_transaction
from mobile_client import check_balance

ACCOUNT_ID = "1002-XYZ"
DEPOSIT_AMOUNT = 250.00
API_BASE_URL = "http://localhost:8000"
COMPOSE_CMD = shlex.split(os.environ.get("COMPOSE_CMD", "docker compose"))
WORKER_GRACE_SECONDS = 3


def banner(text):
    print()
    print("=" * 68)
    print(text)
    print("=" * 68)


def wait_for_api(timeout_seconds=60):
    print("[Demo] Waiting for balance-api to accept requests again...")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            requests.get(f"{API_BASE_URL}/balance/__probe__", timeout=2)
            print("[Demo] balance-api is back up.")
            return True
        except requests.exceptions.RequestException:
            time.sleep(2)
    print(f"[Demo] balance-api never came back within {timeout_seconds}s.")
    return False


def main():
    banner("STEP 1: Push a deposit through RabbitMQ")
    send_transaction(ACCOUNT_ID, "deposit", DEPOSIT_AMOUNT)
    print(f"[Demo] Letting the worker consume the message ({WORKER_GRACE_SECONDS}s)...")
    time.sleep(WORKER_GRACE_SECONDS)

    banner("STEP 2: Balance BEFORE the restart")
    before = check_balance(ACCOUNT_ID)

    banner("STEP 3: docker compose restart")
    print(f"[Demo] Running: {' '.join(COMPOSE_CMD)} restart")
    result = subprocess.run(COMPOSE_CMD + ["restart"])
    if result.returncode != 0:
        print("[Demo] Restart failed. If Docker needs elevated rights, retry with:")
        print('       COMPOSE_CMD="sudo docker compose" python3 restart_demo.py')
        sys.exit(1)

    if not wait_for_api():
        sys.exit(1)

    banner("STEP 4: Balance AFTER the restart")
    after = check_balance(ACCOUNT_ID)

    banner("VERDICT")
    if before.status_code == 200 and after.status_code == 404:
        print(
            f"[Demo] Before: HTTP 200, ${before.json()['balance']:.2f}   "
            f"After: HTTP {after.status_code}, account no longer exists."
        )
        print("[Demo] FLAW DEMONSTRATED: the ledger lived on a tmpfs backed by host")
        print("[Demo] RAM, so stopping mongodb-store destroyed every account record.")
        print("[Demo] A restart is enough to lose customer money in this design.")
        print("[Demo] Fix: back /data/db with a named volume (see docker-compose.yml).")
    elif before.status_code == 200 and after.status_code == 200:
        print(
            f"[Demo] Before: ${before.json()['balance']:.2f}   "
            f"After: ${after.json()['balance']:.2f} - the data SURVIVED."
        )
        print("[Demo] No data loss occurred, so the flaw was NOT demonstrated. Check")
        print("[Demo] whether mongodb-store is still using the durable named volume")
        print("[Demo] instead of the tmpfs mount in docker-compose.yml.")
    else:
        print(
            f"[Demo] Unexpected result - before: HTTP {before.status_code}, "
            f"after: HTTP {after.status_code}."
        )
        print("[Demo] Expected 200 before the restart and 404 after it. Inspect the")
        print(f"[Demo] worker logs with: {' '.join(COMPOSE_CMD)} logs transaction-worker")


if __name__ == "__main__":
    main()
