import json
import sys

import pika

RABBITMQ_HOST = "localhost"
QUEUE_NAME = "transaction_queue"


def send_transaction(account_id, action, amount):
    print("[ATM] Connecting to RabbitMQ Broker...")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    payload = {"account_id": account_id, "action": action, "amount": amount}
    body = json.dumps(payload)

    print("[ATM] Sending transaction payload...")
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print(f"[ATM] Sent: {body}")
    print("[ATM] Transaction pushed to queue successfully.")

    connection.close()


if __name__ == "__main__":
    account_id = sys.argv[1] if len(sys.argv) > 1 else "1002-XYZ"
    action = sys.argv[2] if len(sys.argv) > 2 else "deposit"
    amount = float(sys.argv[3]) if len(sys.argv) > 3 else 250.00

    send_transaction(account_id, action, amount)
