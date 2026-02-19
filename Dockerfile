FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml /app/pyproject.toml

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e ".[dev]"

COPY . /app

RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
