# McBride Construction

A Flask web application that serves as a directory of approved contractors and vendors in the construction industry. Public users can browse and search listings; an admin login provides full control over adding, editing, and removing entries including profile pictures.

---

## Features

- **Public contractor and vendor directories** — browse all approved listings with contact details
- **Search and filter** — live search by name, description, or work type; dropdown filter by specialty
- **Admin panel** — protected dashboard for managing all listings
- **Full CRUD** — add, edit, and delete contractors and vendors through a web form
- **Profile picture uploads** — images are validated, resized, and stored server-side
- **SQLite database** (dev) with a one-command switch to PostgreSQL for production

---

## Project Layout

```
solomon/
├── .env                        # Local secrets (not committed)
├── .gitignore
├── requirements.txt
├── research.md                 # Feature assessment and implementation notes
└── sol_main/                   # Application root (run everything from here)
    ├── app.py                  # Application factory (create_app)
    ├── config.py               # Config class — loads from .env
    ├── extensions.py           # SQLAlchemy, Migrate, LoginManager instances
    ├── models.py               # Listing and AdminUser models
    ├── seed.py                 # One-time DB seed script
    ├── blueprints/
    │   ├── main/               # Home page  /
    │   ├── cont/               # Contractors  /contractors
    │   ├── vend/               # Vendors  /vendors
    │   └── admin/              # Admin panel  /admin/*
    │       ├── forms.py        # LoginForm, ListingForm (Flask-WTF)
    │       └── routes.py       # Auth + CRUD routes
    ├── templates/
    │   ├── layout.html         # Base template (Bootstrap 4, Apple-style CSS)
    │   ├── main/
    │   ├── cont/
    │   ├── vend/
    │   └── admin/              # login, dashboard, listings, listing_form
    ├── static/
    │   ├── main.css
    │   ├── default_listing.png # Placeholder for listings with no image
    │   └── profile_pics/       # Uploaded images (gitignored)
    └── migrations/             # Alembic migration history
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

### 2. Configure environment variables

Copy the example below into `solomon/.env` and set a strong secret key:

```env
SECRET_KEY=replace-this-with-a-long-random-string
DATABASE_URL=sqlite:///solomon.db
```

For production with PostgreSQL:

```env
SECRET_KEY=replace-this-with-a-long-random-string
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname
```

### 3. Run database migrations

```bash
cd sol_main
flask db upgrade
```

### 4. Seed initial data

Creates 5 sample contractors, 5 sample vendors, and an admin account (`admin` / `changeme`).

```bash
python seed.py
```

**Change the admin password** after first login — see [Changing the Admin Password](#changing-the-admin-password).

### 5. Start the development server

```bash
python app.py
```

The app runs at `http://localhost:5000`.

---

## Admin Panel

Navigate to `http://localhost:5000/admin/login`.

| Route | Description |
|---|---|
| `/admin/login` | Login form |
| `/admin/logout` | End session |
| `/admin/dashboard` | Overview — listing counts and recent additions |
| `/admin/listings` | Full listing table with edit/delete controls |
| `/admin/listings/new` | Add a contractor or vendor |
| `/admin/listings/<id>/edit` | Edit an existing listing and upload/replace a photo |
| `/admin/listings/<id>/delete` | Delete a listing (POST only) |

All routes except `/admin/login` require an authenticated session. Unauthenticated requests are redirected to the login page.

---

## Data Model

### `Listing`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `name` | String(100) | Business name |
| `description` | Text | |
| `category` | String(20) | `'contractor'` or `'vendor'` |
| `work_type` | String(50) | e.g. `Plumbing`, `Electrical` |
| `phone` | String(20) | |
| `email` | String(120) | |
| `website` | String(200) | Optional |
| `image_filename` | String(200) | UUID filename stored in `static/profile_pics/` |
| `date_added` | DateTime | Auto-set on creation |

### `AdminUser`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `username` | String(80) | Unique |
| `password_hash` | String(256) | Werkzeug PBKDF2 hash |

---

## Search

Both the `/contractors` and `/vendors` pages accept query parameters:

| Parameter | Description |
|---|---|
| `q` | Free-text search — matches name, work type, and description (case-insensitive) |
| `work_type` | Filter to an exact work type value |

Example: `/contractors?q=plumbing&work_type=Plumbing`

Results are bookmarkable. The work-type dropdown is populated dynamically from the values in the database.

---

## Profile Pictures

Images are uploaded through the admin listing form. The server:

1. Opens the file with Pillow to confirm it is a valid image
2. Converts to RGB and resizes to a maximum of 800×800 pixels
3. Saves as JPEG at 85% quality using a random UUID filename
4. Stores the filename in the `image_filename` column

The original uploaded filename is never used. Supported input formats: JPG, PNG, GIF. Maximum upload size is 8 MB (enforced by Flask via `MAX_CONTENT_LENGTH`).

When a listing is deleted or its image is replaced, the old file is removed from disk.

---

## Database Migrations

This project uses Flask-Migrate (Alembic). All commands must be run from `sol_main/`:

```bash
# Create a new migration after changing models.py
flask db migrate -m "describe the change"

# Apply pending migrations
flask db upgrade

# Roll back one migration
flask db downgrade
```

---

## Switching to PostgreSQL

1. Install and start a PostgreSQL server
2. Create a database and user
3. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
   ```
4. Run `flask db upgrade` — the same migration files work for both SQLite and PostgreSQL
5. Run `python seed.py` if starting fresh

`psycopg2-binary` is already included in `requirements.txt`.

---

## Changing the Admin Password

Open a Flask shell from `sol_main/`:

```bash
flask shell
```

```python
from extensions import db
from models import AdminUser

user = AdminUser.query.filter_by(username='admin').first()
user.set_password('your-new-strong-password')
db.session.commit()
```

---

## Key Dependencies

| Package | Purpose |
|---|---|
| Flask 3.1 | Web framework |
| Flask-SQLAlchemy | ORM |
| Flask-Migrate | Schema migrations via Alembic |
| Flask-Login | Session-based authentication |
| Flask-WTF | CSRF-protected forms |
| Pillow | Image validation and resizing |
| python-dotenv | Load `.env` into config |
| psycopg2-binary | PostgreSQL adapter |
| Werkzeug | Password hashing |
