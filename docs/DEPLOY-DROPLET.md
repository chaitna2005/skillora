# Deploy Skillora on a droplet (Docker Hub → pull on server)

Same flow as many production setups: **build images on your Mac**, **push to Docker Hub**, **pull and run on the VPS** — no Maven/npm on the droplet.

Auth is **JWT + Postgres users** (no Keycloak). **OpenAI** key is required on the **backend** only.

---

## Files added for this workflow

| File | Purpose |
|------|---------|
| `scripts/build-and-push-images.sh` | Build **linux/amd64** images + push `skillora-backend:latest` / `skillora-frontend:latest` |
| `docker-compose.pull.yml` | Run pre-built images; Postgres internal-only; host ports **9080** (UI), **9081** (API) — **not** ERP’s **8080** |
| `deploy/.env.example` | Template — copy to `deploy/.env.production` (gitignored) |

---

## One-time: Docker Hub + env

1. Create a [Docker Hub](https://hub.docker.com) account if needed.
2. On your Mac: `docker login`
3. In the repo:

```bash
cp deploy/.env.example deploy/.env.production
```

4. Edit **`deploy/.env.production`**:

| Variable | Set to |
|----------|--------|
| `DOCKER_USER` | Your Docker Hub username |
| `REACT_APP_API_URL` | **Exact** URL the browser will use to reach the API after deploy. Default compose: `http://YOUR_DROPLET_IP:9081` (ERP uses **8080**) |
| `POSTGRES_*` | Strong password for Skillora DB (not ERP’s DB) |
| `OPENAI_API_KEY` | `sk-...` |
| `SECRET_KEY` | e.g. `openssl rand -hex 32` |
| `CORS_ORIGINS` | Comma-separated browser origins, e.g. `http://YOUR_DROPLET_IP:9080` (must match how you open the UI) |
| `DEBUG` | `false` |

`deploy/.env.production` is **gitignored** — do not commit secrets.

**Build script note:** `scripts/build-and-push-images.sh` reads only **`DOCKER_USER`** and **`REACT_APP_API_URL`** from that file (via `grep`), not `source`. That avoids shell errors when **`OPENAI_API_KEY`** contains characters like `$` that would break `source`.

---

## Build & push (on your Mac, after code changes)

From the **Skillora repo root**:

```bash
bash scripts/build-and-push-images.sh
```

**If you see** `: command not found`, `set: invalid option`, or **`ion: line N`** — the shell script likely has **Windows (CRLF) line endings**. Fix:

```bash
# Option A: run via Make (strips CR before bash runs the script)
make docker-hub-build-push

# Option B: normalize the script once, then use bash again
sed -i '' 's/\r$//' scripts/build-and-push-images.sh
bash scripts/build-and-push-images.sh
```

The repo includes **`.gitattributes`** (`*.sh text eol=lf`) so future checkouts keep LF on Mac/Linux.

- **Apple Silicon:** builds **`linux/amd64`** by default (DigitalOcean droplets). Override: `DOCKER_PLATFORM=linux/arm64 bash scripts/...` only if your server is arm64.
- **Frontend:** `REACT_APP_API_URL` is **baked into the JS** at build time — it must match the public API URL (scheme + host + port). If you change API port or domain, **rebuild and push** the frontend image.

---

## Keep deploy files in Git

Commit and push **`docker-compose.pull.yml`**, **`deploy/.env.example`**, and related scripts on your branch (e.g. `dockerize-the-app`) so the droplet can use **`git pull`** only.

If those files are missing on the remote branch, either push them from your Mac or copy once:

```bash
# From your Mac (repo root), example:
scp docker-compose.pull.yml root@YOUR_DROPLET_IP:/opt/skillora/
scp deploy/.env.example root@YOUR_DROPLET_IP:/opt/skillora/deploy/
```

---

## Deploy on the droplet (runbook)

**Prereqs on the server:** Docker + Compose plugin (`docker compose`), outbound HTTPS (pull images, OpenAI).  
**Private GitHub repo:** use **`git@github.com:OWNER/skillora.git`** — the droplet needs an SSH key allowed on GitHub (`HTTPS` clone without a token will fail).

### 1. Install Docker (if not already)

```bash
# Ubuntu/Debian example (DigitalOcean Docker image usually has this already)
docker --version
docker compose version
```

### 2. Clone or update the repo

```bash
sudo mkdir -p /opt
cd /opt

# First time (SSH — recommended for private repos):
sudo git clone --branch dockerize-the-app git@github.com:YOUR_ORG/skillora.git skillora
cd skillora

# Updates after you push from your Mac:
cd /opt/skillora
git fetch origin
git checkout dockerize-the-app
git pull origin dockerize-the-app
```

### 3. Env on the server

```bash
cd /opt/skillora
cp deploy/.env.example deploy/.env.production
nano deploy/.env.production   # or vim
chmod 600 deploy/.env.production
```

Set at least:

| Variable | Notes |
|----------|--------|
| `DOCKER_USER` | Same Docker Hub user as the pushed images |
| `POSTGRES_*` | Strong password; matches what you want for Skillora DB only |
| `OPENAI_API_KEY` | Real `sk-...` key — **required** for AI features |
| `SECRET_KEY` | e.g. `openssl rand -hex 32` on the server |
| `CORS_ORIGINS` | Exact UI origin, e.g. `http://YOUR_DROPLET_IP:9080` |

**`REACT_APP_API_URL`** in this file does **not** change the running frontend (it is baked in at image build on your Mac). Keep it accurate for docs / future rebuilds. If the UI calls the wrong API, rebuild the frontend with the correct URL and push again.

After editing secrets, recreate backend if it was already running:

```bash
docker compose --env-file deploy/.env.production -f docker-compose.pull.yml up -d --force-recreate backend
```

### 4. Docker Hub (pull)

Public images: no login. **Private** images:

```bash
docker login
```

### 5. Pull images and start

```bash
cd /opt/skillora
docker compose --env-file deploy/.env.production -f docker-compose.pull.yml pull
docker compose --env-file deploy/.env.production -f docker-compose.pull.yml up -d
docker compose --env-file deploy/.env.production -f docker-compose.pull.yml ps
```

### 6. Smoke test (from your Mac or the droplet)

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://YOUR_DROPLET_IP:9081/docs
curl -s -o /dev/null -w '%{http_code}\n' http://YOUR_DROPLET_IP:9080/
```

Expect **200** for both.

### 7. Firewall (if UFW or cloud firewall is on)

Allow **9080** (UI) and **9081** (API), e.g.:

```bash
sudo ufw allow 9080/tcp
sudo ufw allow 9081/tcp
sudo ufw reload
```

### 8. First-time database

Postgres runs **`database/schema.sql`** from the repo on **first** start (empty volume). If you need a full reset (destructive):

```bash
cd /opt/skillora
docker compose --env-file deploy/.env.production -f docker-compose.pull.yml down
docker volume ls | grep skillora    # find the postgres volume name
docker volume rm skillora_skillora_postgres_data   # default if project dir is /opt/skillora
docker compose --env-file deploy/.env.production -f docker-compose.pull.yml up -d
```

---

## URLs (default `docker-compose.pull.yml`)

| App | Host port | Example URL |
|-----|-----------|-------------|
| **ERP** (same droplet) | **8080** | `http://YOUR_IP:8080` — nginx (UI + API + Keycloak) |
| **Skillora UI** | **9080** | `http://YOUR_IP:9080` |
| **Skillora API** | **9081** | `http://YOUR_IP:9081` · docs: `/docs` |

Postgres for Skillora is **not** published on the host. If **9080** / **9081** are taken, change both mappings in `docker-compose.pull.yml` and rebuild the frontend with a matching `REACT_APP_API_URL`.

---

## Same droplet as ERP

- **ERP** is on **8080** only on the host; **Skillora** uses **9080** (UI) and **9081** (API) so there is no port overlap.
- Use a **separate Postgres container + volume** (this compose) or connect to shared Postgres only if you add a **second database** and credentials — do **not** use ERP’s `erp_platform` database for Skillora.

---

## OpenAI

- Set **`OPENAI_API_KEY`** in `deploy/.env.production`.
- Droplet needs outbound HTTPS to OpenAI.

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| **CORS / API calls fail** | `CORS_ORIGINS` includes exact UI origin (`http://ip:9080`). |
| **UI calls wrong API** | Rebuild frontend with correct `REACT_APP_API_URL` and push again. |
| **Cannot pull image** | `docker login` on server; `DOCKER_USER` matches Hub. |
| **Wrong CPU arch** | Images must be **amd64** for typical DO droplets — use default build script. |
| **OpenAI / quiz errors** | Set a real `OPENAI_API_KEY` in `deploy/.env.production`, then `docker compose ... up -d --force-recreate backend`. |
| **`git clone` over HTTPS fails** | Private repo: use `git@github.com:...` and add the server’s SSH key to GitHub. |
| **“Registration failed” / login never hits server** | The UI bundle still points at the **wrong API URL**. Set `REACT_APP_API_URL=http://YOUR_DROPLET_IP:9081` in `deploy/.env.production`, run **`make docker-hub-build-push`**, then on the droplet **`docker compose ... pull && up -d`**. The browser must call the same host:port the API listens on (**9081**). |

---

## Related

- **`docker-compose.yml`** — local dev with `docker compose up --build`
- **`DEPLOY.md`** — Google Cloud Run path
