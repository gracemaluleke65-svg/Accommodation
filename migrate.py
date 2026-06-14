from app import create_app, db
from flask_migrate import upgrade, migrate, init, stamp
import os

app = create_app()

with app.app_context():
    # Ensure migrations directory exists
    if not os.path.exists('migrations'):
        init()
    
    # Create a stamp to head if needed
    try:
        stamp()
    except:
        pass
    
    # Run migrations
    upgrade()
    
    print("Migrations completed successfully!")