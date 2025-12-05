import sys
import os

# Ensure project root is in sys.path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

try:
    from app.main import app
except Exception:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse
    
    app = FastAPI()
    error_msg = traceback.format_exc()
    
    @app.get("/api/{path:path}")
    def debug_catch_all(path: str):
        return PlainTextResponse(error_msg, status_code=200)
