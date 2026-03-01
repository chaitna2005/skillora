# TestMyKnowledge Backend - Local Docker
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app ./app
COPY docker-entrypoint.sh ./

# Config is loaded from env (docker-compose); .env is optional
RUN chmod +x docker-entrypoint.sh

EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["./docker-entrypoint.sh"]
