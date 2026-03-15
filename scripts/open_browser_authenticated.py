import json
import time
import os
from playwright.sync_api import sync_playwright

def open_authenticated_browser(session_data=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        url = "http://localhost:5173"
        page.goto(url)

        if session_data:
            print("🔑 Injecting session into LocalStorage...")
            project_id = "wazgoplarevypdfbgeau"
            storage_key = f"sb-{project_id}-auth-token"
            script = f"localStorage.setItem('{storage_key}', JSON.stringify({json.dumps(session_data)}))"
            page.evaluate(script)
            page.reload()
        else:
            print("⚠️ No session data provided. Opening browser in guest mode.")

        print("✓ Authenticated browser opened. Press Ctrl+C to close...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing browser...")
            browser.close()

if __name__ == "__main__":
    env_session = os.getenv("SUPABASE_SESSION")
    session_json = json.loads(env_session) if env_session else None
    open_authenticated_browser(session_json)
