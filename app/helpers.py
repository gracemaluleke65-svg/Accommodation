import os
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
from datetime import datetime

# ------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------
def allowed_file(filename):
    """Check if file extension is allowed (case-insensitive)"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# ------------------------------------------------------------------
# PROFILE picture
# ------------------------------------------------------------------
def save_profile_picture(file, user_id):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"user_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"

        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, new_filename)
        
        try:
            img = Image.open(file)
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            img.save(filepath, 'JPEG', quality=85)
            return f'uploads/profiles/{new_filename}'
        except Exception as e:
            current_app.logger.error(f'Error saving profile picture: {str(e)}')
            return 'images/default_profile.png'
    return 'images/default_profile.png'

# ------------------------------------------------------------------
# ACCOMMODATION images
# ------------------------------------------------------------------
def save_accommodation_images(files, accommodation_id):
    saved = []
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'accommodations')
    os.makedirs(upload_dir, exist_ok=True)

    for idx, file in enumerate(files):
        if not file or not file.filename:
            continue
        if not allowed_file(file.filename):
            current_app.logger.warning(f'Skipping file with disallowed extension: {file.filename}')
            continue

        try:
            # Generate filename with counter
            new_name = f"acc_{accommodation_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}.jpg"
            disk_path = os.path.join(upload_dir, new_name)

            img = Image.open(file)
            
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Resize maintaining aspect ratio
            img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
            
            # Save as JPEG for consistency
            img.save(disk_path, 'JPEG', quality=85, optimize=True)
            
            saved.append(f'uploads/accommodations/{new_name}')
            
        except Exception as e:
            current_app.logger.error(f'Error saving accommodation image: {str(e)}')
            continue

    return saved

# ------------------------------------------------------------------
# Price calculator
# ------------------------------------------------------------------
def calculate_total_price(price_per_month, duration, period=None):
    if duration == 'annual':
        return price_per_month * 10
    elif duration == 'semester':
        return price_per_month * 5
    return 0

# ------------------------------------------------------------------
# Amenities icon mapper
# ------------------------------------------------------------------
def get_amenities_icons():
    return {
        'wifi': 'wifi',
        'laundry': 'tshirt',
        'kitchen': 'utensils',
        'parking': 'car',
        'gym': 'dumbbell',
        'pool': 'swimming-pool',
        'tv': 'tv',
        'ac': 'snowflake',
        'heating': 'thermometer-half',
        'security': 'shield-alt',
        'cleaning': 'broom',
        'study': 'book',
        'furnished': 'couch'
    }

# ------------------------------------------------------------------
# Convert comma-separated string -> list
# ------------------------------------------------------------------
def format_amenities_list(amenities_string):
    if not amenities_string:
        return []
    return [amenity.strip().lower() for amenity in amenities_string.split(',')]

# ------------------------------------------------------------------
# Dashboard stats
# ------------------------------------------------------------------
def get_dashboard_stats():
    from app.models import db, User, Accommodation, Booking, Payment
    return {
        'total_users': User.query.count(),
        'total_accommodations': Accommodation.query.count(),
        'total_bookings': Booking.query.count(),
        'pending_bookings': Booking.query.filter_by(status='pending').count(),
        'approved_bookings': Booking.query.filter_by(status='approved').count(),
        'paid_bookings': Booking.query.filter_by(status='paid').count(),
        'total_revenue': db.session.query(db.func.sum(Payment.amount)).filter_by(status='succeeded').scalar() or 0
    }

# ------------------------------------------------------------------
# Fake email logger
# ------------------------------------------------------------------
def send_test_payment_success_email(user_email, booking_id):
    current_app.logger.info(f'[TEST MODE] Payment success email would be sent to {user_email} for booking #{booking_id}')
    return True