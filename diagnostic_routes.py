# diagnostic_routes.py - Add this to your project to debug routes
from flask import Flask, current_app
from app import create_app

def debug_routes():
    app = create_app()
    with app.app_context():
        print("=== REGISTERED ROUTES ===")
        for rule in current_app.url_map.iter_rules():
            print(f"Endpoint: {rule.endpoint}")
            print(f"URL: {rule.rule}")
            print(f"Methods: {list(rule.methods)}")
            print("---")

if __name__ == "__main__":
    debug_routes()