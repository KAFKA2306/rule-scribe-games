import os
import sys

# Add backend to sys.path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(root_path, "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.main import app
