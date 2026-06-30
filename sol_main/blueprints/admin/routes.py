from urllib.parse import urljoin, urlparse

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required

import data
from blueprints.admin import bp
from blueprints.admin.forms import LoginForm, ListingForm


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
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = data.get_user_by_username(form.username.data)
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
    contractor_count, vendor_count = data.counts()
    return render_template('admin/dashboard.html',
                           title='Dashboard',
                           contractor_count=contractor_count,
                           vendor_count=vendor_count,
                           recent=data.recent(5))


# ── Listing list ──────────────────────────────────────────────────────────────

@bp.route('/listings')
@login_required
def listings():
    category = request.args.get('category', '')
    cat = category if category in ('contractor', 'vendor') else None
    return render_template('admin/listings.html',
                           title='Manage Listings',
                           listings=data.all_listings(cat),
                           category=category)


# ── Add listing ───────────────────────────────────────────────────────────────

@bp.route('/listings/new', methods=['GET', 'POST'])
@login_required
def new_listing():
    form = ListingForm()
    if form.validate_on_submit():
        listing = data.add(
            name=form.name.data,
            category=form.category.data,
            work_type=form.work_type.data,
            description=form.description.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data or None,
        )
        flash(f'"{listing.name}" added successfully.', 'success')
        return redirect(url_for('admin.listings'))
    return render_template('admin/listing_form.html', form=form, title='Add Listing', legend='Add Listing')


# ── Edit listing ──────────────────────────────────────────────────────────────

@bp.route('/listings/<int:listing_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    listing = data.get(listing_id)
    if listing is None:
        abort(404)
    form = ListingForm(obj=listing)
    if form.validate_on_submit():
        data.update(
            listing_id,
            name=form.name.data,
            category=form.category.data,
            work_type=form.work_type.data,
            description=form.description.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data or None,
        )
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
    listing = data.delete(listing_id)
    if listing is None:
        abort(404)
    flash(f'"{listing.name}" deleted.', 'success')
    return redirect(url_for('admin.listings'))
