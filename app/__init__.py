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
    """Drop all tables using CASCADE"""
    with app.app_context():
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool
        
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        engine = create_engine(database_url, poolclass=NullPool)
        
        try:
            with engine.connect() as connection:
                # Get all table names
                result = connection.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                    AND tablename NOT LIKE 'pg_%'
                    AND tablename NOT LIKE 'sql_%';
                """))
                tables = [row[0] for row in result.fetchall()]
                
                app.logger.info(f"Found tables to drop: {tables}")
                
                # Drop all tables with CASCADE
                for table in tables:
                    try:
                        connection.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                        connection.commit()
                        app.logger.info(f"Dropped table: {table}")
                    except Exception as e:
                        connection.rollback()
                        app.logger.warning(f"Could not drop {table}: {e}")
                
                # Drop alembic version
                try:
                    connection.execute(text('DROP TABLE IF EXISTS alembic_version CASCADE'))
                    connection.commit()
                except:
                    pass
                
                app.logger.info("Schema reset completed successfully")
                return True
                
        except Exception as e:
            app.logger.error(f"Schema reset error: {e}")
            import traceback
            app.logger.error(traceback.format_exc())
            return False
        finally:
            engine.dispose()

# ------------------------------------------------------------------
# App Factory
# ------------------------------------------------------------------
def create_app(config_class='config.Config'):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    # Filters
    app.jinja_env.filters['rjust'] = rjust_filter
    app.jinja_env.filters['ljust'] = ljust_filter
    app.jinja_env.filters['center'] = center_filter

    # Stripe
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Upload folders
    os.makedirs(os.path.join(app.root_path, 'static/uploads/profiles'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static/uploads/accommodations'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static/images'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static/img'), exist_ok=True)

    # EMERGENCY RESET - Comment out after first deploy!
    app.logger.info("Starting database reset...")
    success = reset_database_schema(app)
    app.logger.info(f"Database reset result: {success}")

    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.bookings import bp as bookings_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(admin_bp)

    # Serve uploads
    @app.route('/static/uploads/<path:filename>')
    def uploaded_files(filename):
        return send_from_directory(
            os.path.join(app.root_path, 'static/uploads'),
            filename
        )

    # Create tables and seed
    with app.app_context():
        try:
            app.logger.info("Creating all tables...")
            db.create_all()
            app.logger.info("Tables created successfully")
            
            app.logger.info("Seeding admin user...")
            seed_admin_user(app)
            app.logger.info("Admin seeding completed")
            
        except Exception as e:
            app.logger.error(f"Database setup error: {e}")
            import traceback
            app.logger.error(traceback.format_exc())

    return app

def seed_admin_user(app):
    """Seed admin user"""
    try:
        from app.models import User
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@unistay.com')
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        
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
        else:
            app.logger.info(f"Admin exists: {admin_email}")
    except Exception as e:
        app.logger.error(f"Admin seed error: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        db.session.rollback()

# User loader
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))