"""Phase 6 — model behavior."""
from datetime import datetime

from extensions import db
from models import AdminUser, Listing


# ── AdminUser password hashing ──────────────────────────────────────────────

def test_password_round_trips(app):
    with app.app_context():
        u = AdminUser(username='someone')
        u.set_password('s3cret')
        assert u.check_password('s3cret')
        assert not u.check_password('wrong')


def test_password_is_hashed_not_plaintext(app):
    with app.app_context():
        u = AdminUser(username='someone')
        u.set_password('s3cret')
        assert u.password_hash != 's3cret'
        assert 's3cret' not in u.password_hash


# ── Listing defaults & repr ─────────────────────────────────────────────────

def test_date_added_defaults_on_insert(app):
    with app.app_context():
        listing = Listing(name='X', description='d', category='contractor',
                          work_type='Plumbing', phone='1', email='e@e.com')
        db.session.add(listing)
        db.session.commit()
        assert isinstance(listing.date_added, datetime)


def test_optional_columns_default_to_none(app):
    with app.app_context():
        listing = Listing(name='X', description='d', category='contractor',
                          work_type='Plumbing', phone='1', email='e@e.com')
        db.session.add(listing)
        db.session.commit()
        assert listing.website is None
        assert listing.image_filename is None


def test_listing_repr(app):
    with app.app_context():
        listing = Listing(name='Acme', category='vendor', work_type='Lumber')
        assert repr(listing) == "Listing('Acme', 'vendor', 'Lumber')"


def test_adminuser_repr(app):
    with app.app_context():
        assert repr(AdminUser(username='boss')) == "AdminUser('boss')"
