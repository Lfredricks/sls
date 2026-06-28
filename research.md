# McBride Construction — Site Improvement Research

This document assesses the current state of the app and evaluates the best approaches for implementing a database, admin login, search, and profile pictures. Read this before writing any new code.

---

## Pre-existing Bugs to Fix First

These issues will block or complicate every feature below. Fix them before starting anything else.

| Location | Bug | Fix |
|---|---|---|
| `sol_main/blueprints/vend/routes.py:46` | `title=vendors` passes the function object | Change to `title='vendors'` |
| `sol_main/models.py` | `db.model`, `db.Collumn` (x2), `db.string` are typos | Fix to `db.Model`, `db.Column`, `db.String` before uncommenting |
| `sol_main/templates/layout.html` | Sidebar has `FIXME@email.com` and `(206)fix-latr` | Replace with real contact info |
| `sol_main/templates/layout.html:29` | Login link is `href="#"` — goes nowhere | Point to `/admin/login` once auth is built |
| `sol_main/blueprints/admin/` | Both `__init__.py` and `routes.py` are empty; blueprint not registered in `app.py` | Wire up the blueprint (see Admin section) |
| `sol_main/app.py` | SQLAlchemy imports commented out | Uncomment alongside `models.py` when DB is added |

---

## 1. Performance

### Current Bottlenecks

**Four external CDN requests per page load.** `layout.html` loads Bootstrap CSS from `maxcdn.bootstrapcdn.com`, jQuery from `code.jquery.com`, Popper.js from `cdnjs.cloudflare.com`, and Bootstrap JS from `maxcdn.bootstrapcdn.com`. That is four DNS lookups and four round-trips before the page is usable. If any CDN is slow or blocked, the layout breaks entirely.

**No `SECRET_KEY` and `debug=True` hardcoded.** Running with `debug=True` in production adds Werkzeug reloader overhead and is a security risk. More critically, there is no `SECRET_KEY` set anywhere — Flask-Login and session signing will crash without it.

**No caching.** Once database queries are added, every page load will hit the DB even though the contractor/vendor lists change infrequently.

### Recommendations

**Immediate (prerequisite for everything else):**
- Create `config.py` with at minimum `SECRET_KEY`, `DEBUG`, and `SQLALCHEMY_DATABASE_URI`. Load via `app.config.from_object()` in `create_app()`.
- Use `python-dotenv` to load values from a `.env` file so secrets are never hardcoded.

**Short-term:**
- Consider migrating from Bootstrap 4 to Bootstrap 5. Bootstrap 5 drops the jQuery dependency, eliminating one CDN request. The existing templates are simple enough that the class-name changes are low effort. Alternatively, download Bootstrap locally into `static/` to eliminate all four CDN round-trips.

**Once the DB is live:**
- Add `Flask-Caching` to the contractors and vendors list routes. A `SimpleCache` backend (in-process, no extra infrastructure) with a 5-minute TTL is appropriate at this scale. This eliminates repeated DB hits for pages that change infrequently.

**When image uploads are added:**
- Resize images server-side with Pillow before saving. Serving full-resolution browser uploads (often 3–5 MB per photo) directly is the single largest performance risk this app faces. See Section 5.

### Packages for Performance

| Package | Status | Purpose |
|---|---|---|
| `python-dotenv` | Not installed | Load `.env` into `app.config` |
| `Flask-Caching` | Not installed | Route-level caching for listing pages |

---

## 2. Database

### Current State

Data is hardcoded as `posts` lists in `cont/routes.py` and `vend/routes.py`. The five vendor entries are the same businesses as the five contractor entries — the data was clearly copy-pasted. `models.py` has a commented-out `Post` model with three typos and no image field. Flask-SQLAlchemy, Flask-Migrate, and psycopg2 are already installed in the venv.

### Database Choice: SQLite vs. PostgreSQL

**Use SQLite for local development.** Zero configuration, no server to manage, file-based. Appropriate for one developer building and testing locally.

