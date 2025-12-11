import sys
import os

# Ensure project root is in sys.path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from app.main import app  # noqa: E402, F401
