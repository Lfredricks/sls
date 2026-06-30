# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Branch note — `hardcoded-demo`:** This branch is a database-free demo. All
> listings live in an in-memory Python list (`sol_main/data.py`), and admin login
> uses a single hardcoded account. There is **no database, no migrations, no
> seeding, and no image upload**. Admin add/edit/delete work but persist only for
> the lifetime of the running server — they **reset on restart**. See the `main`
> branch for the full database-backed app.

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

No database or seed step is required — data is hardcoded and loaded on import.

## Admin Login

A single hardcoded admin account is built in `data.py`:

- **username:** `admin`
- **password:** `changeme`

## Environment

Create `.env` at the project root (gitignored) before running:

```env
SECRET_KEY=replace-this-with-a-long-random-string
```

`config.py` calls `load_dotenv(override=True)`. `SECRET_KEY` signs sessions and
CSRF tokens; a dev fallback is used if unset.

## Architecture

**Application factory:** `sol_main/app.py` → `create_app()`. Extensions
(`login_manager`, `csrf`) are instantiated in `extensions.py` and initialized
inside `create_app()` to avoid circular imports.

**Blueprints** (all under `sol_main/blueprints/`):
- `main` — home page (`/`, `/home`)
- `cont` — contractors directory (`/contractors`) with `?q=` and `?work_type=` search
- `vend` — vendors directory (`/vendors`) with same search
- `admin` — auth + full CRUD (`/admin/*`), all routes `@login_required`

**Data layer** (`data.py`) — replaces the database on this branch:
- `Listing` — a plain Python class (attribute access only); `category` is `'contractor'` or `'vendor'`. `image_filename` holds a static-relative path (e.g. `demo_pics/abc.jpg`) or `None` to fall back to the default image.
- `AdminUser` — single hardcoded admin (`UserMixin`); password hashed with Werkzeug at startup.
- `_LISTINGS` — the in-memory store, seeded by `_seed()` at import time (5 contractors + 5 vendors).
- Repository functions: `search`, `get`, `distinct_work_types`, `counts`, `recent`, `all_listings`, `add`, `update`, `delete`, `get_user_by_id`, `get_user_by_username`.

**Admin blueprint** (`blueprints/admin/`):
- `forms.py` — `LoginForm`, `ListingForm` (Flask-WTF with CSRF). No image field.
- `routes.py` — login/logout, dashboard, listings list, new/edit/delete. CRUD calls the `data.*` repository functions; mutations are in-memory only.

**Search:** GET-based forms; `data.search()` does case-insensitive substring
matching across `name`, `work_type`, and `description`. Results are bookmarkable.

**Profile pictures:** Each seeded listing references a bundled image under
`static/demo_pics/` (committed). Listings created via the admin form have no
image and fall back to `static/default_listing.png`. There is no upload feature
on this branch.

## Key Files

| File | Purpose |
|---|---|
| `config.py` | Loads `.env`, sets `SECRET_KEY` and session cookie flags |
| `extensions.py` | Shared `login_manager`, `csrf` instances |
| `data.py` | In-memory `Listing`/`AdminUser` data + repository functions (no DB) |
| `static/demo_pics/` | Bundled listing images referenced by the seeded data |
| `templates/layout.html` | Base template (Bootstrap 4); flash messages block included |
