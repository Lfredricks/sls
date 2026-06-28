from flask import render_template, request
from sqlalchemy import or_

from blueprints.cont import bp
from extensions import db
from models import Listing


@bp.route('/contractors/<int:listing_id>')
def contractor_detail(listing_id):
    listing = Listing.query.filter_by(id=listing_id, category='contractor').first_or_404()
    return render_template('listing_detail.html', listing=listing, title=listing.name)


@bp.route('/contractors')
def contractors():
    q = request.args.get('q', '').strip()
    work_type = request.args.get('work_type', '').strip()

    query = Listing.query.filter_by(category='contractor')

    if q:
        query = query.filter(
            or_(
                Listing.name.ilike(f'%{q}%'),
                Listing.work_type.ilike(f'%{q}%'),
                Listing.description.ilike(f'%{q}%'),
            )
        )

    if work_type:
        query = query.filter_by(work_type=work_type)

    listings = query.order_by(Listing.date_added.desc()).all()

    work_types = [row[0] for row in
                  db.session.query(Listing.work_type)
                  .filter_by(category='contractor')
                  .distinct()
                  .order_by(Listing.work_type)
                  .all()]

    return render_template('cont/contractors.html',
                           listings=listings,
                           work_types=work_types,
                           q=q,
                           selected_work_type=work_type,
                           title='Contractors')
