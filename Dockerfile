FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    "langgraph>=0.2.0" \
    "python-dotenv>=1.2.1" \
    "python-telegram-bot>=22.6"

COPY . /app

CMD ["python", "app.py"]
