import sys

import requests

API_BASE_URL = "http://localhost:8000"


def check_balance(account_id):
    print(f"[Mobile App] Querying balance for account: {account_id}...")
    url = f"{API_BASE_URL}/balance/{account_id}"
    print(f"[Mobile App] Contacting API at {url}")

    response = requests.get(url)
    print(f"[Mobile App] HTTP Status: {response.status_code} {response.reason}")

    if response.status_code == 200:
        data = response.json()
        print(f"[Mobile App] Current Balance: ${data['balance']:.2f}")
    else:
        print(f"[Mobile App] Error: {response.json().get('detail', 'Unknown error')}")


if __name__ == "__main__":
    account_id = sys.argv[1] if len(sys.argv) > 1 else "1002-XYZ"
    check_balance(account_id)
