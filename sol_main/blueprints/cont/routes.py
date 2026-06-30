from flask import render_template, request, abort

import data
from blueprints.cont import bp


@bp.route('/contractors/<int:listing_id>')
def contractor_detail(listing_id):
    listing = data.get(listing_id, category='contractor')
    if listing is None:
        abort(404)
    return render_template('listing_detail.html', listing=listing, title=listing.name)


@bp.route('/contractors')
def contractors():
    q = request.args.get('q', '').strip()
    work_type = request.args.get('work_type', '').strip()

    listings = data.search('contractor', q=q, work_type=work_type)
    work_types = data.distinct_work_types('contractor')

    return render_template('cont/contractors.html',
                           listings=listings,
                           work_types=work_types,
                           q=q,
                           selected_work_type=work_type,
                           title='Contractors')
