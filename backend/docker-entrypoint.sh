#!/bin/sh
# Wait for PostgreSQL when not on Cloud Run; start immediately when DATABASE_HOST is /cloudsql/...
set -e
export PGHOST="${DATABASE_HOST}" PGPORT="${DATABASE_PORT}" PGDATABASE="${DATABASE_NAME}" PGUSER="${DATABASE_USER}" PGPASSWORD="${DATABASE_PASSWORD}"

case "${DATABASE_HOST}" in
  /cloudsql/*) echo "Cloud SQL socket - starting backend"; ;;
  *)
    echo "Waiting for PostgreSQL at ${PGHOST}:${PGPORT}..."
    until python -c "
import os, sys, psycopg2
try:
    psycopg2.connect(
        host=os.environ['PGHOST'],
        port=int(os.environ.get('PGPORT', 5432)),
        dbname=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD']
    ).close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
      echo "Postgres is unavailable - sleeping 2s"
      sleep 2
    done
    echo "PostgreSQL is up"
    ;;
esac

# Cloud Run uses PORT=8080; local default 8000
echo "Starting backend on port ${PORT:-8000}"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
