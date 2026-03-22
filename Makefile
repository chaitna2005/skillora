# Skillora - Local & Google Cloud
# Project: skillora-App

.PHONY: help local build docker-hub-build-push gcp-auth gcp-apis gcp-repo gcp-db gcp-db-create gcp-db-status gcp-schema gcp-schema-docker gcp-build gcp-deploy-backend gcp-deploy-frontend gcp-deploy-all gcp-urls gcp-clean

# -----------------------------------------------------------------------------
# Local
# -----------------------------------------------------------------------------
local:
	docker compose up -d --build

local-down:
	docker compose down

local-logs:
	docker compose logs -f

# -----------------------------------------------------------------------------
# Docker Hub - build linux/amd64 on Mac, push, then pull on droplet (docs/DEPLOY-DROPLET.md)
# Use this if bash scripts/build-and-push-images.sh fails with ": command not found" (CRLF).
# Pipe (not bash <(...)) so /bin/sh (Make's default) can run the recipe on macOS.
# -----------------------------------------------------------------------------
docker-hub-build-push:
	@test -f deploy/.env.production || (echo "Missing deploy/.env.production - copy deploy/.env.example" && exit 1)
	tr -d '\r' < scripts/build-and-push-images.sh | bash

# -----------------------------------------------------------------------------
# Google Cloud (project ID must be lowercase, e.g. skillora-app)
# -----------------------------------------------------------------------------
GCP_PROJECT    ?= skillora-app
GCP_REGION     := us-central1
GCP_REGION2    := us-central1
ARTIFACT_REPO  := skillora
# Set in gcp.env or here if different (e.g. instance name from Cloud Console)
CLOUD_SQL_NAME ?= skillora-db
DB_NAME        := testmyknowledge
DB_USER        := skillora_app
BACKEND_SVC    := skillora-backend
FRONTEND_SVC   := skillora-frontend

# Load secrets from gcp.env (create from gcp.env.example) - not committed
-include gcp.env
export

help:
	@echo "Local:"
	@echo "  make local          - Start app with Docker Compose"
	@echo "  make local-down     - Stop containers"
	@echo "  make local-logs     - Follow logs"
	@echo ""
	@echo "Google Cloud (project: $(GCP_PROJECT)):"
	@echo "  make gcp-projects   - List projects (get PROJECT_ID for gcp.env)"
	@echo "  make gcp-auth       - Login and set project"
	@echo "  make gcp-apis       - Enable required APIs"
	@echo "  make gcp-repo       - Create Artifact Registry repository"
	@echo "  make gcp-db         - Create Cloud SQL instance + database + user"
	@echo "  make gcp-db-create  - Create database + user on existing instance only"
	@echo "  make gcp-db-status  - Check if Cloud SQL instance is ready"
	@echo "  make gcp-schema     - Run schema (needs cloud-sql-proxy + psql)"
	@echo "  make gcp-schema-docker - Run schema using Docker (no local install)"
	@echo "  make gcp-build      - Build and push backend + frontend images"
	@echo "  make gcp-deploy-backend  - Deploy backend to Cloud Run"
	@echo "  make gcp-deploy-frontend - Deploy frontend to Cloud Run"
	@echo "  make gcp-deploy-all - Full deploy (db, schema, build, deploy both)"
	@echo "  make gcp-urls       - Print backend and frontend URLs"
	@echo ""
	@echo "First time: create gcp.env from gcp.env.example and set DB_PASSWORD, OPENAI_API_KEY, SECRET_KEY"

# --- Auth & project ---
gcp-projects:
	@echo "Your GCP projects (use PROJECT_ID, not display name):"
	@gcloud projects list --format="table(projectId,name)"

gcp-auth:
	gcloud auth login
	gcloud config set project $(GCP_PROJECT)

