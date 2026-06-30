from flask import render_template, request, abort

import data
from blueprints.vend import bp


@bp.route('/vendors/<int:listing_id>')
def vendor_detail(listing_id):
    listing = data.get(listing_id, category='vendor')
    if listing is None:
        abort(404)
    return render_template('listing_detail.html', listing=listing, title=listing.name)


@bp.route('/vendors')
def vendors():
    q = request.args.get('q', '').strip()
    work_type = request.args.get('work_type', '').strip()

    listings = data.search('vendor', q=q, work_type=work_type)
    work_types = data.distinct_work_types('vendor')

    return render_template('vend/vendors.html',
                           listings=listings,
                           work_types=work_types,
                           q=q,
                           selected_work_type=work_type,
                           title='Vendors')
