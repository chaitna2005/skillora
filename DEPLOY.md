# Deploy Skillora to Google Cloud (skillora-App)

Use the Makefile for all steps. First time: install [gcloud CLI](https://cloud.google.com/sdk/docs/install) and log in.

---

## 1. One-time setup

```bash
# Copy secrets template and fill in (do not commit gcp.env)
cp gcp.env.example gcp.env
# Edit gcp.env: set DB_PASSWORD, OPENAI_API_KEY, SECRET_KEY (required)
# Optionally OPENAI_MODEL. BACKEND_URL and FRONTEND_URL come later.

# Auth and project
make gcp-auth

# Enable APIs and create Artifact Registry
make gcp-apis
make gcp-repo
```

---

## 2. Database (Cloud SQL)

**If you already have a Cloud SQL instance** (e.g. spinning up in the console):

```bash
# Create only the database and app user on your existing instance (set DB_PASSWORD in gcp.env)
# If your instance name is not "skillora-db", set CLOUD_SQL_NAME=your-instance-name in gcp.env
make gcp-db-create

# Install Cloud SQL Proxy, then run schema
# https://cloud.google.com/sql/docs/postgres/connect-auth-proxy
make gcp-schema
```

**If you need to create the instance from scratch:**

```bash
make gcp-db
make gcp-schema
```

---

## 3. Backend (Cloud Run)

```bash
# Configure Docker for Artifact Registry
make gcp-configure-docker

# Build and push backend image
make gcp-build

# Deploy backend (uses gcp.env: DB_PASSWORD, OPENAI_API_KEY, SECRET_KEY)
make gcp-deploy-backend
```

After deploy, copy the backend URL (e.g. `https://skillora-backend-xxxxx-uc.a.run.app`) into **gcp.env** as:

```bash
BACKEND_URL=https://skillora-backend-xxxxx-uc.a.run.app
```

---

## 4. Frontend (Cloud Run)

```bash
# Build frontend with BACKEND_URL (from gcp.env), then push
make gcp-build-frontend

# Deploy frontend
make gcp-deploy-frontend
```

Optional: set **FRONTEND_URL** in gcp.env to the deployed frontend URL, then redeploy backend so CORS is restricted to that origin:

```bash
make gcp-deploy-backend
```

---

## 5. URLs

```bash
make gcp-urls
```

Open the frontend URL in the browser.

---

## Quick reference

| Target | What it does |
|--------|----------------|
| `make help` | List all targets |
| `make gcp-auth` | Login + set project skillora-App |
| `make gcp-apis` | Enable Run, SQL, Artifact Registry, Secret Manager |
| `make gcp-repo` | Create Artifact Registry repo `skillora` |
| `make gcp-db` | Create Cloud SQL instance + DB + user |
| `make gcp-schema` | Run database/schema.sql (needs Cloud SQL Proxy) |
| `make gcp-build` | Build and push backend image |
| `make gcp-deploy-backend` | Deploy backend to Cloud Run |
| `make gcp-build-frontend` | Build frontend (needs BACKEND_URL in gcp.env) and push |
| `make gcp-deploy-frontend` | Deploy frontend to Cloud Run |
| `make gcp-urls` | Print backend and frontend URLs |
| `make gcp-clean` | Delete Cloud Run services (SQL kept) |

---

## Troubleshooting

- **Schema fails**: Install [Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy) and ensure `psql` is on your PATH.
- **Backend 500 / DB**: Check Cloud Run logs; ensure Cloud SQL instance is in the same region and `gcp-schema` was run.
- **CORS**: Set `FRONTEND_URL` in gcp.env to your frontend Cloud Run URL and run `make gcp-deploy-backend` again.
- **Project/region**: Edit `GCP_PROJECT` and `GCP_REGION` at the top of the Makefile if needed (default: skillora-App, us-central1).
