FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/app/browsers

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium and all its system dependencies during BUILD (not at runtime)
RUN playwright install chromium --with-deps

COPY . .

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --timeout 300 --log-level debug main:app"]
