from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Accommodation, User, Booking, Payment, Review
from app.forms import AccommodationForm
from app.decorators import admin_required
from app.helpers import save_accommodation_images, format_amenities_list, get_dashboard_stats
import os
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__, url_prefix='/admin')

# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------
@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = get_dashboard_stats()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    accommodations = Accommodation.query.all()
    occupancy_data = []
    for acc in accommodations:
        occupancy_rate = (acc.current_occupancy / acc.capacity * 100) if acc.capacity > 0 else 0
        occupancy_data.append({
            'title': acc.title,
            'occupancy_rate': occupancy_rate,
            'current': acc.current_occupancy,
            'capacity': acc.capacity
        })
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_bookings=recent_bookings,
                         occupancy_data=occupancy_data)

# ------------------------------------------------------------------
# List accommodations
# ------------------------------------------------------------------
@bp.route('/accommodations')
@login_required
@admin_required
def manage_accommodations():
    accommodations = Accommodation.query.order_by(Accommodation.created_at.desc()).all()
    return render_template('admin/manage_accommodations.html', accommodations=accommodations)

# ------------------------------------------------------------------
# ADD accommodation
# ------------------------------------------------------------------
@bp.route('/accommodations/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_accommodation():
    form = AccommodationForm()
    if form.validate_on_submit():
        acc = Accommodation(
            title=form.title.data,
            description=form.description.data,
            room_type=form.room_type.data,
            price_per_month=form.price_per_month.data,
            location=form.location.data,
            capacity=form.capacity.data,
            current_occupancy=form.current_occupancy.data or 0,
            amenities=format_amenities_list(form.amenities.data),
            admin_id=current_user.id
        )
        db.session.add(acc)
        db.session.commit()

        files = request.files.getlist('images')
        if files and files[0].filename:
            saved_paths = save_accommodation_images(files, acc.id)
            if saved_paths:
                acc.images = saved_paths
                db.session.commit()

        flash('Accommodation added successfully!', 'success')
        return redirect(url_for('admin.manage_accommodations'))
    
    # Show form errors if validation failed
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return render_template('admin/add_accommodation.html', form=form)

# ------------------------------------------------------------------
# EDIT accommodation
# ------------------------------------------------------------------
@bp.route('/accommodations/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_accommodation(id):
    acc = Accommodation.query.get_or_404(id)
    form = AccommodationForm(obj=acc)
    
    # Pre-populate amenities field for GET request
    if request.method == 'GET' and acc.amenities:
        form.amenities.data = ', '.join(acc.amenities)

    if form.validate_on_submit():
        try:
            # Update basic fields explicitly
            acc.title = form.title.data
            acc.description = form.description.data
            acc.room_type = form.room_type.data
            acc.price_per_month = form.price_per_month.data
            acc.location = form.location.data
            acc.capacity = form.capacity.data
            acc.current_occupancy = form.current_occupancy.data or 0
            acc.amenities = format_amenities_list(form.amenities.data)
            acc.status = 'available' if acc.current_occupancy < acc.capacity else 'fully_occupied'

            # Handle images - only process if new files are uploaded
            files = request.files.getlist('images')
            has_new_files = any(f and f.filename for f in files)
            
            if has_new_files:
                new_paths = save_accommodation_images(files, acc.id)
                if new_paths:
                    # Ensure existing images is a clean list of strings
                    existing_images = []
                    if acc.images and isinstance(acc.images, list):
                        existing_images = [img for img in acc.images if isinstance(img, str)]
                    
                    # Combine existing with new paths
                    acc.images = existing_images + new_paths

            db.session.commit()
            flash('Accommodation updated successfully!', 'success')
            return redirect(url_for('admin.manage_accommodations'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating accommodation: {str(e)}')
            flash(f'Error updating accommodation: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_accommodation', id=id))
    
    # Debug: Show form errors if validation failed
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
                current_app.logger.error(f'Form validation error - {field}: {error}')
    
    return render_template('admin/edit_accommodation.html', form=form, accommodation=acc)

# ------------------------------------------------------------------
# DELETE accommodation
# ------------------------------------------------------------------
@bp.route('/accommodations/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_accommodation(id):
    acc = Accommodation.query.get_or_404(id)
    if acc.bookings:
        flash('Cannot delete accommodation with existing bookings', 'danger')
        return redirect(url_for('admin.manage_accommodations'))

    db.session.delete(acc)
    db.session.commit()
    flash('Accommodation deleted successfully!', 'success')
    return redirect(url_for('admin.manage_accommodations'))

# ------------------------------------------------------------------
# Bookings
# ------------------------------------------------------------------
@bp.route('/bookings')
@login_required
@admin_required
def view_all_bookings():
    status_filter = request.args.get('status', 'all')
    query = Booking.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    bookings = query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/all_bookings.html', bookings=bookings)

@bp.route('/bookings/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_booking_status(id):
    booking = Booking.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'approved', 'paid', 'cancelled']:
        booking.status = new_status
        db.session.commit()
        flash(f'Booking status updated to {new_status}', 'success')
    return redirect(url_for('admin.view_all_bookings'))

# ------------------------------------------------------------------
# Users Management
# ------------------------------------------------------------------
@bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    # Calculate 30 days ago for statistics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    return render_template('admin/manage_users.html', 
                         users=users, 
                         today_minus_30=thirty_days_ago)

@bp.route('/users/promote/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role', 'warning')
        return redirect(url_for('admin.manage_users'))
    
    user.role = 'admin'
    db.session.commit()
    flash(f'{user.full_name} has been promoted to admin', 'success')
    return redirect(url_for('admin.manage_users'))

@bp.route('/users/demote/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role', 'warning')
        return redirect(url_for('admin.manage_users'))
    
    user.role = 'user'
    db.session.commit()
    flash(f'{user.full_name} has been demoted to regular user', 'success')
    return redirect(url_for('admin.manage_users'))

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Check if user has bookings
    if user.bookings:
        flash('Cannot delete user with existing bookings', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.full_name} has been deleted', 'success')
    return redirect(url_for('admin.manage_users'))

# ------------------------------------------------------------------
# Revenue
# ------------------------------------------------------------------
@bp.route('/revenue')
@login_required
@admin_required
def revenue_report():
    payments = Payment.query.filter_by(status='succeeded').order_by(Payment.created_at.desc()).all()
    total_revenue = sum(payment.amount for payment in payments)
    return render_template('admin/revenue_report.html', payments=payments, total_revenue=total_revenue)