**Plan for PostgreSQL in production.** The presence of `psycopg2-binary 2.9.11` in the venv signals this was already the intent. PostgreSQL handles concurrent writes correctly (important once an admin is actively editing listings), and its native full-text search (`tsvector`) is available if LIKE-based search proves insufficient later.

**How to support both without code changes:** Store the database URI in a `DATABASE_URL` environment variable loaded by `python-dotenv`. This is the convention used by Render, Railway, and Heroku — switching from SQLite to PostgreSQL in production requires changing only the environment variable.

```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///solomon.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### Data Model Design

The existing `Post` model does not distinguish contractors from vendors and is missing several needed fields. Two design options:

**Option A — Single `Listing` table with a `category` column** (`'contractor'` or `'vendor'`). One model, one set of admin routes, one migration. Both listing pages query the same table filtered by category. Best choice if contractors and vendors will always share the same fields (currently true).

**Option B — Separate `Contractor` and `Vendor` tables.** More explicit. Allows the two types to diverge in fields later. Doubles the admin implementation effort.

**Recommendation: Option A.** The current data is structurally identical. The category discriminator is easy to add later if the entities need to diverge.

**Proposed `Listing` model:**

```python
from datetime import datetime
from app import db

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20), nullable=False)  # 'contractor' or 'vendor'
    work_type = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Listing('{self.name}', '{self.category}', '{self.work_type}')"
```

### Migration Workflow

Flask-Migrate (Alembic) is already installed. Once the model is in place and SQLAlchemy is uncommented in `app.py`:

```bash
cd sol_main
flask db init          # one-time setup, creates migrations/ directory
flask db migrate -m "initial listing schema"
flask db upgrade
```

After the DB is live, run a one-time seed to import the hardcoded data, then delete the `posts` lists from the route files.

### Packages for Database

| Package | Version | Status |
|---|---|---|
| `Flask-SQLAlchemy` | 3.1.1 | Already installed |
| `Flask-Migrate` | 4.1.0 | Already installed |
| `psycopg2-binary` | 2.9.11 | Already installed (needed for PostgreSQL only) |

---

## 3. Admin Login

### Approach

McBride Construction is an internal admin tool for one person (or a small team) managing listings. This is **not** a public user registration system. The right pattern is a single admin account seeded into the database — no signup flow, no email verification.

### Authentication: Flask-Login

`Flask-Login 0.6.3` is already installed. It handles:
- Storing the logged-in user in the session
- The `@login_required` decorator for protecting admin routes
- The `current_user` proxy available in templates and routes
- Automatic redirect to the login page on unauthorized access

Flask-Login does not handle passwords or DB queries — that is your responsibility, which keeps it from being opinionated.

**Password hashing:** Use `werkzeug.security.generate_password_hash` and `check_password_hash`. Werkzeug is already installed as a Flask dependency. No additional package needed. Never store plain-text passwords.

### Admin User Model

```python
from flask_login import UserMixin
from app import db

class AdminUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
```

`UserMixin` provides default implementations of `is_authenticated`, `is_active`, `is_anonymous`, and `get_id()` that Flask-Login requires.

### Forms: Flask-WTF

`Flask-WTF 1.2.2` is already installed. Use it for all admin forms — login, add listing, edit listing. Flask-WTF automatically injects CSRF tokens into every form, which is essential for any POST route that modifies data.

A login form:

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
```

### Wiring Up the Admin Blueprint

`admin/__init__.py` needs to follow the same pattern as the other blueprints:

```python
from flask import Blueprint

bp = Blueprint('admin', __name__, url_prefix='/admin')

from blueprints.admin import routes
```

`create_app()` in `app.py` needs to:
1. Import and register the admin blueprint
2. Initialize `Flask-Login`'s `LoginManager`
3. Set `login_manager.login_view = 'admin.login'`

### Route Structure

