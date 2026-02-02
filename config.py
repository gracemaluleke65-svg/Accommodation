import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Handle Render's postgres:// vs postgresql:// issue
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///unistay.db'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # CRITICAL FIX: Add SSL mode for Render PostgreSQL (free tier requirement)
    if 'render.com' in database_url and '?' not in database_url:
        database_url += '?sslmode=require'
    elif 'render.com' in database_url and 'sslmode' not in database_url:
        database_url += '&sslmode=require'
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pool settings for Render PostgreSQL stability
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,      # Verify connections before using
        'pool_recycle': 300,        # Recycle every 5 minutes
        'pool_timeout': 30,         # Wait 30 sec for connection
        'max_overflow': 10,         # Allow 10 extra connections
        'pool_size': 10             # Base pool size
    }

    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Stripe configuration (TEST MODE) - Use env vars in production
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_your_key_here'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_your_key_here'
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # App settings
    ITEMS_PER_PAGE = 12
    
    # Admin credentials from env (secure for production)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@unistay.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
