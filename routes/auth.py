from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user, error = AuthService.authenticate_user(username, password)
        if error:
            flash(error, 'danger')
        else:
            login_user(user)
            flash(f"Welcome back, {user.username}!", 'success')
            return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        country_code = request.form.get('country_code', '+91')
        full_phone = f"{country_code}{phone}"
        resident_type = request.form.get('resident_type')  # Owner or Tenant
        emergency_contact = request.form.get('emergency_contact')

        user, error = AuthService.register_resident(
            username=username,
            email=email,
            password=password,
            phone=full_phone,
            flat_id=None,
            resident_type=resident_type,
            emergency_contact=emergency_contact
        )

        if error:
            flash(error, 'danger')
        else:
            flash("Registration successful! Your account is pending admin approval.", 'info')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have logged out successfully.", 'info')
    return redirect(url_for('home.index'))
