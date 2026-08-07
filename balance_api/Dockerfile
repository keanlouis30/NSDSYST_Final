FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY balance_api/balance_api.py .

CMD ["uvicorn", "balance_api:app", "--host", "0.0.0.0", "--port", "8000"]
