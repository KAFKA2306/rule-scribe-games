import os
import sys

# Ensure backend directory is prioritized in sys.path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(root_path, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the production app
from app.main import app
