import os
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
from datetime import datetime
import base64
import io

# ------------------------------------------------------------------
# Image processing helpers
# ------------------------------------------------------------------
def allowed_file(filename):
    """Check if file extension is allowed (case-insensitive)"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_mime_type(filename):
    """Get MIME type from filename"""
    ext = filename.rsplit('.', 1)[1].lower()
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')

def process_image_to_base64(file, max_size=(800, 600), quality=85):
    """
    Convert uploaded file to Base64 string
    Resizes image to reduce database size
    """
    try:
        img = Image.open(file)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Resize to reduce storage size (critical for Base64 in DB)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to buffer
        buffer = io.BytesIO()
        img_format = 'JPEG' if file.filename.lower().endswith(('.jpg', '.jpeg')) else 'PNG'
        img.save(buffer, format=img_format, quality=quality, optimize=True)
        buffer.seek(0)
        
        # Convert to base64
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        mime_type = get_mime_type(file.filename)
        
        return {
            'data': image_data,
            'type': mime_type,
            'filename': secure_filename(file.filename)
        }
        
    except Exception as e:
        current_app.logger.error(f'Error processing image: {str(e)}')
        return None

# ------------------------------------------------------------------
# PROFILE picture - Base64 storage
# ------------------------------------------------------------------
def save_profile_picture(file, user_id):
    """
    Process profile picture and return Base64 data
    Stores in User.profile_picture_data
    """
    if file and allowed_file(file.filename):
        result = process_image_to_base64(file, max_size=(300, 300), quality=85)
        if result:
            return result
    return None

# ------------------------------------------------------------------
# ACCOMMODATION images - Base64 storage in database
# ------------------------------------------------------------------
def save_accommodation_images(files, accommodation_id):
    """
    Process multiple accommodation images and return list of Base64 data dicts
    These will be stored in AccommodationImage table
    """
    from app.models import AccommodationImage, db
    
    saved_images = []
    
    for idx, file in enumerate(files):
        if not file or not file.filename:
            continue
        if not allowed_file(file.filename):
            current_app.logger.warning(f'Skipping file with disallowed extension: {file.filename}')
            continue

        try:
            # Process image (max 1200x800 for accommodation images)
            result = process_image_to_base64(file, max_size=(1200, 800), quality=85)
            
            if result:
                # Create AccommodationImage object (not saved here, returned for bulk save)
                saved_images.append(result)
                
        except Exception as e:
            current_app.logger.error(f'Error saving accommodation image: {str(e)}')
            continue

    return saved_images

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