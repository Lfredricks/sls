# Adoption Guide — Running This Project as Your Own

This guide is for a company that wants to take this repository and deploy it as
their **own** contractor/vendor directory. It covers everything beyond a basic
local run: licensing, rebranding, replacing the sample data, hardening for
production, deploying to a real server, and ongoing maintenance.

For first-time local setup (clone, venv, migrations, dev server) see
[`README.md`](README.md). This document assumes you can already run the app
locally and now want to make it yours.


---

## 1. The Adoption Workflow at a Glance

1. **Fork or import** the repo into your own GitHub account/organization.
2. **Get it running locally** (see README).
3. **Rebrand** — name, logo, colors, contact info (Section 3).
4. **Replace the sample data** and create your own admin account (Section 4).
5. **Harden for production** — secrets, admin password, debug off, HTTPS
   (Section 5).
6. **Deploy** to a server or platform (Section 6).
7. **Set up backups and maintenance** (Sections 7–8).

---

## 2. Fork / Import Into Your Own GitHub

**Option A — Fork** (keeps a visible link to the original):

```bash
# Use GitHub's "Fork" button, then:
git clone https://github.com/<your-org>/<your-fork>.git
```

**Option B — Clean import** (recommended when you want a private, independent
copy with no fork relationship):

```bash
git clone --bare https://github.com/<original-owner>/<repo>.git
cd <repo>.git
git push --mirror https://github.com/<your-org>/<your-new-repo>.git
```

Then clone your new repo normally and continue.

> **Note:** `.env`, the SQLite database, uploaded images, and local Claude
> settings are intentionally git-ignored (see `.gitignore`). A fresh clone will
> not contain secrets or data — you create those in the steps below.

---

## 3. Rebranding

The app currently ships branded as **"McBride Construction."** Replace every
touchpoint below. All paths are relative to the repo root.

### 3.1 Name and page titles

| What | File | Detail |
|---|---|---|
| Browser tab title | `sol_main/templates/layout.html` (lines ~9, ~11) | `<title>McBride Construction ...</title>` |
| Navbar brand | `sol_main/templates/layout.html` (line ~18) | `<a class="navbar-brand ...">McBride Construction</a>` |
| Homepage welcome copy | `sol_main/templates/main/home.html` | "Welcome" heading and intro paragraph |

A quick way to find every occurrence:

```bash
grep -rni "mcbride" sol_main/templates sol_main/static
```

### 3.2 Contact details

The sidebar contact block is in `sol_main/templates/layout.html` (lines ~60–61):

```html
<li class="list-group-item list-group-item-action">info@McBride.com</li>
<li class="list-group-item list-group-item-action">(206) 555-0100</li>
```

Replace with your company's real email and phone.

### 3.3 Colors and theme

The visual theme lives in `sol_main/static/main.css`:

| Token | Where | Current value |
|---|---|---|
| Primary brand color (navbar) | `.bg-steel` (line ~36) | `#0B233D` |
| Accent / link color | various | `#0071e3` |
| Page background | `body` (line ~3) | `#e8e8e8` |

Change these hex values to match your brand palette.

### 3.4 Logo and placeholder image

- **Listing placeholder:** replace `sol_main/static/default_listing.png` with
  your own default image (keep the same filename, or update references to it in
  the templates).
- **Add a logo:** drop an image into `sol_main/static/` and reference it in the
  navbar in `layout.html`, e.g.
  `<img src="{{ url_for('static', filename='logo.png') }}" alt="Your Co">`.

### 3.5 (Optional) Self-host front-end assets

`layout.html` loads Bootstrap 4, jQuery, and Popper from public CDNs
(maxcdn, cloudflare, code.jquery.com). This works out of the box but means the
app depends on third-party uptime and won't render styled when offline. For a
production deployment with a strict Content-Security-Policy, download those
files into `sol_main/static/vendor/` and update the `<link>`/`<script>` tags to
`url_for('static', ...)`.

---

## 4. Replace the Sample Data and Admin Account

### 4.1 Understand the seed script

`sol_main/seed.py` inserts **5 sample contractors, 5 sample vendors**, and a
default admin user (`admin` / `changeme`). It is **idempotent** — it skips
seeding if listings or an admin already exist.

