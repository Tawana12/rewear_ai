from datetime import datetime
from rewear_ai.app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    # ROLE SYSTEM: 'user' for members, 'admin' for you
    role = db.Column(db.String(20), default='user') 

    # Relationships: Links clothes and donations to specific users
    items = db.relationship('ClothingItem', backref='owner', lazy=True)
    donations = db.relationship('DonationRecord', backref='donator', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

class ClothingItem(db.Model):
    __tablename__ = 'clothing_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    season = db.Column(db.String(20), nullable=False)
    occasion = db.Column(db.String(50), nullable=True)
    image_file = db.Column(db.String(100), nullable=True, default='default.jpg') 
    times_worn = db.Column(db.Integer, default=0)

    # --- AI VISION FIELDS ---
    celeb_twin = db.Column(db.String(100), nullable=True)
    styling_tip = db.Column(db.Text, nullable=True)

    # --- USER RELATIONSHIP ---
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<ClothingItem {self.name}>"

class Charity(db.Model):
    __tablename__ = 'charities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

    def to_dict(self):
        return {
            "name": self.name,
            "address": self.address,
            "lat": self.lat,
            "lon": self.lon,
            "type": "Verified Partner"
        }

class DonationRecord(db.Model):
    __tablename__ = 'donation_records'
    
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    charity_name = db.Column(db.String(100))
    date_donated = db.Column(db.DateTime, default=datetime.utcnow)
    impact_score = db.Column(db.Integer, default=10)
    
    # Track who donated it for the leaderboard
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)