| Route | Method | Description |
|---|---|---|
| `/admin/login` | GET, POST | Login form |
| `/admin/logout` | GET | Logout and redirect to home |
| `/admin/dashboard` | GET | Overview page (protected) |
| `/admin/listings` | GET | List all listings (protected) |
| `/admin/listings/new` | GET, POST | Add a listing (protected) |
| `/admin/listings/<id>/edit` | GET, POST | Edit a listing (protected) |
| `/admin/listings/<id>/delete` | POST | Delete a listing (protected) |

All routes except `/admin/login` must be decorated with `@login_required`.

### Security Notes

- `SECRET_KEY` in `config.py` is a hard prerequisite. Sessions are signed with it. Without it, Flask-Login crashes.
- Set `SESSION_COOKIE_HTTPONLY = True` and `SESSION_COOKIE_SAMESITE = 'Lax'` in config.
- The login error message should always be a generic "Invalid username or password" — never confirm which field was wrong.

### Packages for Admin Login

| Package | Version | Status |
|---|---|---|
| `Flask-Login` | 0.6.3 | Already installed |
| `Flask-WTF` | 1.2.2 | Already installed |
| `werkzeug.security` | — | Already available (Flask dependency) |

---

## 4. Search

### Approach: Server-Side LIKE Queries

For a construction directory with at most a few hundred listings, server-side filtered queries are the right starting point. No additional search infrastructure needed.

The search bar is a plain `<form method="GET">` with a text input named `q`. The route reads `request.args.get('q', '')` and applies a filter:

```python
from sqlalchemy import or_

q = request.args.get('q', '').strip()
query = Listing.query.filter_by(category='contractor')
if q:
    query = query.filter(
        or_(
            Listing.name.ilike(f'%{q}%'),
            Listing.work_type.ilike(f'%{q}%'),
            Listing.description.ilike(f'%{q}%')
        )
    )
listings = query.all()
```

`ilike` is case-insensitive LIKE and works on both SQLite and PostgreSQL.

### Use GET, Not POST

The search form must use `method="GET"` so the query appears in the URL (`/contractors?q=plumbing`). This makes results bookmarkable and shareable, and means the browser back button works correctly. Never use POST for a search form.

### Placement

The search bar belongs at the top of `contractors.html` and `vendors.html`, above the listing loop. The existing route functions will need to be updated to read `request.args` rather than passing the hardcoded list.

### Work-Type Filter

A work-type dropdown alongside the text search would meaningfully improve usability. Populate it from the distinct `work_type` values in the DB:

```python
work_types = db.session.query(Listing.work_type).filter_by(category='contractor').distinct().all()
```

Worth planning for even if not built in the first pass.

### PostgreSQL Full-Text Search (Optional)

If the listing count grows large and LIKE-based search proves too slow or imprecise, PostgreSQL's `tsvector`/`tsquery` full-text search provides relevance ranking and stemming. This is overkill for a small directory — use it only if needed.

### Packages for Search

No new packages needed for LIKE-based search. SQLAlchemy handles it natively.

---

## 5. Profile Pictures

### Approach: Local Filesystem Storage

Store uploaded images under `sol_main/static/profile_pics/`. The DB stores only the filename. The template generates the URL via `url_for('static', filename='profile_pics/' + listing.image_filename)`.

The CSS already has `.article-img` (65×65px, rounded corners) defined in `main.css` — the styles exist and are waiting for images to exist.

### Why Pillow is Required

Raw file uploads from browsers are unsafe and wasteful:
- Users will upload 4 MB phone photos for a 65×65px thumbnail
- Users can rename non-image files with image extensions

Pillow addresses both:
- `Image.open()` raises an exception if the file is not a valid image — use this to validate before saving
- Resize to a maximum dimension (e.g., 800×800) before saving to cap file size
- Save in a consistent format regardless of what the user uploaded

**Pillow is not currently installed.** It must be added: `pip install Pillow`.

### Filename Handling

Never save files using the user-supplied filename. A filename like `../../app.py` or `<script>.jpg` can be used in path traversal or injection attacks.

