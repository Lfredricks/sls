"""Phase 6 — security cross-cutting concerns."""
from conftest import ADMIN_USERNAME, ADMIN_PASSWORD


# ── CSRF enforcement (csrf_client has WTF_CSRF_ENABLED=True) ─────────────────

def test_login_post_without_csrf_token_rejected(csrf_client):
    resp = csrf_client.post('/admin/login',
                            data={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD})
    assert resp.status_code == 400


def test_csrf_token_present_in_login_form(csrf_client):
    resp = csrf_client.get('/admin/login')
    assert b'csrf_token' in resp.data


# ── Session cookie hardening ────────────────────────────────────────────────

def test_session_cookie_is_httponly_and_samesite(client):
    resp = client.post('/admin/login',
                       data={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD})
    cookies = resp.headers.getlist('Set-Cookie')
    session_cookie = next((c for c in cookies if c.startswith('session=')), '')
    assert 'HttpOnly' in session_cookie
    assert 'SameSite=Lax' in session_cookie


# ── No public exposure of the admin entrypoint ──────────────────────────────

def test_admin_login_not_linked_from_public_pages(client):
    for path in ('/', '/contractors', '/vendors'):
        assert b'/admin/login' not in client.get(path).data
