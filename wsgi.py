from app import create_app
import os

app = create_app('config.Config')

# Handle Render deployment - run migrations if possible
if os.environ.get('RENDER'):
    try:
        from flask_migrate import upgrade
        with app.app_context():
            upgrade()
            print("Database migrations applied successfully")
    except Exception as e:
        print(f"Migration warning (may be already applied): {e}")

if __name__ == "__main__":
    app.run()