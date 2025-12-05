import sys
import os

# Ensure project root is in sys.path so 'from api.app' works
root_path = os.path.join(os.path.dirname(__file__), "..")
if root_path not in sys.path:
    sys.path.append(root_path)

from api.app.main import app
