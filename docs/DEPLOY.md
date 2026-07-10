# Deployment — GeoAvia (production)

This is the single recommended path to run GeoAvia on a public server with HTTPS. It uses
Docker Compose for the backend stack and [Caddy](https://caddyserver.com/) as the reverse
proxy because Caddy provisions and renews TLS certificates automatically.

Target: a fresh Linux server (Ubuntu 22.04+) with a domain name pointing at it.

## 1. Install the tools

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 nodejs npm python3

# Caddy (official repository)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

Confirm Node is 20+ (`node -v`); if not, install a 20+ release before building the frontend.

## 2. Get the code and create `.env`

```bash
git clone <repo-url> && cd Geoavia
cp .env_example .env
```

## 3. Harden `.env` (do this before starting anything)

Edit `.env` and set strong, unique values:

```bash
# Generate a strong JWT signing key and paste it into SECRET_KEY
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

| Variable | Set it to |
| :--- | :--- |
| `APP_ENV` | `production` |
| `SECRET_KEY` | the value generated above (never reuse across environments) |
| `DB_PASS` | a long random password |
| `ADMIN_USER` / `ADMIN_PASS` | your real admin login (strong password; the bootstrap enforces the policy) |
| `AIRFLOW_USER` / `AIRFLOW_PASS` | strong Airflow UI credentials (not `admin`/`admin`) |
| `CORS_ORIGINS` | your exact domain, e.g. `https://app.example.com` — no wildcard |
| `UVICORN_RELOAD` | leave empty (hot reload off) |
| `VITE_API_BASE_URL` | `/api` |

The backend refuses to boot in `production` if `SECRET_KEY` is still the placeholder.

## 4. Start the backend stack

The production override binds all container ports to `127.0.0.1`, so the database, API and
Airflow UI are only reachable through the reverse proxy:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The backend runs `alembic upgrade head` on boot. Create the admin user once the stack is up:

```bash
docker exec -e BOOT_USER="$ADMIN_USER" -e BOOT_PASS="$ADMIN_PASS" -e BOOT_ROLE=administrador \
  -i geoavia_backend python - <<'PY'
import os
from geoavia_backend.repositories.user import UserRepository
from geoavia_backend.services.user import UserService
username, password, role = os.environ["BOOT_USER"], os.environ["BOOT_PASS"], os.environ["BOOT_ROLE"]
if UserRepository().obtain_user_from_username(username) is None:
    UserService().register_user(username, password, role)
    print("created")
else:
    print("already exists")
PY
```

## 5. Build the frontend

The production frontend is static files (do **not** use the Vite dev server). Build once,
then serve the output with the reverse proxy:

```bash
cd frontend
npm ci
npm run build            # outputs to frontend/dist
sudo mkdir -p /var/www/geoavia
sudo cp -r dist/* /var/www/geoavia/
cd ..
```

`VITE_*` values are read from `.env` at build time, so make sure `.env` is correct before
building.

## 6. Configure Caddy (HTTPS + reverse proxy)

Replace `/etc/caddy/Caddyfile` with the following (swap `app.example.com` for your domain):

```caddyfile
app.example.com {
    encode gzip

    # API: strip the /api prefix and forward to the backend
    handle_path /api/* {
        reverse_proxy 127.0.0.1:8000
    }

    # Everything else: the static frontend (SPA fallback to index.html)
    handle {
        root * /var/www/geoavia
        try_files {path} /index.html
        file_server
    }
}
```

Reload Caddy — it obtains a Let's Encrypt certificate automatically:

```bash
sudo systemctl reload caddy
```

Your site is now live at `https://app.example.com`. The Airflow UI is intentionally not
exposed publicly; reach it over an SSH tunnel when needed:
`ssh -L 8080:127.0.0.1:8080 user@server` then open `http://localhost:8080`.

## 7. Firewall

Allow only SSH and web traffic:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Because the container ports bind to `127.0.0.1` (step 4), the database, backend and
Airflow UI are unreachable from the internet regardless of firewall rules.

## Security checklist

- [ ] `APP_ENV=production` and a generated `SECRET_KEY` (not the placeholder).
- [ ] Strong, unique `DB_PASS`, admin password, and Airflow credentials.
- [ ] `CORS_ORIGINS` set to your exact domain (no wildcard).
- [ ] `.env` is never committed (it is gitignored).
- [ ] Only ports 22/80/443 are public; DB/API/Airflow bind to `127.0.0.1`.
- [ ] TLS served by Caddy; the app is only reached over `https://`.

## Operations

```bash
# Logs
docker compose logs -f backend

# Restart the stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Update to a new version
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
cd frontend && npm ci && npm run build && sudo cp -r dist/* /var/www/geoavia/ && cd ..

# Back up the database (the Postgres data lives in the postgres_data volume)
docker exec geoavia_db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > backup_$(date +%F).sql.gz
```
