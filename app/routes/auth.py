from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Booking
from app.forms import RegistrationForm, LoginForm
from app.helpers import save_profile_picture

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == form.email.data) |
            (User.student_number == form.student_number.data) |
            (User.id_number == form.id_number.data)
        ).first()
        
        if existing_user:
            if existing_user.email == form.email.data:
                flash('Email already registered', 'danger')
            elif existing_user.student_number == form.student_number.data:
                flash('Student number already registered', 'danger')
            else:
                flash('ID number already registered', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(
            student_number=form.student_number.data,
            full_name=form.full_name.data,
            email=form.email.data,
            id_number=form.id_number.data,
            phone_number=form.phone_number.data
        )
        user.set_password(form.password.data)
        
        # Handle profile picture upload
        if form.profile_picture.data:
            profile_pic = save_profile_picture(form.profile_picture.data, user.id)
            user.profile_picture = profile_pic
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            if user.is_admin():
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_bookings = Booking.query.filter_by(user_id=current_user.id)\
        .order_by(Booking.created_at.desc()).limit(5).all()
    
    return render_template('auth/profile.html', bookings=user_bookings)