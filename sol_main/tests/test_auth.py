"""Phase 4 — authentication and access control."""
from conftest import ADMIN_USERNAME, ADMIN_PASSWORD


# ── Login: happy path ───────────────────────────────────────────────────────

def test_login_get_renders_form(client):
    resp = client.get('/admin/login')
    assert resp.status_code == 200
    assert b'Admin Login' in resp.data


def test_login_valid_redirects_to_dashboard(client):
    resp = client.post('/admin/login',
                       data={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD})
    assert resp.status_code == 302
    assert '/admin/dashboard' in resp.headers['Location']


def test_login_valid_establishes_session(client):
    client.post('/admin/login',
                data={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD})
    # A subsequent protected request now succeeds without redirect.
    assert client.get('/admin/dashboard').status_code == 200


# ── Login: failure paths ────────────────────────────────────────────────────

def test_login_wrong_password_flashes_error(client):
    resp = client.post('/admin/login',
                       data={'username': ADMIN_USERNAME, 'password': 'nope'},
                       follow_redirects=True)
    assert resp.status_code == 200
    assert b'Invalid username or password' in resp.data


def test_login_unknown_user_flashes_error(client):
    resp = client.post('/admin/login',
                       data={'username': 'ghost', 'password': 'whatever'},
                       follow_redirects=True)
    assert b'Invalid username or password' in resp.data


def test_login_wrong_password_does_not_authenticate(client):
    client.post('/admin/login',
                data={'username': ADMIN_USERNAME, 'password': 'nope'})
    resp = client.get('/admin/dashboard')
    assert resp.status_code == 302
    assert '/admin/login' in resp.headers['Location']


def test_login_missing_fields_rerenders(client):
    resp = client.post('/admin/login', data={'username': '', 'password': ''})
    assert resp.status_code == 200  # form re-rendered, not redirected


# ── Already-authenticated short-circuit ─────────────────────────────────────

def test_login_get_when_authed_redirects(auth_client):
    resp = auth_client.get('/admin/login')
    assert resp.status_code == 302
    assert '/admin/dashboard' in resp.headers['Location']


# ── next= redirect ──────────────────────────────────────────────────────────

def test_login_honors_internal_next(client):
    resp = client.post('/admin/login?next=/admin/listings',
                       data={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/admin/listings')


def test_login_rejects_external_next(client):
    """A malicious next= pointing off-site must NOT be followed; falls back
    to the dashboard instead (open-redirect mitigation)."""
    evil = 'http://evil.example/phish'
    resp = client.post(f'/admin/login?next={evil}',
                       data={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD})
    assert 'evil.example' not in resp.headers['Location']
    assert '/admin/dashboard' in resp.headers['Location']


def test_login_rejects_protocol_relative_next(client):
    """`//evil.example` is protocol-relative and must also be rejected."""
    resp = client.post('/admin/login?next=//evil.example/phish',
                       data={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD})
    assert 'evil.example' not in resp.headers['Location']
    assert '/admin/dashboard' in resp.headers['Location']


# ── Logout ──────────────────────────────────────────────────────────────────

def test_logout_redirects_home(auth_client):
    resp = auth_client.get('/admin/logout')
    assert resp.status_code == 302
    # main.home is registered on both '/' and '/home'; url_for picks '/home'.
    assert resp.headers['Location'].rstrip('/').endswith('/home') \
        or resp.headers['Location'].endswith('/')


def test_logout_clears_session(auth_client):
    auth_client.get('/admin/logout')
    resp = auth_client.get('/admin/dashboard')
    assert resp.status_code == 302
    assert '/admin/login' in resp.headers['Location']
