"""
WSGI application entry point for production servers (Vercel, Gunicorn, etc.)

This file is used by:
- Vercel Python Runtime
- Gunicorn
- Other WSGI-compatible servers

Usage:
  gunicorn wsgi:app
"""

import os
import sys

# Ensure the app directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from app import app

if __name__ == '__main__':
    # This will only be used for local development with gunicorn
    # In Vercel, the api/index.py file is used instead
    app.run()
