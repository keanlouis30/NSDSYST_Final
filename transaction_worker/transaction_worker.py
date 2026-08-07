import json
import os
import time

import pika
from pymongo import MongoClient

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
QUEUE_NAME = "transaction_queue"
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")

mongo_client = MongoClient(MONGO_URI)
accounts = mongo_client["bank"]["accounts"]


def connect_to_rabbitmq(max_retries=10, delay_seconds=3):
    for attempt in range(1, max_retries + 1):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
            print(f"[Worker] Connected to RabbitMQ at {RABBITMQ_HOST}")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(
                f"[Worker] RabbitMQ not ready (attempt {attempt}/{max_retries}), "
                f"retrying in {delay_seconds}s..."
            )
            time.sleep(delay_seconds)
    raise RuntimeError("Could not connect to RabbitMQ after multiple retries")


def process_transaction(body):
    try:
        payload = json.loads(body)
        account_id = payload["account_id"]
        action = payload["action"]
        amount = float(payload["amount"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"[Worker] Rejected malformed message: {body!r} ({exc})")
        return

    account = accounts.find_one({"account_id": account_id})
    current_balance = account["balance"] if account else 0.0

    if action == "deposit":
        new_balance = current_balance + amount
    elif action == "withdraw":
        new_balance = current_balance - amount
        if new_balance < 0:
            print(
                f"[Worker] Insufficient Funds: account {account_id} has "
                f"${current_balance:.2f}, cannot withdraw ${amount:.2f}"
            )
            return
    else:
        print(f"[Worker] Unknown action '{action}' for account {account_id}, skipping")
        return

    accounts.update_one(
        {"account_id": account_id},
        {"$set": {"balance": new_balance}},
        upsert=True,
    )
    print(
        f"[Worker] Processed {action} of ${amount:.2f} for {account_id}. "
        f"New balance: ${new_balance:.2f}"
    )


def on_message(channel, method, properties, body):
    process_transaction(body)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message, auto_ack=False)

    print(f"[Worker] Listening on queue '{QUEUE_NAME}'. Waiting for transactions...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()


if __name__ == "__main__":
    main()
