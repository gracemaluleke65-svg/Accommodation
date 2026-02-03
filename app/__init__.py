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
    return str(value).rjust(int(width), str(fillchar))

def ljust_filter(value, width, fillchar=' '):
    return str(value).ljust(int(width), str(fillchar))

def center_filter(value, width, fillchar=' '):
    return str(value).center(int(width), str(fillchar))

def reset_database_schema(app):
    """NUCLEAR OPTION: Drop all tables and recreate fresh"""
    with app.app_context():
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool
        
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        engine = create_engine(database_url, poolclass=NullPool)
        
        try:
            with engine.connect() as connection:
                # Disable foreign key checks temporarily (PostgreSQL uses constraints)
                connection.execute(text("SET session_replication_role = 'replica';"))
                connection.commit()
                
                # Get all table names
                result = connection.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public';
                """))
                tables = [row[0] for row in result]
                
                # Drop all tables with CASCADE
                for table in tables:
                    try:
                        connection.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
                        connection.commit()
                        app.logger.info(f"Dropped table: {table}")
                    except Exception as e:
                        connection.rollback()
                        app.logger.warning(f"Could not drop {table}: {e}")
                
                # Re-enable normal mode
                connection.execute(text("SET session_replication_role = 'origin';"))
                connection.commit()
                
                app.logger.info("All tables dropped successfully")
                return True
                
        except Exception as e:
            app.logger.error(f"Error dropping tables: {e}")
            return False
        finally:
            engine.dispose()

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
    # NUCLEAR OPTION: Reset database on startup
    # WARNING: This deletes ALL data!
    # Comment this out after first successful deploy!
    # ------------------------------------------------------------------
    reset_database_schema(app)

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
    # Database setup - Create all tables fresh
    # ------------------------------------------------------------------
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("All tables created successfully")
            seed_admin_user(app)
        except Exception as e:
            app.logger.error(f"Database setup error: {e}")

    return app

def seed_admin_user(app):
    """Seed admin user"""
    try:
        from app.models import User
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@unistay.com')
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        
        # Check if admin exists
        existing = User.query.filter_by(email=admin_email).first()
        if not existing:
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
            app.logger.info(f"Admin created: {admin_email}")
    except Exception as e:
        app.logger.error(f"Admin seed error: {e}")
        db.session.rollback()

# ------------------------------------------------------------------
# User loader
# ------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))