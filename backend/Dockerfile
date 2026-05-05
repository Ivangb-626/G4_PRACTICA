FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.main \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

COPY . .

EXPOSE 8000

# Production: gunicorn with sync workers (Flask is sync)
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "--timeout", "120", "app.main:app"]
