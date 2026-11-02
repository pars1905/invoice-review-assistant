FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
CMD ["python", "demo.py"]
