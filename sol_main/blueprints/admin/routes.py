import os
import uuid
from urllib.parse import urljoin, urlparse

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from PIL import Image

from blueprints.admin import bp
from blueprints.admin.forms import LoginForm, ListingForm
from extensions import db
from models import AdminUser, Listing


# ── Auth ──────────────────────────────────────────────────────────────────────

def _is_safe_redirect_url(target):
    """True only if `target` stays on this host (prevents open redirects)."""
    if not target:
        return False
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ('http', 'https') and ref.netloc == test.netloc


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not _is_safe_redirect_url(next_page):
                next_page = None
            return redirect(next_page or url_for('admin.dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('admin/login.html', form=form, title='Admin Login')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@bp.route('/dashboard')
@login_required
def dashboard():
    contractor_count = Listing.query.filter_by(category='contractor').count()
    vendor_count = Listing.query.filter_by(category='vendor').count()
    recent = Listing.query.order_by(Listing.date_added.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           title='Dashboard',
                           contractor_count=contractor_count,
                           vendor_count=vendor_count,
                           recent=recent)


# ── Listing list ──────────────────────────────────────────────────────────────

@bp.route('/listings')
@login_required
def listings():
    category = request.args.get('category', '')
    query = Listing.query
    if category in ('contractor', 'vendor'):
        query = query.filter_by(category=category)
    all_listings = query.order_by(Listing.date_added.desc()).all()
    return render_template('admin/listings.html',
                           title='Manage Listings',
                           listings=all_listings,
                           category=category)


# ── Add listing ───────────────────────────────────────────────────────────────

@bp.route('/listings/new', methods=['GET', 'POST'])
@login_required
def new_listing():
    form = ListingForm()
    if form.validate_on_submit():
        listing = Listing(
            name=form.name.data,
            category=form.category.data,
            work_type=form.work_type.data,
            description=form.description.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data or None,
        )
        if form.image.data:
            listing.image_filename = _save_image(form.image.data)
        db.session.add(listing)
        db.session.commit()
        flash(f'"{listing.name}" added successfully.', 'success')
        return redirect(url_for('admin.listings'))
    return render_template('admin/listing_form.html', form=form, title='Add Listing', legend='Add Listing')


# ── Edit listing ──────────────────────────────────────────────────────────────

@bp.route('/listings/<int:listing_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    form = ListingForm(obj=listing)
    if form.validate_on_submit():
        listing.name = form.name.data
        listing.category = form.category.data
        listing.work_type = form.work_type.data
        listing.description = form.description.data
        listing.phone = form.phone.data
        listing.email = form.email.data
        listing.website = form.website.data or None
        if form.image.data:
            if listing.image_filename:
                _delete_image(listing.image_filename)
            listing.image_filename = _save_image(form.image.data)
        db.session.commit()
        flash(f'"{listing.name}" updated successfully.', 'success')
        return redirect(url_for('admin.listings'))
    return render_template('admin/listing_form.html',
                           form=form,
                           title='Edit Listing',
                           legend=f'Edit — {listing.name}',
                           listing=listing)


# ── Delete listing ────────────────────────────────────────────────────────────

@bp.route('/listings/<int:listing_id>/delete', methods=['POST'])
@login_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.image_filename:
        _delete_image(listing.image_filename)
    db.session.delete(listing)
    db.session.commit()
    flash(f'"{listing.name}" deleted.', 'success')
    return redirect(url_for('admin.listings'))


# ── Image helpers ─────────────────────────────────────────────────────────────

def _save_image(file_storage):
    """Validate, resize, and save an uploaded image. Returns the saved filename."""
    img = Image.open(file_storage)
    img = img.convert('RGB')
    img.thumbnail((800, 800))

    filename = uuid.uuid4().hex + '.jpg'
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    img.save(os.path.join(upload_folder, filename), 'JPEG', quality=85)
    return filename


def _delete_image(filename):
    """Remove an uploaded image from disk if it exists."""
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)
