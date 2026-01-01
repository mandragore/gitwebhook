FROM python:3.11-slim

# Install system dependencies
# git: for pulling repositories
# docker.io: for restarting containers (client only)
# curl: for healthchecks or testing
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
