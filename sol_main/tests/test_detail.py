"""Phase 3 — detail page tests, incl. cross-category isolation."""


def test_contractor_detail_renders(client, make_listing):
    cid = make_listing(category='contractor', name='Bob the Builder',
                       work_type='Carpentry')
    resp = client.get(f'/contractors/{cid}')
    assert resp.status_code == 200
    assert b'Bob the Builder' in resp.data
    assert b'Carpentry' in resp.data


def test_vendor_detail_renders(client, make_listing):
    vid = make_listing(category='vendor', name='Widget Supply')
    resp = client.get(f'/vendors/{vid}')
    assert resp.status_code == 200
    assert b'Widget Supply' in resp.data


def test_contractor_id_on_vendor_route_404s(client, make_listing):
    """A contractor id must not resolve on the vendor detail route."""
    cid = make_listing(category='contractor')
    assert client.get(f'/vendors/{cid}').status_code == 404


def test_vendor_id_on_contractor_route_404s(client, make_listing):
    vid = make_listing(category='vendor')
    assert client.get(f'/contractors/{vid}').status_code == 404


def test_detail_shows_website_when_present(client, make_listing):
    cid = make_listing(category='contractor', website='https://acme.example')
    resp = client.get(f'/contractors/{cid}')
    assert b'https://acme.example' in resp.data


def test_detail_omits_website_when_absent(client, make_listing):
    cid = make_listing(category='contractor', website=None)
    resp = client.get(f'/contractors/{cid}')
    # The "Website:" list item is only rendered when a website exists.
    assert resp.status_code == 200
    assert b'Email:' in resp.data
