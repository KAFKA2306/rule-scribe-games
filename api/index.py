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
            "error_type": type(e).__name__,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "sys_path": sys.path,
            "cwd": os.getcwd(),
            "contents": os.listdir(".")
        }
