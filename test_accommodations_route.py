# test_accommodations_route.py - Test the actual route access
import requests
import sys
from app import create_app, db
from app.models import Accommodation

def test_route():
    app = create_app()
    
    # Test 1: Simple route access
    print("=== Testing /accommodations route ===")
    with app.test_client() as client:
        response = client.get('/accommodations')
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 500:
            print(f"500 Error Details: {response.data.decode()}")
        elif response.status_code == 404:
            print("404 - Route not found or template missing")
        elif response.status_code == 200:
            print("Route is working!")
            print(f"Response length: {len(response.data)} bytes")
        else:
            print(f"Response data: {response.data.decode()[:500]}...")

def test_database():
    print("\n=== Testing Database Connection ===")
    app = create_app()
    with app.app_context():
        try:
            # Test database connection
            count = Accommodation.query.count()
            print(f"Database connection successful")
            print(f"Total accommodations in database: {count}")
            
            # Test if any accommodations are available
            available = Accommodation.query.filter_by(status='available').count()
            print(f"Available accommodations: {available}")
            
            # Test a simple query like the one in your route
            test_query = Accommodation.query.filter_by(status='available')\
                .order_by(Accommodation.created_at.desc())\
                .paginate(page=1, per_page=12, error_out=False)
            print(f"Test query successful: {len(test_query.items)} items")
            
        except Exception as e:
            print(f"Database error: {e}")
            import traceback
            traceback.print_exc()

def test_template():
    print("\n=== Testing Template Loading ===")
    app = create_app()
    with app.app_context():
        try:
            from flask import render_template
            # Try to render just the template without data
            result = render_template('main/accommodations.html', 
                                   accommodations=[],
                                   form=None,
                                   amenities_icons={})
            print("Template loads successfully!")
            print(f"Template length: {len(result)} characters")
        except Exception as e:
            print(f"Template error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_database()
    test_template()
    test_route()