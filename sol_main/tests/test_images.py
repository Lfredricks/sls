"""Phase 5 — image upload pipeline (_save_image / _delete_image)."""
import io
import os

from PIL import Image

from extensions import db
from models import Listing
from test_admin_crud import form_data


def make_image_bytes(size=(1000, 1000), fmt='PNG', color=(120, 80, 40)):
    """An in-memory image file suitable for a multipart upload."""
    buf = io.BytesIO()
    Image.new('RGB', size, color).save(buf, fmt)
    buf.seek(0)
    return buf


def upload_folder(app):
    return app.config['UPLOAD_FOLDER']


def saved_filename(app, name):
    with app.app_context():
        return Listing.query.filter_by(name=name).first().image_filename


# ── Save ────────────────────────────────────────────────────────────────────

def test_upload_saves_jpeg_with_uuid_name(auth_client, app):
    data = form_data(name='WithPic')
    data['image'] = (make_image_bytes(), 'photo.png')
    auth_client.post('/admin/listings/new', data=data,
                     content_type='multipart/form-data')

    fname = saved_filename(app, 'WithPic')
    assert fname is not None
    assert fname.endswith('.jpg')          # always normalized to .jpg
    assert 'photo' not in fname            # name is a uuid, never user-supplied
    assert os.path.exists(os.path.join(upload_folder(app), fname))


def test_upload_is_resized_within_800(auth_client, app):
    data = form_data(name='BigPic')
    data['image'] = (make_image_bytes(size=(1600, 1200)), 'big.png')
    auth_client.post('/admin/listings/new', data=data,
                     content_type='multipart/form-data')

    fname = saved_filename(app, 'BigPic')
    with Image.open(os.path.join(upload_folder(app), fname)) as img:
        assert img.format == 'JPEG'
        assert max(img.size) <= 800


def test_small_image_not_upscaled(auth_client, app):
    data = form_data(name='SmallPic')
    data['image'] = (make_image_bytes(size=(100, 100)), 'small.png')
    auth_client.post('/admin/listings/new', data=data,
                     content_type='multipart/form-data')

    fname = saved_filename(app, 'SmallPic')
    with Image.open(os.path.join(upload_folder(app), fname)) as img:
        assert img.size == (100, 100)


def test_non_image_extension_rejected(auth_client, app):
    data = form_data(name='NotAnImage')
    data['image'] = (io.BytesIO(b'just some text'), 'notes.txt')
    resp = auth_client.post('/admin/listings/new', data=data,
                            content_type='multipart/form-data')
    assert resp.status_code == 200          # form re-rendered with error
    with app.app_context():
        assert Listing.query.filter_by(name='NotAnImage').count() == 0


# ── Replace on edit ─────────────────────────────────────────────────────────

def test_edit_replaces_and_deletes_old_image(auth_client, app):
    # Create with an initial image.
    data = form_data(name='Swapper')
    data['image'] = (make_image_bytes(), 'first.png')
    auth_client.post('/admin/listings/new', data=data,
                     content_type='multipart/form-data')

    old_name = saved_filename(app, 'Swapper')
    old_path = os.path.join(upload_folder(app), old_name)
    assert os.path.exists(old_path)

    with app.app_context():
        listing_id = Listing.query.filter_by(name='Swapper').first().id

    # Edit with a new image.
    data2 = form_data(name='Swapper')
    data2['image'] = (make_image_bytes(color=(10, 200, 10)), 'second.png')
    auth_client.post(f'/admin/listings/{listing_id}/edit', data=data2,
                     content_type='multipart/form-data')

    new_name = saved_filename(app, 'Swapper')
    assert new_name != old_name
    assert os.path.exists(os.path.join(upload_folder(app), new_name))
    assert not os.path.exists(old_path)     # old file cleaned up


def test_edit_without_new_image_keeps_existing(auth_client, app):
    data = form_data(name='Keeper')
    data['image'] = (make_image_bytes(), 'keep.png')
    auth_client.post('/admin/listings/new', data=data,
                     content_type='multipart/form-data')
    fname = saved_filename(app, 'Keeper')

    with app.app_context():
        listing_id = Listing.query.filter_by(name='Keeper').first().id

    # Edit with no image field -> image_filename unchanged.
    auth_client.post(f'/admin/listings/{listing_id}/edit',
                     data=form_data(name='Keeper Renamed'))
    with app.app_context():
        assert db.session.get(Listing, listing_id).image_filename == fname
    assert os.path.exists(os.path.join(upload_folder(app), fname))


# ── Delete removes file ─────────────────────────────────────────────────────

def test_delete_listing_removes_image_file(auth_client, app):
    data = form_data(name='ToRemove')
    data['image'] = (make_image_bytes(), 'gone.png')
    auth_client.post('/admin/listings/new', data=data,
                     content_type='multipart/form-data')
    fname = saved_filename(app, 'ToRemove')
    path = os.path.join(upload_folder(app), fname)
    assert os.path.exists(path)

    with app.app_context():
        listing_id = Listing.query.filter_by(name='ToRemove').first().id
    auth_client.post(f'/admin/listings/{listing_id}/delete')
    assert not os.path.exists(path)


# ── Upload size cap ─────────────────────────────────────────────────────────

def test_oversized_upload_rejected_413(auth_client):
    """MAX_CONTENT_LENGTH is 8 MB; a larger request body is refused."""
    big = io.BytesIO(b'x' * (8 * 1024 * 1024 + 1024))
    data = form_data(name='TooBig')
    data['image'] = (big, 'huge.png')
    resp = auth_client.post('/admin/listings/new', data=data,
                            content_type='multipart/form-data')
    assert resp.status_code == 413
