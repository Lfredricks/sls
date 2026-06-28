"""Phase 3 — search, filter, category isolation, and work_type dropdown.

These tests target the contractor blueprint; the vendor blueprint shares the
identical query logic, with a couple of vendor-side checks to guard against
copy-paste drift between the two.
"""
from datetime import datetime


# ── Category isolation ──────────────────────────────────────────────────────

def test_contractors_list_excludes_vendors(client, make_listing):
    make_listing(category='contractor', name='ConPro')
    make_listing(category='vendor', name='VendCorp')
    resp = client.get('/contractors')
    assert b'ConPro' in resp.data
    assert b'VendCorp' not in resp.data


def test_vendors_list_excludes_contractors(client, make_listing):
    make_listing(category='contractor', name='ConPro')
    make_listing(category='vendor', name='VendCorp')
    resp = client.get('/vendors')
    assert b'VendCorp' in resp.data
    assert b'ConPro' not in resp.data


# ── Search across name / work_type / description ────────────────────────────

def test_search_matches_name(client, make_listing):
    make_listing(category='contractor', name='Aardvark Plumbing')
    make_listing(category='contractor', name='Zebra Electric')
    resp = client.get('/contractors?q=aardvark')
    assert b'Aardvark Plumbing' in resp.data
    assert b'Zebra Electric' not in resp.data


def test_search_matches_work_type(client, make_listing):
    make_listing(category='contractor', name='Generic One', work_type='Roofing')
    make_listing(category='contractor', name='Generic Two', work_type='Painting')
    resp = client.get('/contractors?q=roof')
    assert b'Generic One' in resp.data
    assert b'Generic Two' not in resp.data


def test_search_matches_description(client, make_listing):
    make_listing(category='contractor', name='Hidden Gem',
                 description='We specialize in skylight installation.')
    make_listing(category='contractor', name='Other Co',
                 description='General handiwork.')
    resp = client.get('/contractors?q=skylight')
    assert b'Hidden Gem' in resp.data
    assert b'Other Co' not in resp.data


def test_search_is_case_insensitive(client, make_listing):
    make_listing(category='contractor', name='CamelCase Co')
    resp = client.get('/contractors?q=camelcase')
    assert b'CamelCase Co' in resp.data


def test_search_is_partial(client, make_listing):
    make_listing(category='contractor', name='Internationalize Inc')
    resp = client.get('/contractors?q=national')
    assert b'Internationalize Inc' in resp.data


def test_whitespace_query_returns_all(client, make_listing):
    make_listing(category='contractor', name='Alpha')
    make_listing(category='contractor', name='Beta')
    resp = client.get('/contractors?q=%20%20')  # "  " -> stripped to empty
    assert b'Alpha' in resp.data
    assert b'Beta' in resp.data


def test_no_match_shows_empty_state(client, make_listing):
    make_listing(category='contractor', name='Alpha')
    resp = client.get('/contractors?q=zzzznotfound')
    assert b'Alpha' not in resp.data
    assert b'No contractors found' in resp.data


# ── work_type filter (exact match) ──────────────────────────────────────────

def test_work_type_filter_exact(client, make_listing):
    make_listing(category='contractor', name='Roofer One', work_type='Roofing')
    make_listing(category='contractor', name='Painter One', work_type='Painting')
    resp = client.get('/contractors?work_type=Roofing')
    assert b'Roofer One' in resp.data
    assert b'Painter One' not in resp.data


def test_work_type_filter_is_not_partial(client, make_listing):
    """work_type uses filter_by (exact), not ilike — a substring must not match."""
    make_listing(category='contractor', name='Roofer One', work_type='Roofing')
    resp = client.get('/contractors?work_type=Roof')
    assert b'Roofer One' not in resp.data
    assert b'No contractors found' in resp.data


def test_combined_query_and_work_type(client, make_listing):
    make_listing(category='contractor', name='Acme Roofing', work_type='Roofing')
    make_listing(category='contractor', name='Beta Roofing', work_type='Roofing')
    make_listing(category='contractor', name='Acme Painting', work_type='Painting')
    resp = client.get('/contractors?q=acme&work_type=Roofing')
    assert b'Acme Roofing' in resp.data
    assert b'Beta Roofing' not in resp.data   # excluded by q
    assert b'Acme Painting' not in resp.data  # excluded by work_type


# ── work_type dropdown options ──────────────────────────────────────────────

def test_work_types_dropdown_is_distinct_and_category_scoped(client, make_listing):
    make_listing(category='contractor', work_type='Roofing')
    make_listing(category='contractor', work_type='Roofing')   # duplicate
    make_listing(category='contractor', work_type='Plumbing')
    make_listing(category='vendor', work_type='Lumber')        # other category
    resp = client.get('/contractors')
    body = resp.data
    # Each contractor work_type appears exactly once as an <option>.
    assert body.count(b'<option value="Roofing"') == 1
    assert body.count(b'<option value="Plumbing"') == 1
    # Vendor-only work types must not appear in the contractor dropdown.
    assert b'<option value="Lumber"' not in body


# ── Ordering: newest first ──────────────────────────────────────────────────

def test_listings_ordered_newest_first(client, make_listing):
    make_listing(category='contractor', name='Older',
                 date_added=datetime(2020, 1, 1))
    make_listing(category='contractor', name='Newer',
                 date_added=datetime(2025, 1, 1))
    body = client.get('/contractors').data
    assert body.index(b'Newer') < body.index(b'Older')
