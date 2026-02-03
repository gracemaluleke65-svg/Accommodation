#!/bin/bash
# Run migrations (will fail silently if already applied)
flask db upgrade || echo "Migration may have failed or already applied"

# Start the app
gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2
