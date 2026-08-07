FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY transaction_worker/transaction_worker.py .

CMD ["python", "transaction_worker.py"]