# --- Enable APIs ---
gcp-apis:
	gcloud services enable run.googleapis.com --project=$(GCP_PROJECT)
	gcloud services enable sqladmin.googleapis.com --project=$(GCP_PROJECT)
	gcloud services enable artifactregistry.googleapis.com --project=$(GCP_PROJECT)
	gcloud services enable secretmanager.googleapis.com --project=$(GCP_PROJECT)
	@echo "APIs enabled."

# --- Artifact Registry ---
gcp-repo:
	gcloud artifacts repositories create $(ARTIFACT_REPO) \
		--repository-format=docker \
		--location=$(GCP_REGION) \
		--project=$(GCP_PROJECT) \
		--description="Skillora images" || true
	@echo "Artifact Registry repo ready."

# --- Cloud SQL: instance + database + user (public IP for Cloud Run) ---
# Requires gcp.env with DB_PASSWORD
gcp-db:
	@if [ -z "$$DB_PASSWORD" ]; then echo "Create gcp.env from gcp.env.example and set DB_PASSWORD"; exit 1; fi
	gcloud sql instances create $(CLOUD_SQL_NAME) \
		--project=$(GCP_PROJECT) \
		--database-version=POSTGRES_15 \
		--tier=db-f1-micro \
		--region=$(GCP_REGION) \
		--root-password="$$DB_PASSWORD" \
		--storage-type=SSD \
		--storage-size=10GB \
		|| true
	gcloud sql databases create $(DB_NAME) --instance=$(CLOUD_SQL_NAME) --project=$(GCP_PROJECT) || true
	gcloud sql users create $(DB_USER) --instance=$(CLOUD_SQL_NAME) --password="$$DB_PASSWORD" --project=$(GCP_PROJECT) || true
	@echo "Cloud SQL ready. Run: make gcp-schema"

# --- Create database + user on existing Cloud SQL instance (skip instance create) ---
gcp-db-create:
	@if [ -z "$$DB_PASSWORD" ]; then echo "Set DB_PASSWORD in gcp.env"; exit 1; fi
	gcloud sql databases create $(DB_NAME) --instance=$(CLOUD_SQL_NAME) --project=$(GCP_PROJECT) || true
	gcloud sql users create $(DB_USER) --instance=$(CLOUD_SQL_NAME) --password="$$DB_PASSWORD" --project=$(GCP_PROJECT) || true
	@echo "Database and user ready. Run: make gcp-schema"

# --- Check if Cloud SQL instance is ready ---
gcp-db-status:
	@echo "Checking Cloud SQL instance: $(CLOUD_SQL_NAME)"
	@gcloud sql instances describe $(CLOUD_SQL_NAME) --project=$(GCP_PROJECT) --format="table(state,connectionName,ipAddresses.ipAddress)" 2>/dev/null || (echo "Instance not found or not ready. Check: gcloud sql instances list --project=$(GCP_PROJECT)"; exit 1)
	@echo "If state is RUNNABLE, the instance is ready."

# --- Run schema on Cloud SQL ---
# Option A: use Docker (no local Cloud SQL Proxy or psql needed)
gcp-schema-docker:
	@if [ -z "$$DB_PASSWORD" ]; then echo "Set DB_PASSWORD in gcp.env"; exit 1; fi
	$(eval CONN_NAME := $(shell gcloud sql instances describe $(CLOUD_SQL_NAME) --project=$(GCP_PROJECT) --format='value(connectionName)' 2>/dev/null))
	@if [ -z "$(CONN_NAME)" ]; then echo "Cloud SQL instance $(CLOUD_SQL_NAME) not found."; exit 1; fi
	@echo "Running schema via Docker (Cloud SQL Proxy + psql)..."
	@docker network create skillora-sqlnet 2>/dev/null || true
	@docker rm -f skillora-sqlproxy 2>/dev/null || true
	@docker run -d --name skillora-sqlproxy --network skillora-sqlnet -p 15432:15432 \
		-v $(HOME)/.config/gcloud/application_default_credentials.json:/adc.json:ro \
		-e GOOGLE_APPLICATION_CREDENTIALS=/adc.json \
		gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest \
		"$(CONN_NAME)" --port 15432 --address 0.0.0.0
	@echo "Waiting for Cloud SQL Proxy (~8s)..."
	@sleep 8
	@echo "Running schema (if this fails, run: make gcp-db-create  and ensure DB_PASSWORD in gcp.env is correct)"
	@docker run --rm --network skillora-sqlnet -e PGPASSWORD="$$DB_PASSWORD" \
		-v $(PWD)/database:/schema postgres:15-alpine \
		psql -h skillora-sqlproxy -p 15432 -U $(DB_USER) -d $(DB_NAME) -f /schema/schema.sql
	@docker rm -f skillora-sqlproxy 2>/dev/null || true
	@echo "Schema applied."

