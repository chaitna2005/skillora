# Deploy to Google Cloud – Step by Step

Project: **skillora-App** (use project *ID*, which is lowercase, e.g. `skillora-app` — see Step 1.1)

---

## Where do env variables go? (like .env for backend)

**Use a single file in your project:** `gcp.env` (in the repo root, same level as the Makefile).

- **Do not commit** `gcp.env` (it’s in `.gitignore`).
- The Makefile reads `gcp.env` and passes these values to Cloud Run when you run `make gcp-deploy-backend` and `make gcp-deploy-frontend`.
- So: **one place** = `gcp.env`. No need to add env vars in the GCP Console for normal deploy; the Makefile injects them.

**Create it once:**

```bash
cp gcp.env.example gcp.env
```

Then edit `gcp.env` and set (see Step 1 below).

---

## Step 1: Set project and env variables

**1.1 Select the GCP project**

GCP **project IDs** are lowercase only (e.g. `skillora-app`). The name in the Console (e.g. "skillora-App") is the display name; the **ID** is what you use.

To find your project ID:
```bash
gcloud projects list
```
Use the **PROJECT_ID** column (lowercase).

Then either set it in `gcp.env` as `GCP_PROJECT=your-project-id`, or run:
```bash
make gcp-auth
```
(The Makefile default is `skillora-app`. If your ID is different, set `GCP_PROJECT` in `gcp.env` before running make.)

**1.2 Create and fill `gcp.env` (your “.env” for deploy)**

```bash
cp gcp.env.example gcp.env
```

Edit **`gcp.env`** and set:

| Variable | Required for | What to set |
|----------|----------------|-------------|
| `DB_PASSWORD` | DB + backend | Strong password for the DB user |
| `OPENAI_API_KEY` | Backend | Your OpenAI API key (e.g. `sk-...`) |
| `SECRET_KEY` | Backend | Random secret for JWT (e.g. `openssl rand -hex 32`) |
| `CLOUD_SQL_NAME` | Optional | Only if your instance name is **not** `skillora-db` |
| `OPENAI_MODEL` | Optional | Default `gpt-4o-mini` |

Leave these for later (you’ll set them after deploy):

- `BACKEND_URL` – set after Step 5 (backend deploy).
- `FRONTEND_URL` – optional; set after Step 7 to lock CORS.

Save the file. All later steps use this same `gcp.env`.

---

## Step 2: Enable APIs and create Artifact Registry

```bash
make gcp-apis
make gcp-repo
```

---

## Step 3: Create database and user on your existing instance

**If you haven’t created the database/user yet on your Cloud SQL instance:**

```bash
make gcp-db-create
```

(If your instance has a different name than `skillora-db`, set `CLOUD_SQL_NAME=your-instance-name` in `gcp.env` first.)

---

## Step 4: Check if the DB in Cloud is ready

**4.1 Check instance status**

```bash
make gcp-db-status
```

You should see `state: RUNNABLE`. If the instance is still creating, wait a few minutes and run again.

**4.2 Apply the schema (tables)**

**Option A – using Docker (no local install):**

```bash
make gcp-schema-docker
```

Uses Cloud SQL Proxy and `psql` in containers. Ensure Docker is running and you’ve run `gcloud auth application-default login` once if needed.

**Option B – using local tools:**

Install [Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy) and `psql` (e.g. `brew install cloud-sql-proxy postgresql`), then:

```bash
make gcp-schema
```

Either way, `database/schema.sql` is applied and the DB is ready for the backend.

---

## Step 5: Deploy the backend

**5.1 Configure Docker for Artifact Registry (one time)**

```bash
make gcp-configure-docker
```

**5.2 Build and push the backend image**

```bash
make gcp-build
```

(Images are built for `linux/amd64` for Cloud Run; on Apple Silicon this may take a bit longer.)

**5.3 Deploy the backend to Cloud Run**

```bash
make gcp-deploy-backend
```

The Makefile reads `DB_PASSWORD`, `OPENAI_API_KEY`, and `SECRET_KEY` from `gcp.env` and passes them to Cloud Run as environment variables (so the backend gets them like from a .env file).

**5.4 Copy the backend URL**

After deploy, the command output shows the backend URL, e.g.:

`https://skillora-backend-xxxxx-uc.a.run.app`

Open **`gcp.env`** and add (or uncomment and set):

```bash
BACKEND_URL=https://skillora-backend-xxxxx-uc.a.run.app
```

Replace with your actual URL. You need this for the frontend build.

---

## Step 6: Deploy the frontend

**6.1 Build the frontend (uses `BACKEND_URL` from gcp.env)**

```bash
make gcp-build-frontend
```

**6.2 Deploy the frontend to Cloud Run**

```bash
make gcp-deploy-frontend
```

---

## Step 7: Get URLs and test the frontend

**7.1 Print backend and frontend URLs**

```bash
make gcp-urls
```

**7.2 Open the frontend URL in your browser**

Use the **Frontend** URL from the output (e.g. `https://skillora-frontend-xxxxx-uc.a.run.app`).

**7.3 Test**

- Register / log in.
- Create a quiz and take a test.
- If the app loads but API calls fail, check the backend URL is correct in `gcp.env` as `BACKEND_URL`, then rebuild and redeploy the frontend:

  ```bash
  make gcp-build-frontend && make gcp-deploy-frontend
  ```

**Optional:** Set `FRONTEND_URL` in `gcp.env` to that frontend URL, then run `make gcp-deploy-backend` again to restrict CORS to your frontend only.

---

## Quick checklist

| Step | Command | Notes |
|------|---------|--------|
| 1 | Create `gcp.env` from `gcp.env.example`, set `DB_PASSWORD`, `OPENAI_API_KEY`, `SECRET_KEY` | Env vars for deploy |
| 2 | `make gcp-auth` | Select project (set `GCP_PROJECT` in gcp.env if not default) |
| 3 | `make gcp-apis` then `make gcp-repo` | APIs + Artifact Registry |
| 4a | `make gcp-db-create` | DB + user on existing instance |
| 4b | `make gcp-db-status` | Confirm instance is RUNNABLE |
| 4c | `make gcp-schema-docker` or `make gcp-schema` | Apply schema (Docker = no local install) |
| 5 | `make gcp-configure-docker` then `make gcp-build` then `make gcp-deploy-backend` | Deploy backend |
| 5b | Add `BACKEND_URL=...` to `gcp.env` | From deploy output |
| 6 | `make gcp-build-frontend` then `make gcp-deploy-frontend` | Deploy frontend |
| 7 | `make gcp-urls` and open Frontend URL in browser | Test app |

---

## Changing env variables later

1. Edit **`gcp.env`** on your machine.
2. Redeploy the service that uses them:
   - Backend: `make gcp-deploy-backend`
   - Frontend: `make gcp-build-frontend && make gcp-deploy-frontend` (if you changed `BACKEND_URL` or need to rebuild).

You do **not** need to add these in the GCP Console for the Makefile-based deploy; the Makefile injects them from `gcp.env`.
