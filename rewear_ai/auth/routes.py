from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from rewear_ai.wardrobe.models import User
from rewear_ai.app import db

auth = Blueprint('auth', __name__, template_folder='templates')

# 📌 THE LANDING PAGE (Mission & Goals)
@auth.route('/')
def landing():
    # If already logged in, skip the landing page
    if current_user.is_authenticated:
        return redirect(url_for('wardrobe.index'))
    # Otherwise, show the mission, challenges, and goals
    return render_template('home.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('wardrobe.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        # Create the user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        # LOGIC: First user is Admin, others are standard users
        if User.query.count() == 0:
            new_user.role = 'admin'
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('wardrobe.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            # Redirect to Admin Dashboard if Admin, else Wardrobe
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('wardrobe.index'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
            
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))