import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Handle Render's postgres:// vs postgresql:// issue
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///unistay.db'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Stripe configuration (TEST MODE) - Use env vars in production
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_51RCfdhC4ofBWBtBfsZMlapzUKBqk40bIESk3D1CBlCuE18KdF9rG8gmmjo1FoMwdR8pFit1Xhv2QSUNW8t1AH9R300T2mJ9WY4'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_51RCfdhC4ofBWBtBf5YS6sIJNuqDpY5DnwHmPxXKFgxKzS3sZJjvd4r4ctRGT78Zq2Hmd2Cg26qft2uoNOdMXAm2o00eBqewKdw'
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # App settings
    ITEMS_PER_PAGE = 12
    
    # Admin credentials from env (secure for production)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@unistay.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'