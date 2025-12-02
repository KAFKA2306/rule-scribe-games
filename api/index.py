import sys
import os

# Add the backend directory to sys.path so that 'app' can be imported as a top-level package
# This matches the local development environment structure
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_path)

from app.main import app
