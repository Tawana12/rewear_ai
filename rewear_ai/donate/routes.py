import requests
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from rewear_ai.wardrobe.models import ClothingItem, Charity, DonationRecord
from rewear_ai.app import db

donate = Blueprint('donate', __name__, template_folder='templates')

# --- GLOBAL API SEARCH (Overpass API for Nearby Charities) ---
@donate.route('/api/nearby')
@login_required
def nearby_charities():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    radius = 15000  # 15km search radius

    results = []
    try:
        # 1. Start with verified partners from our own Database
        local_db_partners = Charity.query.all()
        results = [c.to_dict() for c in local_db_partners]
    except Exception as e:
        print(f"Database Fetch Error: {e}")

    # 2. Add real-world data from OpenStreetMap (Overpass API)
    if lat and lon:
        overpass_url = "https://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["social_facility"](around:{radius},{lat},{lon});
          node["amenity"="social_centre"](around:{radius},{lat},{lon});
          node["office"="ngo"](around:{radius},{lat},{lon});
          node["charity"="yes"](around:{radius},{lat},{lon});
        );
        out center;
        """
        
        try:
            response = requests.get(overpass_url, params={'data': overpass_query}, timeout=8)
            data = response.json()
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name') or tags.get('official_name') or "Community Support Center"
                
                if any(r['name'].lower() == name.lower() for r in results):
                    continue

                results.append({
                    "name": name,
                    "lat": element.get('lat') or element.get('center', {}).get('lat'),
                    "lon": element.get('lon') or element.get('center', {}).get('lon'),
                    "type": tags.get('social_facility:for') or "Non-Profit",
                    "address": tags.get('addr:street') or tags.get('addr:city') or "Local Area"
                })
        except Exception as e:
            print(f"Global API Error: {e}")

    return jsonify(results)

# --- PAGES ---

@donate.route('/find')
@donate.route('/find/<int:item_id>') 
@login_required
def index(item_id=0): 
    """
    Main interactive page. Defaults item_id to 0 for navbar clicks 
    to prevent 'BuildError' or mandatory ID requirements.
    """
    return render_template('donate/find_home.html', item_id=item_id)

@donate.route('/log/<int:item_id>', methods=['POST'])
@login_required
def log_donation(item_id):
    """
    Processes the donation. 
    If item_id > 0, it removes the specific item from the user's wardrobe.
    If item_id is 0, it logs a general donation.
    """
    selected_home = request.form.get('charity_name', 'Local Community Center')
    
    # Check if we are donating a specific wardrobe item
    if item_id and item_id > 0:
        item = ClothingItem.query.filter_by(id=item_id, user_id=current_user.id).first()
        if not item:
            flash("Item not found in your wardrobe.", "danger")
            return redirect(url_for('wardrobe.index'))
        
        item_name = item.name
        category = item.category
    else:
        # Handles 'General Donation' from Navbar (item_id is 0)
        item_name = "General Clothing Bundle"
        category = "Mixed"
        item = None

    new_record = DonationRecord(
        item_name=item_name,
        category=category,
        charity_name=selected_home,
        user_id=current_user.id,
        impact_score=15 if item else 10 # 15 points for wardrobe items, 10 for general
    )
    
    try:
        db.session.add(new_record)
        # 🛡️ THE SUSTAINABLE ACTION: Delete from closet only if it came from the wardrobe
        if item:
            db.session.delete(item) 
        
        db.session.commit()
        
        flash(f"Amazing! You've logged your donation to {selected_home}.", "success")
        return redirect(url_for('donate.donation_success', record_id=new_record.id))
        
    except Exception as e:
        db.session.rollback()
        print(f"Donation Error: {e}")
        flash("Could not process donation. Please try again.", "danger")
        return redirect(url_for('donate.index', item_id=item_id))

@donate.route('/success/<int:record_id>')
@login_required
def donation_success(record_id):
    """Celebration page to show the impact of the donation."""
    record = DonationRecord.query.filter_by(id=record_id, user_id=current_user.id).first_or_404()
    return render_template('donate/success.html', record=record)