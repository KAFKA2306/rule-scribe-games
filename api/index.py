import sys
import os

# Ensure project root is in sys.path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

try:
    from app.main import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/api/{path:path}")
    def debug_error(path: str):
        return {
            "error": str(e),
            "type": type(e).__name__
        }
