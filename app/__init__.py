from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import stripe
import os

# ------------------------------------------------------------------
# Extensions
# ------------------------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

# ------------------------------------------------------------------
# Custom Jinja2 Filters
# ------------------------------------------------------------------
def rjust_filter(value, width, fillchar=' '):
    """Right-justify string with padding"""
    return str(value).rjust(int(width), str(fillchar))

def ljust_filter(value, width, fillchar=' '):
    """Left-justify string with padding"""
    return str(value).ljust(int(width), str(fillchar))

def center_filter(value, width, fillchar=' '):
    """Center string with padding"""
    return str(value).center(int(width), str(fillchar))

# ------------------------------------------------------------------
# App Factory
# ------------------------------------------------------------------
def create_app(config_class='config.Config'):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    # ------------------------------------------------------------------
    # Register Custom Filters
    # ------------------------------------------------------------------
    app.jinja_env.filters['rjust'] = rjust_filter
    app.jinja_env.filters['ljust'] = ljust_filter
    app.jinja_env.filters['center'] = center_filter

    # ------------------------------------------------------------------
    # Initialize Stripe
    # ------------------------------------------------------------------
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    # ------------------------------------------------------------------
    # Bind extensions
    # ------------------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # ------------------------------------------------------------------
    # Login manager
    # ------------------------------------------------------------------
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # ------------------------------------------------------------------
    # Ensure upload folders exist
    # ------------------------------------------------------------------
    os.makedirs(os.path.join(app.root_path, 'static/uploads/profiles'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static/uploads/accommodations'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static/images'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static/img'), exist_ok=True)

    # ------------------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------------------
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.bookings import bp as bookings_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(admin_bp)

    # ------------------------------------------------------------------
    # Development helper: serve uploaded files
    # ------------------------------------------------------------------
    @app.route('/static/uploads/<path:filename>')
    def uploaded_files(filename):
        return send_from_directory(
            os.path.join(app.root_path, 'static/uploads'),
            filename
        )

    # ------------------------------------------------------------------
    # Database setup - ONLY creates tables if they don't exist
    # NEVER drops tables - that was causing data loss!
    # ------------------------------------------------------------------
    with app.app_context():
        try:
            # Use Flask-Migrate for schema changes, not drop/create
            # This only creates tables if missing, never drops existing
            db.create_all()
            
            # Seed admin user if missing
            seed_admin_user(app)
            
        except Exception as e:
            app.logger.warning(f"Database setup warning (tables may exist): {e}")

    return app

def seed_admin_user(app):
    """Seed admin user - safe to run multiple times"""
    try:
        from app.models import User
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@unistay.com')
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        
        # Only create if admin doesn't exist
        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin = User(
                student_number='00000000',
                full_name='Admin User',
                email=admin_email,
                id_number='0000000000000',
                phone_number='0000000000',
                role='admin'
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            app.logger.info(f"Admin user created: {admin_email}")
        else:
            app.logger.debug(f"Admin user exists: {admin_email}")
            
    except Exception as e:
        app.logger.error(f"Error seeding admin: {e}")
        db.session.rollback()

# ------------------------------------------------------------------
# User loader
# ------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
