"""Phase 2 — smoke tests: every route returns a sane status code."""
import pytest


# ── Public pages return 200 ─────────────────────────────────────────────────

@pytest.mark.parametrize('path', ['/', '/home', '/contractors', '/vendors'])
def test_public_pages_ok(client, path):
    assert client.get(path).status_code == 200


def test_home_renders_welcome(client):
    resp = client.get('/')
    assert b'Welcome' in resp.data


def test_unknown_url_404s(client):
    assert client.get('/no-such-page').status_code == 404


# ── Public nav no longer exposes a Login link ───────────────────────────────

def test_no_public_login_link(client):
    """The admin login link was intentionally hidden from anonymous users."""
    resp = client.get('/')
    assert b'/admin/login' not in resp.data


# ── Detail routes for empty DB 404 ──────────────────────────────────────────

def test_contractor_detail_missing_404(client):
    assert client.get('/contractors/999').status_code == 404


def test_vendor_detail_missing_404(client):
    assert client.get('/vendors/999').status_code == 404


# ── Protected routes redirect anonymous users to login ──────────────────────

PROTECTED_GET = [
    '/admin/dashboard',
    '/admin/listings',
    '/admin/listings/new',
    '/admin/listings/1/edit',
    '/admin/logout',
]


@pytest.mark.parametrize('path', PROTECTED_GET)
def test_protected_get_redirects_anonymous(client, path):
    resp = client.get(path)
    assert resp.status_code == 302
    assert '/admin/login' in resp.headers['Location']


def test_protected_delete_redirects_anonymous(client):
    resp = client.post('/admin/listings/1/delete')
    assert resp.status_code == 302
    assert '/admin/login' in resp.headers['Location']


# ── Login page is reachable directly (it has no nav link) ────────────────────

def test_login_page_reachable(client):
    resp = client.get('/admin/login')
    assert resp.status_code == 200
    assert b'Username' in resp.data or b'username' in resp.data


# ── Authenticated smoke: protected routes render ────────────────────────────

@pytest.mark.parametrize('path', [
    '/admin/dashboard',
    '/admin/listings',
    '/admin/listings/new',
])
def test_protected_get_ok_when_authed(auth_client, path):
    assert auth_client.get(path).status_code == 200
