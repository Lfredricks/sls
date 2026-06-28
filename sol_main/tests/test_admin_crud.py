"""Phase 5 — admin CRUD (no image; image pipeline lives in test_images.py)."""
from extensions import db
from models import Listing


def form_data(**overrides):
    """Valid ListingForm payload; override individual fields via kwargs."""
    data = dict(
        name='New Co',
        category='contractor',
        work_type='Plumbing',
        description='Reliable plumbing services.',
        phone='555-0199',
        email='new@example.com',
        website='',
    )
    data.update(overrides)
    return data


# ── Dashboard ───────────────────────────────────────────────────────────────

def test_dashboard_counts_and_recent(auth_client, make_listing):
    make_listing(category='contractor', name='C-One')
    make_listing(category='contractor', name='C-Two')
    make_listing(category='vendor', name='V-One')
    resp = auth_client.get('/admin/dashboard')
    assert resp.status_code == 200
    # Recent listings table shows the names.
    assert b'C-One' in resp.data
    assert b'V-One' in resp.data


def test_dashboard_recent_capped_at_five(auth_client, make_listing):
    for i in range(7):
        make_listing(category='contractor', name=f'Listing-{i}')
    resp = auth_client.get('/admin/dashboard')
    # Newest 5 only (route uses .limit(5)).
    shown = [f'Listing-{i}'.encode() in resp.data for i in range(7)]
    assert sum(shown) == 5


# ── Listings list filter ────────────────────────────────────────────────────

def test_listings_filter_by_category(auth_client, make_listing):
    make_listing(category='contractor', name='ConListed')
    make_listing(category='vendor', name='VenListed')
    resp = auth_client.get('/admin/listings?category=vendor')
    assert b'VenListed' in resp.data
    assert b'ConListed' not in resp.data


def test_listings_invalid_category_shows_all(auth_client, make_listing):
    make_listing(category='contractor', name='ConListed')
    make_listing(category='vendor', name='VenListed')
    resp = auth_client.get('/admin/listings?category=bogus')
    assert b'ConListed' in resp.data
    assert b'VenListed' in resp.data


# ── Create ──────────────────────────────────────────────────────────────────

def test_new_listing_creates_row(auth_client, app):
    resp = auth_client.post('/admin/listings/new', data=form_data(name='Created Co'),
                            follow_redirects=True)
    assert resp.status_code == 200
    assert b'added successfully' in resp.data
    with app.app_context():
        assert Listing.query.filter_by(name='Created Co').count() == 1


def test_new_listing_blank_website_stored_as_none(auth_client, app):
    auth_client.post('/admin/listings/new', data=form_data(name='NoWeb', website=''))
    with app.app_context():
        listing = Listing.query.filter_by(name='NoWeb').first()
        assert listing.website is None


def test_new_listing_accepts_unvalidated_email(auth_client, app):
    """Regression: the Email() validator was removed; any string is accepted."""
    resp = auth_client.post('/admin/listings/new',
                            data=form_data(name='OddEmail', email='not-an-email'),
                            follow_redirects=True)
    assert b'added successfully' in resp.data
    with app.app_context():
        assert Listing.query.filter_by(name='OddEmail').first().email == 'not-an-email'


def test_new_listing_missing_required_field_rerenders(auth_client, app):
    resp = auth_client.post('/admin/listings/new', data=form_data(name=''))
    assert resp.status_code == 200          # re-rendered, not redirected
    assert b'added successfully' not in resp.data
    with app.app_context():
        assert Listing.query.count() == 0   # nothing written


def test_new_listing_invalid_website_rejected(auth_client, app):
    resp = auth_client.post('/admin/listings/new',
                            data=form_data(name='BadURL', website='not a url'))
    assert resp.status_code == 200
    with app.app_context():
        assert Listing.query.filter_by(name='BadURL').count() == 0


# ── Edit ────────────────────────────────────────────────────────────────────

def test_edit_get_prefills_form(auth_client, make_listing):
    cid = make_listing(name='Original Name', work_type='Roofing')
    resp = auth_client.get(f'/admin/listings/{cid}/edit')
    assert resp.status_code == 200
    assert b'Original Name' in resp.data


def test_edit_updates_fields(auth_client, app, make_listing):
    cid = make_listing(name='Before')
    resp = auth_client.post(f'/admin/listings/{cid}/edit',
                            data=form_data(name='After'), follow_redirects=True)
    assert b'updated successfully' in resp.data
    with app.app_context():
        assert db.session.get(Listing, cid).name == 'After'


def test_edit_missing_listing_404s(auth_client):
    assert auth_client.post('/admin/listings/9999/edit',
                            data=form_data()).status_code == 404


# ── Delete ──────────────────────────────────────────────────────────────────

def test_delete_removes_row(auth_client, app, make_listing):
    cid = make_listing(name='Doomed')
    resp = auth_client.post(f'/admin/listings/{cid}/delete', follow_redirects=True)
    assert b'deleted' in resp.data
    with app.app_context():
        assert db.session.get(Listing, cid) is None


def test_delete_missing_listing_404s(auth_client):
    assert auth_client.post('/admin/listings/9999/delete').status_code == 404


def test_delete_via_get_not_allowed(auth_client, make_listing):
    cid = make_listing(name='Safe')
    assert auth_client.get(f'/admin/listings/{cid}/delete').status_code == 405