### 4.2 Recommended approach for a real deployment

**Do not ship the demo data to production.** You have two clean options:

**Option A — Edit the seed script** with your own initial listings and a
non-default admin username, then run it once:

```bash
cd sol_main
# edit seed.py: replace CONTRACTORS / VENDORS lists and the admin block
python seed.py
```

**Option B — Start empty and add everything through the admin UI.** Create just
an admin account from a Flask shell, then add listings via `/admin/listings/new`:

```bash
cd sol_main
flask shell
```
```python
from extensions import db
from models import AdminUser
u = AdminUser(username='your-admin-name')
u.set_password('a-long-strong-password')
db.session.add(u); db.session.commit()
```

> **Critical:** if you do run `seed.py`, immediately change the default
> `admin` / `changeme` password — see Section 5.2.

---

## 5. Production Hardening Checklist

Work through every item before exposing the app to the internet.

### 5.1 Set a strong `SECRET_KEY`

`config.py` falls back to `'dev-only-change-in-production'` if unset. In
production, **always** set a real one in `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Put the result in `.env` as `SECRET_KEY=...`. (Copy `.env.example` to `.env`
as a starting point.) If this key leaks or uses the default, sessions and CSRF
tokens can be forged.

### 5.2 Change the admin password

If you seeded the default account:

```bash
cd sol_main
flask shell
```
```python
from extensions import db
from models import AdminUser
u = AdminUser.query.filter_by(username='admin').first()
u.set_password('a-long-strong-password')
db.session.commit()
```

### 5.3 Turn off debug mode

`sol_main/app.py` ends with `app.run(debug=True)` — that's for local
development only. In production you run under a WSGI server (Section 6) and
never invoke `app.run()`. Do **not** deploy with `debug=True`; it exposes an
interactive debugger that allows remote code execution.

### 5.4 Enforce HTTPS-only cookies

`config.py` already sets `SESSION_COOKIE_HTTPONLY = True` and
`SESSION_COOKIE_SAMESITE = 'Lax'`. For a production site served over HTTPS, also
add:

```python
SESSION_COOKIE_SECURE = True   # only send the session cookie over HTTPS
```

Consider keeping this in a production-specific config or driving it from an env
var so local HTTP development still works.

### 5.5 Use PostgreSQL, not SQLite

SQLite is fine for development but not for concurrent production traffic. Switch
`DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname
```

`psycopg2-binary` is already in `requirements.txt`, and the same migrations work
for both. Run `flask db upgrade` against the new database.

### 5.6 Confirm what's already handled

These are built in — no action needed, but good to know:

- **Password storage:** Werkzeug PBKDF2 hashes (never plaintext).
- **CSRF protection:** enabled globally via Flask-WTF.
- **Open-redirect protection:** the login `next=` parameter is validated to the
  app's own host.
- **Upload limits:** `MAX_CONTENT_LENGTH` caps uploads at 8 MB; images are
  re-encoded via Pillow and stored under random UUID filenames (the original
  filename is never trusted).

### 5.7 Run the test suite

A regression suite (~85 tests) lives in `sol_main/tests/`. Run it after any
customization:

```bash
pip install -r requirements-dev.txt
cd sol_main
pytest
```

---

## 6. Deploying to Production

The app is a standard Flask WSGI application. The entry point is
`create_app()` in `sol_main/app.py`. **Run everything from the `sol_main/`
directory** so blueprint imports resolve.

### 6.1 Gunicorn + Nginx + systemd (self-managed server)

**Install a WSGI server** (add to your environment):

```bash
pip install gunicorn
```

**Run Gunicorn** from `sol_main/`, pointing at the app factory:

```bash
cd sol_main
gunicorn "app:create_app()" --bind 127.0.0.1:8000 --workers 3
```

**systemd unit** (`/etc/systemd/system/directory.service`) to keep it running:

```ini
[Unit]
Description=Contractor/Vendor Directory
After=network.target

