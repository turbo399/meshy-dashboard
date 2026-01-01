FROM python:3.11-slim

# Prevent python from buffering logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better build cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Default port (can be overridden)
ENV LISTEN_HOST=0.0.0.0
ENV LISTEN_PORT=5001

EXPOSE 5001

CMD ["python", "app.py"]
