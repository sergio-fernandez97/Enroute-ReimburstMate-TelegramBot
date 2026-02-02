FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    "langchain-openai>=1.1.7" \
    "langgraph>=0.2.0"\
    "loguru>=0.7.3"\
    "minio>=7.2.0"\
    "psycopg[binary]>=3.2.1"\
    "python-dotenv>=1.2.1"\
    "python-telegram-bot>=22.6"


COPY . /app

CMD ["python", "app.py"]
