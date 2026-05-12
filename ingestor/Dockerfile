FROM python:3.10-slim

WORKDIR /ingestor

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

RUN useradd -m appuser && chown -R appuser /ingestor
USER appuser

CMD ["python", "ingestor.py"]