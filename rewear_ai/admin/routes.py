from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from rewear_ai.wardrobe.models import Charity, DonationRecord, User, ClothingItem
from rewear_ai.app import db

admin_bp = Blueprint('admin', __name__, template_folder='templates')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Only allow David (the admin) to see this
    if not current_user.is_admin:
        flash("Unauthorized access. Admin only.", "danger")
        return redirect(url_for('wardrobe.index'))

    # Stats for the dashboard
    total_users = User.query.count()
    total_donations = DonationRecord.query.count()
    total_clothes = ClothingItem.query.count()
    verified_charities = Charity.query.all()
    
    return render_template('admin/dashboard.html', 
                           users=total_users, 
                           donations=total_donations,
                           clothes=total_clothes,
                           charities=verified_charities)

@admin_bp.route('/add-charity', methods=['POST'])
@login_required
def add_charity():
    if not current_user.is_admin:
        return redirect(url_for('wardrobe.index'))

    name = request.form.get('name')
    address = request.form.get('address')
    lat = request.form.get('lat')
    lon = request.form.get('lon')

    new_charity = Charity(name=name, address=address, lat=lat, lon=lon)
    db.session.add(new_charity)
    db.session.commit()
    
    flash(f"Successfully added {name} to the verified list!", "success")
    return redirect(url_for('admin.dashboard'))