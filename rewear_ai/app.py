import os
from flask import Flask
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate() 
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder="templates")

    # --- DATABASE LOGIC ---
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        print("DATABASE: Connecting to PostgreSQL...")
    else:
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "rewear.db")}'
        print("DATABASE: Fallback to local SQLite...")

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key_123')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_PERMANENT'] = False

    # Initialize Extensions
    db.init_app(app) 
    migrate.init_app(app, db, render_as_batch=True)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # --- THE CRITICAL FIX: IMPORT ALL MODELS FOR TABLE CREATION ---
    with app.app_context():
        # We import every model file so SQLAlchemy registers the tables
        from rewear_ai.wardrobe.models import User, Item
        from rewear_ai.outfit.models import Outfit
        from rewear_ai.donate.models import Donation
        
        # This will now create ALL tables in the Postgres DB
        db.create_all()
        print("DATABASE: All tables (Users, Items, Outfits, Donations) verified/created.")

    @login_manager.user_loader
    def load_user(user_id):
        from rewear_ai.wardrobe.models import User
        return db.session.get(User, int(user_id))

    # --- Register Blueprints ---
    from rewear_ai.wardrobe.routes import wardrobe
    from rewear_ai.outfit.routes import outfit
    from rewear_ai.donate.routes import donate
    from rewear_ai.upcycle.routes import upcycle
    from rewear_ai.auth.routes import auth
    from rewear_ai.admin.routes import admin_bp

    app.register_blueprint(wardrobe, url_prefix='/wardrobe')
    app.register_blueprint(outfit, url_prefix='/style')
    app.register_blueprint(donate, url_prefix='/donate')
    app.register_blueprint(upcycle, url_prefix='/upcycle')
    app.register_blueprint(auth)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app