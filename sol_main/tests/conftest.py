"""Shared pytest fixtures for the Solomon test suite.

Run from ``sol_main/``::

    cd sol_main && pytest
"""
import os
import sys

import pytest

# Ensure sol_main/ (one level up from tests/) is importable so that the
# blueprint imports (``from blueprints... import bp``, ``import models``)
# resolve the same way they do when the app runs.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from config import TestConfig  # noqa: E402
from extensions import db as _db  # noqa: E402
from models import AdminUser, Listing  # noqa: E402


ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'test-password'


@pytest.fixture
def app(tmp_path):
    """A fresh app + in-memory database for each test.

    UPLOAD_FOLDER is pointed at a per-test temp dir so nothing touches
    static/profile_pics/.
    """
    class _Config(TestConfig):
        UPLOAD_FOLDER = str(tmp_path / 'profile_pics')

    app = create_app(_Config)

    with app.app_context():
        _db.create_all()
        # Seed a known admin so auth_client and login tests have credentials.
        admin = AdminUser(username=ADMIN_USERNAME)
        admin.set_password(ADMIN_PASSWORD)
        _db.session.add(admin)
        _db.session.commit()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Anonymous test client."""
    return app.test_client()


@pytest.fixture
def csrf_client(tmp_path):
    """Anonymous client on an app with CSRF protection ENABLED.

    The default `app` fixture disables CSRF for convenience; this one keeps it
    on so the CSRF-enforcement tests are meaningful.
    """
    class _Config(TestConfig):
        WTF_CSRF_ENABLED = True
        UPLOAD_FOLDER = str(tmp_path / 'profile_pics')

    app = create_app(_Config)
    with app.app_context():
        _db.create_all()
        yield app.test_client()
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    """The SQLAlchemy handle, inside an app context."""
    with app.app_context():
        yield _db


@pytest.fixture
def auth_client(app):
    """A test client already logged in as the seeded admin."""
    client = app.test_client()
    client.post(
        '/admin/login',
        data={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD},
        follow_redirects=True,
    )
    return client


@pytest.fixture
def make_listing(app):
    """Factory that inserts a Listing and returns its id.

    Returning the id (rather than the ORM instance) keeps callers free of
    DetachedInstanceError once the insert's app context closes. Tests that
    need the object can ``db.session.get(Listing, id)`` inside their own
    app context. Sensible defaults; override any field via kwargs.
    """
    def _make(**kwargs):
        defaults = dict(
            name='Acme Co',
            description='General services and repair work.',
            category='contractor',
            work_type='Plumbing',
            phone='555-0100',
            email='acme@example.com',
            website=None,
            image_filename=None,
        )
        defaults.update(kwargs)
        with app.app_context():
            listing = Listing(**defaults)
            _db.session.add(listing)
            _db.session.commit()
            return listing.id

    return _make
