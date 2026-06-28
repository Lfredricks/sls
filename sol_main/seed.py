"""
Run once to seed the database with initial listings and admin user.
Usage:  python seed.py
"""
from app import create_app
from extensions import db
from models import Listing, AdminUser

CONTRACTORS = [
    {
        'name': 'ABC Contractors',
        'description': 'ABC Contractors has been serving the greater Seattle area for over 20 years. Specializing in residential and commercial builds.',
        'work_type': 'General Contractors',
        'phone': '(123) 456-7891',
        'email': 'contact@abccontractors.com',
    },
    {
        'name': 'Pacific Plumbing Co.',
        'description': 'Pacific Plumbing offers 24/7 emergency services for all your plumbing needs. Licensed and insured with over 15 years of experience.',
        'work_type': 'Plumbing',
        'phone': '(206) 555-1234',
        'email': 'info@pacificplumbing.com',
    },
    {
        'name': 'Summit Electrical',
        'description': 'Summit Electrical provides residential and commercial electrical services. From panel upgrades to full rewires, we do it all.',
        'work_type': 'Electrical',
        'phone': '(425) 555-9876',
        'email': 'service@summitelectrical.com',
    },
    {
        'name': 'Cascade Roofing',
        'description': 'Cascade Roofing specializes in roof installation, repair, and replacement. Free inspections and estimates available.',
        'work_type': 'Roofing',
        'phone': '(253) 555-4321',
        'email': 'hello@cascaderoofing.com',
    },
    {
        'name': 'Northwest Landscaping',
        'description': 'Northwest Landscaping transforms outdoor spaces with custom design, installation, and maintenance services year round.',
        'work_type': 'Landscaping',
        'phone': '(360) 555-6789',
        'email': 'info@nwlandscaping.com',
    },
]

VENDORS = [
    {
        'name': 'ABC Building Supply',
        'description': 'ABC Building Supply stocks everything from lumber to hardware for residential and commercial projects throughout the Seattle area.',
        'work_type': 'Building Materials',
        'phone': '(123) 456-7891',
        'email': 'contact@abcbuildingsupply.com',
    },
    {
        'name': 'Pacific Pipe & Fittings',
        'description': 'Pacific Pipe & Fittings supplies commercial and residential plumbing materials. Same-day availability on most standard stock.',
        'work_type': 'Plumbing Supplies',
        'phone': '(206) 555-1234',
        'email': 'info@pacificpipe.com',
    },
    {
        'name': 'Summit Electrical Supply',
        'description': 'Summit Electrical Supply carries a full line of electrical components, panels, and wiring for contractors and DIYers alike.',
        'work_type': 'Electrical Supplies',
        'phone': '(425) 555-9876',
        'email': 'service@summitelectricalsupply.com',
    },
    {
        'name': 'Cascade Roofing Materials',
        'description': 'Cascade Roofing Materials provides shingles, underlayment, flashing, and all accessory roofing products at competitive prices.',
        'work_type': 'Roofing Supplies',
        'phone': '(253) 555-4321',
        'email': 'hello@cascaderoofingmaterials.com',
    },
    {
        'name': 'Northwest Garden & Landscape',
        'description': 'Northwest Garden & Landscape supplies plants, soil, gravel, and hardscape materials for landscape contractors and homeowners.',
        'work_type': 'Landscaping Supplies',
        'phone': '(360) 555-6789',
        'email': 'info@nwgardenlandscape.com',
    },
]


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        if Listing.query.first() is None:
            for data in CONTRACTORS:
                db.session.add(Listing(category='contractor', **data))
            for data in VENDORS:
                db.session.add(Listing(category='vendor', **data))
            print("Seeded listings.")
        else:
            print("Listings already exist — skipping.")

        if AdminUser.query.first() is None:
            admin = AdminUser(username='admin')
            admin.set_password('changeme')
            db.session.add(admin)
            print("Created admin user (username: admin, password: changeme). Change the password!")
        else:
            print("Admin user already exists — skipping.")

        db.session.commit()
        print("Done.")


if __name__ == '__main__':
    seed()
