# NSDSYST Final — CQRS Banking Microservices

Written in partial fulfillment for the requirements of NSDSYST by Kean Rosales and Evan Pinca.

A containerised banking ledger split along CQRS lines:

| Service | Role | Talks to |
| --- | --- | --- |
| `transaction-worker` | Command side — consumes deposits/withdrawals asynchronously | RabbitMQ → MongoDB |
| `balance-api` | Query side — serves balances over HTTP on port 8000 | MongoDB (directly) |
| `rabbitmq-broker` | Message queue (`transaction_queue`) | — |
| `mongodb-store` | Data layer | — |

## Running on a fresh machine

Everything needed is in this folder — no `git clone` or `git pull` required.

**1. Install Docker** (Docker Desktop on Windows/macOS, or `docker.io` + the Compose plugin on Linux) and confirm it works:

```bash
docker --version && docker compose version
```

**2. Install the Python libraries** used by the client scripts (`requirements.txt` is the same file the container images install, so `pika` and `requests` come along with it):

```bash
pip3 install -r requirements.txt
```

**3. Launch the stack** from this directory:

```bash
docker compose up --build -d
```

Verify all four containers are up with `docker compose ps`. Add `sudo` to the Docker commands if your user is not in the `docker` group.

## Normal usage

```bash
python3 atm_client.py 1002-XYZ deposit 250.00
python3 mobile_client.py 1002-XYZ
```

Both scripts take optional arguments — `atm_client.py [account_id] [deposit|withdraw] [amount]` and `mobile_client.py [account_id]` — defaulting to a $250.00 deposit for account `1002-XYZ`.

Things worth demonstrating:

- **Insufficient funds:** `python3 atm_client.py 1002-XYZ withdraw 9999` is rejected by the worker, leaving MongoDB untouched.
- **Unknown account:** `python3 mobile_client.py 9999-NOPE` returns HTTP 404.
- **Live processing:** `docker compose logs -f transaction-worker` (Ctrl+C to stop following).

## The volatility demo

```bash
python3 restart_demo.py
```

Use `COMPOSE_CMD="sudo docker compose" python3 restart_demo.py` if Docker needs elevated rights.

The script deposits $250, shows the balance, runs `docker compose restart`, waits for the API to return, and queries the same account again — which now 404s.

This works because `mongodb-store` mounts `/data/db` as a **tmpfs**, so the ledger lives in host RAM. Docker discards a tmpfs mount whenever the container stops, meaning a plain restart destroys every account record. It is a deliberate illustration of why an in-memory data layer is unfit for financial state.

**The fix** is commented into `docker-compose.yml`: swap the `tmpfs` block on `mongodb-store` for the named `mongo_data` volume (and uncomment the top-level `volumes:` block). Re-run the demo afterwards and the balance survives the restart — the script detects this and reports that no data loss occurred.

Note that `docker compose restart` only wipes data because of the tmpfs. A restart alone stops and starts the *same* container, so with a named volume — or even with plain container storage — the data would persist.

## Teardown

```bash
docker compose down
```