# Option B: use local Cloud SQL Proxy + psql (install: brew install cloud-sql-proxy postgresql)
gcp-schema:
	@which cloud_sql_proxy >/dev/null 2>&1 || which cloud-sql-proxy >/dev/null 2>&1 || (echo "Install Cloud SQL Proxy: brew install cloud-sql-proxy  (or use: make gcp-schema-docker)"; exit 1)
	@which psql >/dev/null || (echo "Install psql: brew install postgresql  (or use: make gcp-schema-docker)"; exit 1)
	@if [ -z "$$DB_PASSWORD" ]; then echo "Set DB_PASSWORD in gcp.env"; exit 1; fi
	$(eval CONN_NAME := $(shell gcloud sql instances describe $(CLOUD_SQL_NAME) --project=$(GCP_PROJECT) --format='value(connectionName)' 2>/dev/null))
	@if [ -z "$(CONN_NAME)" ]; then echo "Cloud SQL instance $(CLOUD_SQL_NAME) not found."; exit 1; fi
	@echo "Running schema via Cloud SQL Proxy..."
	@mkdir -p .tmp
	@if command -v cloud_sql_proxy >/dev/null 2>&1; then cloud_sql_proxy -instances="$(CONN_NAME)=tcp:15432" & else cloud-sql-proxy -instances="$(CONN_NAME)=tcp:15432" & fi
	@sleep 3
	@PGPASSWORD="$$DB_PASSWORD" psql -h 127.0.0.1 -p 15432 -U $(DB_USER) -d $(DB_NAME) -f database/schema.sql || true
	@pkill -f "cloud_sql_proxy.*15432" 2>/dev/null; pkill -f "cloud-sql-proxy.*15432" 2>/dev/null; true
	@echo "Schema applied."

# --- Build & push images ---
IMAGE_BACKEND  := $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REPO)/backend:latest
IMAGE_FRONTEND := $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REPO)/frontend:latest

gcp-configure-docker:
	gcloud auth configure-docker $(GCP_REGION)-docker.pkg.dev --quiet

gcp-build: gcp-configure-docker
	@echo "Building backend for linux/amd64 (Cloud Run)..."
	docker build --platform linux/amd64 -t $(IMAGE_BACKEND) ./backend
	docker push $(IMAGE_BACKEND)
	@echo "Backend image pushed."
	@echo "Build frontend after backend is deployed (need BACKEND_URL). Run: make gcp-deploy-backend first, then make gcp-build-frontend"

# Frontend build needs BACKEND_URL (set after first backend deploy, or set in gcp.env)
gcp-build-frontend: gcp-configure-docker
	@if [ -z "$$BACKEND_URL" ]; then echo "Set BACKEND_URL in gcp.env (e.g. https://skillora-backend-xxx.run.app)"; exit 1; fi
	docker build --platform linux/amd64 -t $(IMAGE_FRONTEND) --build-arg REACT_APP_API_URL=$$BACKEND_URL ./frontend
	docker push $(IMAGE_FRONTEND)
	@echo "Frontend image pushed."

