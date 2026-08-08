# Written in partial fulfillment for the requirements of NSDSYST by Kean Rosales and Evan Pinca

import os

from fastapi import FastAPI, HTTPException
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")

app = FastAPI(title="Balance API")
mongo_client = MongoClient(MONGO_URI)
accounts = mongo_client["bank"]["accounts"]


@app.get("/balance/{account_id}")
def get_balance(account_id: str):
    account = accounts.find_one({"account_id": account_id})
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_id": account_id, "balance": account["balance"]}
