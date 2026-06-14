from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import base64

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(8), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    # Changed: Store Base64 image data instead of file path
    profile_picture_data = db.Column(db.Text)  # Base64 encoded image
    profile_picture_type = db.Column(db.String(50))  # MIME type (e.g., 'image/jpeg')
    id_number = db.Column(db.String(13), unique=True, nullable=False)
    phone_number = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def profile_picture(self):
        """Return data URI for HTML img src"""
        if self.profile_picture_data:
            return f"data:{self.profile_picture_type};base64,{self.profile_picture_data}"
        return 'images/default_profile.png'

class AccommodationImage(db.Model):
    """Store images as Base64 in database - PERSISTS on Render free tier"""
    __tablename__ = 'accommodation_images'
    
    id = db.Column(db.Integer, primary_key=True)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accommodations.id'), nullable=False)
    image_data = db.Column(db.Text, nullable=False)  # Base64 encoded
    image_type = db.Column(db.String(50), nullable=False)  # MIME type
    filename = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_data_uri(self):
        """Convert to data URI for HTML img src"""
        return f"data:{self.image_type};base64,{self.image_data}"

class Accommodation(db.Model):
    __tablename__ = 'accommodations'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price_per_month = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(200), default='Sandton, Johannesburg')
    capacity = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0)
    amenities = db.Column(db.JSON)
    # Removed: images = db.Column(db.JSON) - Now uses relationship
    status = db.Column(db.String(20), default='available')
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('User', backref='accommodations_added')
    favorites = db.relationship('Favorite', backref='accommodation', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='accommodation', lazy=True)
    reviews = db.relationship('Review', backref='accommodation', lazy=True)
    images = db.relationship('AccommodationImage', backref='accommodation', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_available(self):
        return self.current_occupancy < self.capacity and self.status == 'available'
    
    @property
    def average_rating(self):
        if self.reviews:
            return sum(review.rating for review in self.reviews) / len(self.reviews)
        return 0
    
    @property
    def first_image(self):
        """Get first image as data URI or return default"""
        if self.images:
            return self.images[0].to_data_uri()
        return 'images/default_accommodation.jpg'

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accommodations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'accommodation_id'),)

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accommodations.id'), nullable=False)
    duration = db.Column(db.String(20), nullable=False)
    period = db.Column(db.String(10))
    payment_responsible = db.Column(db.String(50), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    stripe_session_id = db.Column(db.String(100))
    stripe_payment_intent_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payment = db.relationship('Payment', backref='booking', lazy=True, uselist=False)

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accommodations.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'accommodation_id'),)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    stripe_payment_id = db.Column(db.String(100), unique=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)