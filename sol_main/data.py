"""
Hardcoded, in-memory data store for the demo branch — no database.

Listings live in a plain Python list. CRUD mutates that list, so changes
persist for the lifetime of the running server and reset on restart.
Auth uses a single hardcoded admin account (admin / changeme).
"""
from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class Listing:
    """Plain stand-in for the old SQLAlchemy model (attribute access only)."""

    def __init__(self, id, name, description, category, work_type,
                 phone, email, website=None, image_filename=None, date_added=None):
        self.id = id
        self.name = name
        self.description = description
        self.category = category  # 'contractor' or 'vendor'
        self.work_type = work_type
        self.phone = phone
        self.email = email
        self.website = website
        # static-relative path, e.g. 'demo_pics/abc.jpg'; None -> default image
        self.image_filename = image_filename
        self.date_added = date_added or datetime.utcnow()

    def __repr__(self):
        return f"Listing('{self.name}', '{self.category}', '{self.work_type}')"


class AdminUser(UserMixin):
    """Single hardcoded admin. id is fixed at 1 for the Flask-Login user_loader."""

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


ADMIN = AdminUser(1, 'admin', 'changeme')


def _seed():
    """Build the initial in-memory listings. Newest first via staggered dates."""
    base = datetime(2026, 1, 1, 12, 0, 0)
    rows = [
        # contractors
        ('ABC Contractors',
         'ABC Contractors has been serving the greater Seattle area for over 20 years. '
         'Specializing in residential and commercial builds.',
         'contractor', 'General Contractors', '(123) 456-7891',
         'contact@abccontractors.com', 'https://abccontractors.com',
         'demo_pics/abc_contractors.jpg'),
        ('Pacific Plumbing Co.',
         'Pacific Plumbing offers 24/7 emergency services for all your plumbing needs. '
         'Licensed and insured with over 15 years of experience.',
         'contractor', 'Plumbing', '(206) 555-1234',
         'info@pacificplumbing.com', None, 'demo_pics/pacific_plumbing.jpg'),
        ('Summit Electrical',
         'Summit Electrical provides residential and commercial electrical services. '
         'From panel upgrades to full rewires, we do it all.',
         'contractor', 'Electrical', '(425) 555-9876',
         'service@summitelectrical.com', None, 'demo_pics/summit_electrical.jpg'),
        ('Cascade Roofing',
         'Cascade Roofing specializes in roof installation, repair, and replacement. '
         'Free inspections and estimates available.',
         'contractor', 'Roofing', '(253) 555-4321',
         'hello@cascaderoofing.com', None, 'demo_pics/cascade_roofing.jpg'),
        ('Northwest Landscaping',
         'Northwest Landscaping transforms outdoor spaces with custom design, '
         'installation, and maintenance services year round.',
         'contractor', 'Landscaping', '(360) 555-6789',
         'info@nwlandscaping.com', None, 'demo_pics/nw_landscaping.jpg'),
        # vendors
        ('ABC Building Supply',
         'ABC Building Supply stocks everything from lumber to hardware for residential '
         'and commercial projects throughout the Seattle area.',
         'vendor', 'Building Materials', '(123) 456-7891',
         'contact@abcbuildingsupply.com', 'https://abcbuildingsupply.com',
         'demo_pics/abc_supply.jpg'),
        ('Pacific Pipe & Fittings',
         'Pacific Pipe & Fittings supplies commercial and residential plumbing materials. '
         'Same-day availability on most standard stock.',
         'vendor', 'Plumbing Supplies', '(206) 555-1234',
         'info@pacificpipe.com', None, 'demo_pics/pacific_pipe.jpg'),
        ('Summit Electrical Supply',
         'Summit Electrical Supply carries a full line of electrical components, panels, '
         'and wiring for contractors and DIYers alike.',
         'vendor', 'Electrical Supplies', '(425) 555-9876',
         'service@summitelectricalsupply.com', None, 'demo_pics/summit_supply.jpg'),
        ('Cascade Roofing Materials',
         'Cascade Roofing Materials provides shingles, underlayment, flashing, and all '
         'accessory roofing products at competitive prices.',
         'vendor', 'Roofing Supplies', '(253) 555-4321',
         'hello@cascaderoofingmaterials.com', None, 'demo_pics/cascade_materials.jpg'),
        ('Northwest Garden & Landscape',
         'Northwest Garden & Landscape supplies plants, soil, gravel, and hardscape '
         'materials for landscape contractors and homeowners.',
         'vendor', 'Landscaping Supplies', '(360) 555-6789',
         'info@nwgardenlandscape.com', None, 'demo_pics/nw_garden.jpg'),
    ]
    listings = []
    for i, (name, desc, cat, wt, phone, email, website, img) in enumerate(rows, start=1):
        listings.append(Listing(
            id=i, name=name, description=desc, category=cat, work_type=wt,
            phone=phone, email=email, website=website, image_filename=img,
            date_added=base + timedelta(minutes=i),
        ))
    return listings


_LISTINGS = _seed()
_next_id = len(_LISTINGS) + 1


# ── Auth ────────────────────────────────────────────────────────────────────

def get_user_by_id(user_id):
    return ADMIN if str(user_id) == str(ADMIN.id) else None


def get_user_by_username(username):
    return ADMIN if username == ADMIN.username else None


# ── Reads ───────────────────────────────────────────────────────────────────

def search(category, q='', work_type=''):
    """Replicates the old ilike/work_type filter; newest first."""
    results = [l for l in _LISTINGS if l.category == category]
    if q:
        needle = q.lower()
        results = [l for l in results
                   if needle in l.name.lower()
                   or needle in l.work_type.lower()
                   or needle in l.description.lower()]
    if work_type:
        results = [l for l in results if l.work_type == work_type]
    return sorted(results, key=lambda l: l.date_added, reverse=True)


def get(listing_id, category=None):
    for l in _LISTINGS:
        if l.id == listing_id and (category is None or l.category == category):
            return l
    return None


def distinct_work_types(category):
    return sorted({l.work_type for l in _LISTINGS if l.category == category})


def counts():
    contractors = sum(1 for l in _LISTINGS if l.category == 'contractor')
    vendors = sum(1 for l in _LISTINGS if l.category == 'vendor')
    return contractors, vendors


def recent(n=5):
    return sorted(_LISTINGS, key=lambda l: l.date_added, reverse=True)[:n]


def all_listings(category=None):
    rows = _LISTINGS if category is None else [l for l in _LISTINGS if l.category == category]
    return sorted(rows, key=lambda l: l.date_added, reverse=True)


# ── Writes (in-memory; reset on restart) ─────────────────────────────────────

def add(**kwargs):
    global _next_id
    listing = Listing(id=_next_id, **kwargs)
    _next_id += 1
    _LISTINGS.append(listing)
    return listing


def update(listing_id, **kwargs):
    listing = get(listing_id)
    if listing is None:
        return None
    for key, value in kwargs.items():
        setattr(listing, key, value)
    return listing


def delete(listing_id):
    listing = get(listing_id)
    if listing is not None:
        _LISTINGS.remove(listing)
    return listing
