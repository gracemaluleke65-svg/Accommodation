from app import create_app
import os
import sys

try:
    app = create_app('config.Config')
    print("Flask app created successfully", file=sys.stderr)
except Exception as e:
    print(f"Error creating app: {e}", file=sys.stderr)
    import traceback
    print(traceback.format_exc(), file=sys.stderr)
    raise

if __name__ == "__main__":
    app.run()