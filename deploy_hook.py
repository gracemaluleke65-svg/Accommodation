# deploy_hook.py
import os
import sys

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from sqlalchemy import text

app = create_app('config.Config')

with app.app_context():
    print("🔄 Setting up database...")
    
    try:
        # CRITICAL FIX: Drop all tables with CASCADE to handle foreign keys
        print("Dropping all existing tables with CASCADE...")
        
        # Get database connection
        with db.engine.connect() as conn:
            # Disable foreign key checks temporarily (PostgreSQL specific)
            conn.execute(text("DROP TABLE IF EXISTS policies CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS system_logs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS claims CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS payments CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS reviews CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS bookings CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS favorites CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS accommodations CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.commit()
            print("✅ All old tables dropped")
        
        # Now create fresh tables
        print("Creating new tables...")
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Seed admin user
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@unistay.com')
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        
        if not User.query.filter_by(email=admin_email).first():
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
            print(f"✅ Admin user created: {admin_email}")
        else:
            print(f"ℹ️  Admin user already exists: {admin_email}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("🚀 Starting application...")