# --- Deploy to Cloud Run ---
gcp-deploy-backend:
	@if [ -z "$$DB_PASSWORD" ]; then echo "Set DB_PASSWORD in gcp.env"; exit 1; fi
	@if [ -z "$$OPENAI_API_KEY" ]; then echo "Set OPENAI_API_KEY in gcp.env"; exit 1; fi
	@if [ -z "$$SECRET_KEY" ]; then echo "Set SECRET_KEY in gcp.env"; exit 1; fi
	$(eval CONN_NAME := $(shell gcloud sql instances describe $(CLOUD_SQL_NAME) --project=$(GCP_PROJECT) --format='value(connectionName)' 2>/dev/null))
	@if [ -z "$(CONN_NAME)" ]; then echo "Cloud SQL instance not found. Run: make gcp-db"; exit 1; fi
	gcloud run deploy $(BACKEND_SVC) \
		--project=$(GCP_PROJECT) \
		--image=$(IMAGE_BACKEND) \
		--region=$(GCP_REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--add-cloudsql-instances="$(CONN_NAME)" \
		--set-env-vars="DATABASE_HOST=/cloudsql/$(CONN_NAME),DATABASE_PORT=5432,DATABASE_NAME=$(DB_NAME),DATABASE_USER=$(DB_USER),DATABASE_PASSWORD=$$DB_PASSWORD,OPENAI_API_KEY=$$OPENAI_API_KEY,OPENAI_MODEL=$${OPENAI_MODEL:-gpt-4o-mini},SECRET_KEY=$$SECRET_KEY,CORS_ORIGINS=$${FRONTEND_URL:-*}" \
		--timeout=300

	@echo "Backend deployed. Get URL and set BACKEND_URL in gcp.env, then: make gcp-build-frontend && make gcp-deploy-frontend"

gcp-deploy-frontend:
	@if [ -z "$$BACKEND_URL" ]; then echo "Set BACKEND_URL in gcp.env"; exit 1; fi
	$(eval FRONTEND_URL := $(shell gcloud run services describe $(FRONTEND_SVC) --region=$(GCP_REGION) --project=$(GCP_PROJECT) --format='value(status.url)' 2>/dev/null || echo ""))
	gcloud run deploy $(FRONTEND_SVC) \
		--project=$(GCP_PROJECT) \
		--image=$(IMAGE_FRONTEND) \
		--region=$(GCP_REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--set-env-vars="REACT_APP_API_URL=$$BACKEND_URL"
	@echo "Frontend deployed. Run: make gcp-urls"

# Full deploy: ensure APIs, repo, DB, schema, build backend, deploy backend, build frontend, deploy frontend
gcp-deploy-all: gcp-apis gcp-repo
	@echo "Ensure Cloud SQL exists (make gcp-db-public if not), then run: make gcp-schema"
	@echo "Then: make gcp-build && make gcp-deploy-backend"
	@echo "Set BACKEND_URL in gcp.env from the deployed backend URL, then: make gcp-build-frontend && make gcp-deploy-frontend"

gcp-urls:
	@echo "Backend:  $$(gcloud run services describe $(BACKEND_SVC) --region=$(GCP_REGION) --project=$(GCP_PROJECT) --format='value(status.url)' 2>/dev/null || echo 'not deployed')"
	@echo "Frontend: $$(gcloud run services describe $(FRONTEND_SVC) --region=$(GCP_REGION) --project=$(GCP_PROJECT) --format='value(status.url)' 2>/dev/null || echo 'not deployed')"

gcp-clean:
	@echo "Removing Cloud Run services and Cloud SQL (manual)."
	gcloud run services delete $(BACKEND_SVC) --region=$(GCP_REGION) --project=$(GCP_PROJECT) --quiet || true
	gcloud run services delete $(FRONTEND_SVC) --region=$(GCP_REGION) --project=$(GCP_PROJECT) --quiet || true
	@echo "To delete Cloud SQL: gcloud sql instances delete $(CLOUD_SQL_NAME) --project=$(GCP_PROJECT)"
