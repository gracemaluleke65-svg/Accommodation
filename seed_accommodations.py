# seed_accommodations.py
import os
import json
from app import app, db
from models import Accommodation
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil

def seed_accommodations():
    """Seed accommodations only if they don't already exist"""
    
    # Define all accommodations with their data
    accommodations_data = [
        {
            'title': 'Maboneng Study Loft',
            'description': 'Modern student loft in the heart of Johannesburg CBD, walking distance to University of Johannesburg satellite campuses. Close to cafes, Gautrain buses, art spaces, and 24/7 security patrols.',
            'location': 'Johannesburg CBD, Gauteng',
            'room_type': 'apartment',
            'price_per_month': 4800.00,
            'capacity': 130,
            'current_occupancy': 52,
            'amenities': ['wifi', 'parking', 'laundry', 'furnished', 'security', 'study_area'],
            'image_source': 'static/images/team/Accommodations/Maboneng Study Loft.jpg'
        },
        {
            'title': 'Hatfield Campus Residence',
            'description': 'Popular student residence near University of Pretoria. Includes shuttle access, quiet study lounges, and vibrant student community.',
            'location': 'Hatfield, Pretoria',
            'room_type': 'single',
            'price_per_month': 5900.00,
            'capacity': 290,
            'current_occupancy': 98,
            'amenities': ['wifi', 'laundry', 'gym', 'furnished', 'security', 'study_area'],
            'image_source': 'static/images/team/Accommodations/Hatfield Campus Residence.webp'
        },
        {
            'title': 'Braamfontein Scholar House',
            'description': 'Located in Braamfontein, ideal for Wits University students. Surrounded by libraries, bookstores, and student nightlife.',
            'location': 'Braamfontein, Johannesburg',
            'room_type': 'shared',
            'price_per_month': 4900.00,
            'capacity': 325,
            'current_occupancy': 75,
            'amenities': ['wifi', 'laundry', 'security', 'study_area'],
            'image_source': 'static/images/team/Accommodations/Braamfontein Scholar House.webp'
        },
        {
            'title': 'Observatory Student Living',
            'description': 'Trendy Cape Town student housing near UCT. Easy access to train station and campus shuttle routes.',
            'location': 'Observatory, Cape Town',
            'room_type': 'single',
            'price_per_month': 6500.00,
            'capacity': 200,
            'current_occupancy': 50,
            'amenities': ['wifi', 'parking', 'laundry', 'furnished', 'security', 'study_area'],
            'image_source': 'static/images/team/Accommodations/Observatory Student Living.webp'
        },
        {
            'title': 'Durban North Academic Lodge',
            'description': 'Quiet coastal accommodation close to UKZN. Safe environment with ocean breeze and modern rooms.',
            'location': 'Durban North, KZN',
            'room_type': 'single',
            'price_per_month': 4300.00,
            'capacity': 190,
            'current_occupancy': 55,
            'amenities': ['wifi', 'parking', 'laundry', 'furnished', 'security'],
            'image_source': 'static/images/team/Accommodations/Durban North Academic Lodge.jpg'
        },
        {
            'title': 'Sunnyside Student Apartments',
            'description': 'Affordable Pretoria student housing close to transport routes and shops.',
            'location': 'Sunnyside, Pretoria',
            'room_type': 'shared',
            'price_per_month': 4000.00,
            'capacity': 360,
            'current_occupancy': 140,
            'amenities': ['wifi', 'laundry', 'security', 'study_area'],
            'image_source': 'static/images/team/Accommodations/Sunnyside Student Apartments.jpg'
        },
        {
            'title': 'Rosebank Campus Hub',
            'description': 'Premium student accommodation near Rosebank Mall and transport interchange.',
            'location': 'Rosebank, Johannesburg',
            'room_type': 'apartment',
            'price_per_month': 7800.00,
            'capacity': 45,
            'current_occupancy': 38,
            'amenities': ['wifi', 'parking', 'gym', 'furnished', 'security', 'study_area'],
            'image_source': 'static/images/team/Accommodations/Rosebank Campus Hub.jpg'
        },
        {
            'title': 'Stellenbosch Green Residences',
            'description': 'Peaceful student living surrounded by vineyards and university campuses.',
            'location': 'Stellenbosch, Western Cape',
            'room_type': 'single',
            'price_per_month': 6200.00,
            'capacity': 90,
            'current_occupancy': 72,
            'amenities': ['wifi', 'parking', 'laundry', 'furnished', 'security', 'study_area'],
            'image_source': 'static/images/team/Accommodations/Stellenbosch Green Residences.jpg'
        },
        {
            'title': 'Hatfield Studios',
            'description': 'Modern high-rise student suites in the city centre with 24/7 security.',
            'location': 'Pretoria Hatfield, Gauteng',
            'room_type': 'apartment',
            'price_per_month': 5900.00,
            'capacity': 240,
            'current_occupancy': 95,
            'amenities': ['wifi', 'parking', 'gym', 'furnished', 'security', 'study_area'],
            'image_source': 'static/images/team/Accommodations/Hatfield Campus Residence.webp'
        }
    ]
    
    # Get admin user (first admin in database)
    from models import User
    admin = User.query.filter_by(is_admin=True).first()
    
    if not admin:
        print("⚠️ No admin user found. Please ensure admin exists before seeding.")
        return
    
    accommodations_added = 0
    
    for acc_data in accommodations_data:
        # Check if accommodation already exists (by title)
        existing = Accommodation.query.filter_by(title=acc_data['title']).first()
        
        if existing:
            print(f"⏭️ Skipping existing accommodation: {acc_data['title']}")
            continue
        
        # Create new accommodation
        accommodation = Accommodation(
            title=acc_data['title'],
            description=acc_data['description'],
            location=acc_data['location'],
            room_type=acc_data['room_type'],
            price_per_month=acc_data['price_per_month'],
            capacity=acc_data['capacity'],
            current_occupancy=acc_data['current_occupancy'],
            admin_id=admin.id,
            is_active=True
        )
        
        # Set amenities
        accommodation.set_amenities_list(acc_data['amenities'])
        
        # Handle image copy
        image_source = acc_data['image_source']
        if os.path.exists(image_source):
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            original_filename = os.path.basename(image_source)
            name, ext = os.path.splitext(original_filename)
            new_filename = f"{timestamp}_{secure_filename(name)}{ext}"
            
            # Copy to uploads folder
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            try:
                shutil.copy2(image_source, upload_path)
                accommodation.image_filename = new_filename
                print(f"📸 Copied image for {acc_data['title']}")
            except Exception as e:
                print(f"⚠️ Could not copy image for {acc_data['title']}: {e}")
        else:
            print(f"⚠️ Image not found for {acc_data['title']}: {image_source}")
        
        db.session.add(accommodation)
        accommodations_added += 1
        print(f"✅ Added accommodation: {acc_data['title']}")
    
    if accommodations_added > 0:
        db.session.commit()
        print(f"\n🎉 Successfully added {accommodations_added} new accommodations!")
    else:
        print("\n📝 No new accommodations were added (all already exist).")
    
    return accommodations_added

def update_existing_accommodations():
    """Optional: Update existing accommodations with new data if needed"""
    # You can add logic here to update existing accommodations
    # For now, we'll just skip this
    pass

if __name__ == '__main__':
    with app.app_context():
        seed_accommodations()