# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

All commands must be run from `sol_main/` so blueprint imports resolve correctly.

```bash
cd sol_main
python app.py          # development server at http://localhost:5000
```

Or via Flask CLI (set `FLASK_APP=app.py` if needed):

```bash
cd sol_main
flask run
```

## Database Setup

```bash
cd sol_main
flask db upgrade          # apply migrations (creates the DB on first run)
python seed.py            # seed 5 contractors, 5 vendors, admin user (admin/changeme)
```

```bash
flask db migrate -m "description"   # generate a new migration after changing models.py
flask db downgrade                  # roll back one migration
```

The DB file (`instance/solomon.db`) is gitignored. Migration version files (`migrations/versions/*.py`) are also gitignored — regenerate with `flask db migrate`.

## Environment

Create `solomon/.env` (gitignored) before running:

```env
SECRET_KEY=replace-this-with-a-long-random-string
DATABASE_URL=sqlite:///solomon.db
```

`config.py` calls `load_dotenv(override=True)` — the `override=True` is intentional to prevent a stale shell `DATABASE_URL` from shadowing the `.env` value.

## Architecture

**Application factory:** `sol_main/app.py` → `create_app()`. Extensions (`db`, `migrate`, `login_manager`) are instantiated in `extensions.py` and initialized inside `create_app()` to avoid circular imports.

**Blueprints** (all under `sol_main/blueprints/`):
- `main` — home page (`/`, `/home`)
- `cont` — contractors directory (`/contractors`) with `?q=` and `?work_type=` search
- `vend` — vendors directory (`/vendors`) with same search
- `admin` — auth + full CRUD (`/admin/*`), all routes `@login_required`

**Models** (`models.py`):
- `Listing` — single table for both contractors and vendors; `category` column is `'contractor'` or `'vendor'`
- `AdminUser` — single admin account with `UserMixin`; password stored as Werkzeug PBKDF2 hash

**`import models` in `create_app()`** is required so SQLAlchemy metadata is populated before Alembic introspects it during migrations.

**Admin blueprint** (`blueprints/admin/`):
- `forms.py` — `LoginForm`, `ListingForm` (Flask-WTF with CSRF)
- `routes.py` — login/logout, dashboard, listings list, new/edit/delete; `_save_image()` uses Pillow to validate, resize to max 800×800, and save as JPEG with a UUID filename; `_delete_image()` removes old files on replace/delete

**Search:** GET-based forms with SQLAlchemy `ilike` across `name`, `work_type`, and `description`. Results are bookmarkable.

**Profile pictures:** Uploaded images go to `static/profile_pics/` (gitignored). Filenames are `uuid4().hex + '.jpg'` — never user-supplied. Listings without an image fall back to `static/default_listing.png`.

## Key Files

| File | Purpose |
|---|---|
| `config.py` | Loads `.env`, sets `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, `UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH` (8 MB) |
| `extensions.py` | Shared `db`, `migrate`, `login_manager` instances |
| `models.py` | `Listing` and `AdminUser` ORM models |
| `seed.py` | One-time seed script; idempotent (skips if data exists) |
| `templates/layout.html` | Base template (Bootstrap 4); flash messages block included |
