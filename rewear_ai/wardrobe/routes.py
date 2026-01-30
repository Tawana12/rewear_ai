import os
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, current_app
)
from flask_login import login_required, current_user # Added for Auth
from werkzeug.utils import secure_filename
from rewear_ai.wardrobe.models import ClothingItem
from rewear_ai.app import db
from rewear_ai.services.vision import analyze_clothing_image 

wardrobe = Blueprint(
    'wardrobe',
    __name__,
    template_folder='templates'
)

# 📌 VIEW ALL & SEARCH (Filtered by User)
@wardrobe.route('/')
@login_required # Must be logged in
def index():
    search_query = request.args.get('q', '')
    category_filter = request.args.get('cat', '')
    
    # 🛡️ ONLY get items belonging to the current user
    query = ClothingItem.query.filter_by(user_id=current_user.id)

    if search_query:
        query = query.filter(ClothingItem.name.contains(search_query))
    if category_filter:
        query = query.filter_by(category=category_filter)

    items = query.all()
    
    # --- SUSTAINABILITY LOGIC ---
    total_wears = sum(item.times_worn for item in items)
    co2_saved = round(total_wears * 0.5, 1)
    
    return render_template('wardrobe/index.html', 
                            items=items, 
                            co2_saved=co2_saved, 
                            total_wears=total_wears)

# 📌 VIEW SINGLE ITEM
@wardrobe.route('/item/<int:id>')
@login_required
def detail(id):
    # Ensure a user can't peek at someone else's item via ID
    item = ClothingItem.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('wardrobe/detail.html', item=item)

# 📌 ADD ITEM (Linked to User)
@wardrobe.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'GET':
        return render_template('wardrobe/add.html')

    name = request.form.get('name')
    category = request.form.get('category')
    color = request.form.get('color')
    season = request.form.get('season')
    occasion = request.form.get('occasion')
    
    file = request.files.get('image')
    filename = 'default.jpg' 
    
    celeb_twin = "Style Icon"
    styling_tip = "Pair with neutral tones for a balanced look."
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.static_folder, 'uploads')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        saved_path = os.path.join(upload_path, filename)
        file.save(saved_path)

        ai_results = analyze_clothing_image(saved_path)
        if ai_results:
            if not category or category == "Other": 
                category = ai_results.get('category', category)
            if not color:
                color = ai_results.get('color', color)
            
            celeb_twin = ai_results.get('celeb_twin', celeb_twin)
            styling_tip = ai_results.get('styling_tip', styling_tip)

    if not name or not category:
        flash('Name and Category are required', 'danger')
        return redirect(url_for('wardrobe.add'))

    # 🛡️ ASSIGN user_id to the new item
    item = ClothingItem(
        name=name, 
        category=category, 
        color=color,
        season=season, 
        occasion=occasion, 
        image_file=filename,
        celeb_twin=celeb_twin,
        styling_tip=styling_tip,
        user_id=current_user.id # Linking to the logged-in user
    )

    db.session.add(item)
    db.session.commit()
    flash(f"Success! Gemini matched this to {celeb_twin}'s style and added it to your wardrobe.")
    return redirect(url_for('wardrobe.index'))

# 📌 EDIT ITEM
@wardrobe.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    item = ClothingItem.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.category = request.form.get('category')
        item.color = request.form.get('color')
        item.season = request.form.get('season')
        item.occasion = request.form.get('occasion')
        
        file = request.files.get('image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.static_folder, 'uploads', filename))
            item.image_file = filename
            
        db.session.commit()
        flash('Item updated!', 'success')
        return redirect(url_for('wardrobe.detail', id=item.id))
    return render_template('wardrobe/edit.html', item=item)

# 📌 DELETE ITEM
@wardrobe.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    item = ClothingItem.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if item.image_file and item.image_file != 'default.jpg':
        file_path = os.path.join(current_app.static_folder, 'uploads', item.image_file)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(item)
    db.session.commit()
    flash('Item removed from wardrobe', 'success')
    return redirect(url_for('wardrobe.index'))