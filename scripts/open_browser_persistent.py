import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def launch_persistent_browser():
    user_data_dir = Path("./.playwright_data")
    user_data_dir.mkdir(exist_ok=True)

    print(f"📂 Using browser profile in: {user_data_dir.absolute()}")
    print("💡 TIP: Login manually in the opened window. Profiles are saved automatically.")

    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )

        page = browser_context.new_page()
        page.goto("http://localhost:5173")

        print("✓ Persistent browser opened. Press Ctrl+C to close...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing browser...")
            browser_context.close()

if __name__ == "__main__":
    launch_persistent_browser()
