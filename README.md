# McBride Construction — Hardcoded Demo

A Flask web application that serves as a directory of approved contractors and vendors in the construction industry. Public users can browse and search listings; an admin login provides full control over adding, editing, and removing entries.

> **This is the `hardcoded-demo` branch.** It runs with **no database** — all data
> lives in an in-memory Python list (`sol_main/data.py`). It's meant to show off
> every feature with zero setup: no migrations, no seeding, no environment beyond a
> secret key. Admin add/edit/delete work, but changes persist only while the server
> is running and **reset on restart**. For the full database-backed application
> (SQLite/PostgreSQL, Alembic migrations, image uploads), see the `main` branch.

---

## Features

- **Public contractor and vendor directories** — browse all listings with contact details
- **Search and filter** — search by name, description, or work type; dropdown filter by specialty
- **Admin panel** — protected dashboard for managing all listings
- **Full CRUD** — add, edit, and delete contractors and vendors through a web form (in-memory)
- **Bundled listing images** — sample listings ship with their own images under `static/demo_pics/`
- **Zero setup** — no database, migrations, or seed step required

---

## Project Layout

```
solomon/
├── .env                        # Local secret (not committed)
├── .gitignore
├── requirements.txt
└── sol_main/                   # Application root (run everything from here)
    ├── app.py                  # Application factory (create_app)
    ├── config.py               # Config class — loads SECRET_KEY from .env
    ├── extensions.py           # LoginManager, CSRFProtect instances
    ├── data.py                 # In-memory listings + admin user (replaces the DB)
    ├── blueprints/
    │   ├── main/               # Home page  /
    │   ├── cont/               # Contractors  /contractors
    │   ├── vend/               # Vendors  /vendors
    │   └── admin/              # Admin panel  /admin/*
    │       ├── forms.py        # LoginForm, ListingForm (Flask-WTF)
    │       └── routes.py       # Auth + CRUD routes
    ├── templates/
    │   ├── layout.html         # Base template (Bootstrap 4, Apple-style CSS)
    │   ├── main/  cont/  vend/  admin/
    └── static/
        ├── main.css
        ├── default_listing.png # Placeholder for listings with no image
        └── demo_pics/          # Bundled images for the sample listings
```

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd solomon
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure the secret key

Copy the example into `.env` at the project root:

```env
SECRET_KEY=replace-this-with-a-long-random-string
```

`SECRET_KEY` signs sessions and CSRF tokens. If unset, a dev fallback is used.

### 3. Start the development server

```bash
cd sol_main
python app.py
```

The app runs at `http://localhost:5000`. Data is loaded into memory on startup —
there is no database or seed step.

---

## Admin Panel

Navigate to `http://localhost:5000/admin/login` and sign in with the built-in
demo account:

- **username:** `admin`
- **password:** `changeme`

| Route | Description |
|---|---|
| `/admin/login` | Login form |
| `/admin/logout` | End session |
| `/admin/dashboard` | Overview — listing counts and recent additions |
| `/admin/listings` | Full listing table with edit/delete controls |
| `/admin/listings/new` | Add a contractor or vendor |
| `/admin/listings/<id>/edit` | Edit an existing listing |
| `/admin/listings/<id>/delete` | Delete a listing (POST only) |

All routes except `/admin/login` require an authenticated session. Unauthenticated
requests are redirected to the login page. **Changes are in-memory and reset when
the server restarts.**

---

## Data (in memory)

There is no ORM on this branch. `sol_main/data.py` defines plain Python objects and
a repository API.

### `Listing` (attributes)

| Field | Notes |
|---|---|
| `id` | Auto-incrementing integer |
| `name` | Business name |
| `description` | |
| `category` | `'contractor'` or `'vendor'` |
| `work_type` | e.g. `Plumbing`, `Electrical` |
| `phone` | |
| `email` | |
| `website` | Optional |
| `image_filename` | Static-relative path (e.g. `demo_pics/abc.jpg`) or `None` for the default image |
| `date_added` | Set on creation |

### `AdminUser`

A single hardcoded account (`admin` / `changeme`), `UserMixin`-based, with the
password hashed via Werkzeug at startup.

### Repository functions

`search`, `get`, `distinct_work_types`, `counts`, `recent`, `all_listings`,
`add`, `update`, `delete`, `get_user_by_id`, `get_user_by_username`.

---

## Search

Both the `/contractors` and `/vendors` pages accept query parameters:

| Parameter | Description |
|---|---|
| `q` | Free-text search — matches name, work type, and description (case-insensitive) |
| `work_type` | Filter to an exact work type value |

Example: `/contractors?q=plumbing&work_type=Plumbing`

Results are bookmarkable. The work-type dropdown is populated dynamically from the
in-memory listings.

---

## Images

On this branch there is **no upload feature**. The sample listings reference
bundled images committed under `static/demo_pics/`. Any listing created through
the admin form has no image and falls back to `static/default_listing.png`.

---

## Changing the Admin Credentials

Edit the hardcoded account near the top of `sol_main/data.py`:

```python
ADMIN = AdminUser(1, 'admin', 'changeme')
```

---

## Key Dependencies

| Package | Purpose |
|---|---|
| Flask 3.1 | Web framework |
| Flask-Login | Session-based authentication |
| Flask-WTF | CSRF-protected forms |
| python-dotenv | Load `.env` into config |
| Werkzeug | Password hashing |