[Service]
User=www-data
WorkingDirectory=/srv/yourapp/sol_main
EnvironmentFile=/srv/yourapp/.env
ExecStart=/srv/yourapp/venv/bin/gunicorn "app:create_app()" --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now directory.service
```

**Nginx** as a reverse proxy that terminates TLS and serves static files
directly:

```nginx
server {
    listen 443 ssl;
    server_name directory.example.com;

    # ssl_certificate / ssl_certificate_key ... (e.g. via Let's Encrypt / certbot)

    client_max_body_size 8m;   # match MAX_CONTENT_LENGTH

    location /static/ {
        alias /srv/yourapp/sol_main/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Run `flask db upgrade` once on the server before first start.

### 6.2 Platform-as-a-Service (Heroku, Render, Railway, Fly.io, etc.)

The same `gunicorn "app:create_app()"` command works as a start command. Key
points for any PaaS:

- Set `SECRET_KEY` and `DATABASE_URL` as platform environment variables (not a
  committed `.env`).
- Use the platform's **managed PostgreSQL** add-on for `DATABASE_URL`.
- Run `flask db upgrade` as a release/deploy step.
- **Uploaded images need persistent storage** — see Section 7. Most PaaS
  filesystems are ephemeral and will lose uploads on restart.

A minimal `Procfile`:

```
web: cd sol_main && gunicorn "app:create_app()"
release: cd sol_main && flask db upgrade
```

### 6.3 Docker (optional)

If you prefer containers, a minimal `Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
WORKDIR /app/sol_main
CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8000"]
```

Mount a volume for `sol_main/static/profile_pics/` and use an external database.

---

## 7. Persistent Storage for Uploads

Profile pictures are written to `sol_main/static/profile_pics/` on the local
filesystem (`UPLOAD_FOLDER` in `config.py`). This matters in production:

- **Self-managed server:** ensure that directory is on persistent disk and is
  writable by the service user, and include it in backups.
- **PaaS / containers:** the local filesystem is usually ephemeral. Either
  mount a persistent volume at that path, or modify `_save_image()` /
  `_delete_image()` in `sol_main/blueprints/admin/routes.py` to store images in
  object storage (e.g. S3) and serve via the object store / CDN.

---

## 8. Ongoing Maintenance

### 8.1 Database schema changes

If you modify `models.py`, generate and apply a migration (from `sol_main/`):

```bash
flask db migrate -m "describe the change"
flask db upgrade
```

> Note: per this project's convention, the Alembic version files
> (`sol_main/migrations/versions/*.py`) are git-ignored. If multiple developers
> or environments share a schema, consider **committing** those version files
> instead so history is shared — remove that line from `.gitignore`.

### 8.2 Backups

- **Database:** schedule regular dumps (`pg_dump` for PostgreSQL).
- **Uploads:** back up the `profile_pics/` directory (or rely on object-store
  durability if you moved uploads there).

### 8.3 Dependency updates

Keep dependencies patched, especially Flask, Werkzeug, and Pillow (image
parsing is a common vulnerability surface):

```bash
pip list --outdated
# update requirements.txt, then:
pip install -r requirements.txt
cd sol_main && pytest      # confirm nothing broke
```

---

## 9. Quick Customization Checklist

Copy this into an issue and tick it off:

- [ ] Confirm licensing / permission to use the code
- [ ] Fork or import into your own GitHub org
- [ ] Replace "McBride Construction" name in `layout.html` (title + navbar)
- [ ] Update homepage copy in `templates/main/home.html`
- [ ] Update footer contact email/phone in `layout.html`
- [ ] Set brand colors in `static/main.css` (`.bg-steel`, accent)
- [ ] Replace `static/default_listing.png` and add a logo
- [ ] (Optional) Self-host Bootstrap/jQuery instead of CDNs
- [ ] Replace seed data in `seed.py` or start empty
- [ ] Create a non-default admin account; remove/secure `admin`/`changeme`
- [ ] Generate and set a strong `SECRET_KEY`
- [ ] Switch `DATABASE_URL` to PostgreSQL
- [ ] Add `SESSION_COOKIE_SECURE = True` for HTTPS
- [ ] Deploy under Gunicorn (never `app.run(debug=True)`)
- [ ] Put uploads on persistent storage; set up DB + upload backups
- [ ] Run `pytest` — all green before go-live