The correct approach:
1. Generate a random name: `uuid.uuid4().hex`
2. Append the verified extension from Pillow (e.g., `.jpg`), not from the original filename
3. Save to `static/profile_pics/<uuid>.jpg`

`werkzeug.utils.secure_filename` only sanitizes the original filename — it does not make it safe to use as-is. Use random name generation instead.

### Upload Form

```python
from flask_wtf.file import FileField, FileAllowed

class ListingForm(FlaskForm):
    # ... other fields ...
    image = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only')
    ])
```

The `<form>` tag in the template must have `enctype="multipart/form-data"`. Without this attribute, the file data is not sent.

### Default Image

When `listing.image_filename` is NULL, templates need a fallback:

```html
<img src="{{ url_for('static', filename='profile_pics/' + (listing.image_filename or 'default_listing.png')) }}"
     class="article-img">
```

Place a placeholder image at `static/default_listing.png`.

### File Storage Layout

```
sol_main/static/
    main.css
    default_listing.png       <- new placeholder image
    profile_pics/             <- new directory, gitignored
        <uuid>.jpg
        <uuid>.jpg
```

Add `sol_main/static/profile_pics/` to `.gitignore`. Uploaded images should not be committed to version control.

### Cloud Storage: When It Becomes Necessary

Local filesystem storage will not work on platforms with ephemeral filesystems (Heroku dynos, some serverless platforms) — uploaded files disappear on each deploy. If deploying to such a platform, cloud object storage (AWS S3, Cloudflare R2, Backblaze B2) is needed, with `boto3` for S3.

Design the code so the filename is the only thing stored in the DB regardless of backend. Switching to cloud storage later then only requires changing where the file is written and how the URL is generated — the DB schema and template logic stay the same.

### Packages for Profile Pictures

| Package | Status | Purpose |
|---|---|---|
| `Pillow` | **Not installed** | Image validation and resizing |
| `Flask-WTF` | Already installed | `FileField` and `FileAllowed` validator |

---

## Dependencies Summary

### Already Installed in the Venv

| Package | Version | Purpose |
|---|---|---|
| Flask | 3.1.3 | Core framework |
| Flask-SQLAlchemy | 3.1.1 | ORM |
| Flask-Migrate | 4.1.0 | DB migrations (Alembic) |
| Flask-Login | 0.6.3 | Session-based authentication |
| Flask-WTF | 1.2.2 | Form handling and CSRF protection |
| SQLAlchemy | 2.0.48 | ORM engine |
| psycopg2-binary | 2.9.11 | PostgreSQL adapter |
| Werkzeug | 3.1.6 | Password hashing, request utilities |
| WTForms | 3.2.1 | Form fields and validators |

### Needs to Be Installed

| Package | Purpose |
|---|---|
| `Pillow` | Image validation and resizing for profile picture uploads |
| `Flask-Caching` | Route-level caching for listing pages once DB is live |
| `python-dotenv` | Load `SECRET_KEY` and `DATABASE_URL` from `.env` |

```bash
pip install Pillow Flask-Caching python-dotenv
pip freeze > requirements.txt
```

Note: No `requirements.txt` currently exists. Creating one is a prerequisite for any deployment or collaboration.

---

## Recommended Implementation Order

Each step builds on the previous one. Steps 1–2 are hard prerequisites for everything else.

1. **Fix existing bugs** — vend title bug, models.py typos, sidebar placeholder text
2. **Add `config.py` and `.env`** — `SECRET_KEY` is required before any session/auth work
3. **Enable the database** — uncomment `app.py` and `models.py`, run migrations, seed hardcoded data into DB
4. **Wire up admin blueprint and login** — `__init__.py`, register in `create_app()`, Flask-Login setup, login/logout routes
5. **Add listing CRUD routes** — add/edit/delete behind `@login_required`
6. **Add search** — update contractors/vendors routes to read `request.args`, add search form to templates
7. **Add profile picture upload** — image field in `Listing` model, Pillow resize/save logic, `FileField` in admin form
8. **Generate `requirements.txt`** — `pip freeze > requirements.txt`
