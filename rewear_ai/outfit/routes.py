import random
import requests
from flask import Blueprint, render_template, request, jsonify
from rewear_ai.wardrobe.models import ClothingItem
from rewear_ai.app import db # Added db import for saving 'worn' stats

outfit = Blueprint('outfit', __name__, template_folder='templates')

@outfit.route('/api/weather')
def weather_api():
    """Fetches real-time weather from Open-Meteo based on browser coordinates."""
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return jsonify({"error": "Location missing"}), 400

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
    
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        temp = round(data['current']['temperature_2m'])
        code = data['current']['weather_code']
        
        # WMO Weather interpretation codes
        mapping = {0: "Sunny", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast", 61: "Rainy", 80: "Showers"}
        condition = mapping.get(code, "Clear")
        
        return jsonify({"temp": temp, "condition": condition})
    except Exception as e:
        return jsonify({"temp": "--", "condition": "Unavailable"}), 500

@outfit.route('/dashboard')
def dashboard():
    occasion = request.args.get('occasion', 'Casual')
    temp = request.args.get('temp', type=int)

    # 🧠 AI Selection Logic
    query = ClothingItem.query.filter_by(occasion=occasion)
    
    tops = query.filter_by(category='Top').all()
    bottoms = query.filter_by(category='Bottom').all()
    shoes = query.filter_by(category='Shoes').all()
    
    # Weather-Aware Layering
    outerwear = None
    if temp and temp < 18:
        # Tries to find outerwear for the occasion, or just any outerwear as a fallback
        outerwear = ClothingItem.query.filter_by(category='Outerwear', occasion=occasion).first() or \
                    ClothingItem.query.filter_by(category='Outerwear').first()

    suggested_outfit = None
    if tops and bottoms and shoes:
        suggested_outfit = {
            "top": random.choice(tops),
            "bottom": random.choice(bottoms),
            "shoes": random.choice(shoes),
            "outerwear": outerwear
        }
        
        # ✅ SUSTAINABILITY LOGIC: Update wear count
        # This tracks "Wardrobe Intelligence" by rewarding reuse
        for item in suggested_outfit.values():
            if item: # Check if item exists (like optional outerwear)
                item.times_worn += 1
        
        db.session.commit()

    return render_template('outfit/dashboard.html', 
                           outfit=suggested_outfit, 
                           occasion=occasion)