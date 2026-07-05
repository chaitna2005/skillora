#!/usr/bin/env bash
# Build Skillora backend + frontend images and push to Docker Hub.
# From repo root: bash scripts/build-and-push-images.sh
# If you see ": command not found" (CRLF): make docker-hub-build-push
# Needs: docker login, deploy/.env.production

set -e

# Repo root: works from normal path and when stdin-fed (git cwd must be repo)
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  cd "$(git rev-parse --show-toplevel)"
else
  cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

ENV_FILE=""
if [[ -f deploy/.env.production ]]; then
  ENV_FILE="deploy/.env.production"
elif [[ -f deploy/.env ]]; then
  ENV_FILE="deploy/.env"
else
  echo "ERROR: Create deploy/.env.production (copy deploy/.env.example)"
  exit 1
fi

# Do not `source` the whole file — OPENAI keys often contain "$" and break the shell.
read_env_key() {
  local key="$1"
  grep -E "^[[:space:]]*${key}=" "$ENV_FILE" | head -1 | tr -d '\r' | sed -E "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//"
}

_file_docker=$(read_env_key DOCKER_USER)
_file_react=$(read_env_key REACT_APP_API_URL)

if [[ -n "${DOCKER_USER:-}" && "$DOCKER_USER" != "YOUR_DOCKERHUB_USERNAME" ]]; then
  : # use exported DOCKER_USER (e.g. CI)
else
  DOCKER_USER="$_file_docker"
fi

if [[ -z "${DOCKER_USER:-}" || "$DOCKER_USER" == "YOUR_DOCKERHUB_USERNAME" ]]; then
  echo "ERROR: Set DOCKER_USER in $ENV_FILE"
  exit 1
fi

if [[ -n "${REACT_APP_API_URL:-}" ]]; then
  REACT_URL="$REACT_APP_API_URL"
elif [[ -n "$_file_react" ]]; then
  REACT_URL="$_file_react"
else
  REACT_URL="http://localhost:9081"
fi
PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"

echo "DOCKER_USER=$DOCKER_USER"
echo "REACT_APP_API_URL=$REACT_URL"
echo "Platform: $PLATFORM"

echo ">>> Building backend..."
docker build --platform "$PLATFORM" -t "$DOCKER_USER/skillora-backend:latest" backend/

echo ">>> Building frontend..."
docker build --platform "$PLATFORM" \
  --build-arg "REACT_APP_API_URL=$REACT_URL" \
  -f frontend/Dockerfile \
  -t "$DOCKER_USER/skillora-frontend:latest" \
  frontend/

echo ">>> Pushing..."
docker push "$DOCKER_USER/skillora-backend:latest"
docker push "$DOCKER_USER/skillora-frontend:latest"

echo ""
echo "Done. UI :9080  API :9081  (ERP :8080)"
