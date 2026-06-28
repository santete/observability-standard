import os
import time
from playwright.sync_api import sync_playwright

# The URL to load Discover with otel-traces-dataview
url = "http://localhost:5601/app/discover#/view/otel-traces-dataview"

print(f"Launching browser to load Discover: {url}")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    
    page.on("console", lambda msg: print(f"[CONSOLE {msg.type.upper()}] {msg.text}") if msg.type in ["error", "warning"] else None)
    page.on("pageerror", lambda err: print(f"[PAGE EXCEPTION] {err.message}\n{err.stack}"))
    
    print("Navigating to Discover...")
    page.goto(url)
    
    print("Waiting 15 seconds...")
    time.sleep(15)
    
    artifact_dir = r"C:\Users\nangh\.gemini\antigravity\brain\ebba6e7b-5d89-46c8-bb3c-76a747786481"
    screenshot_path = os.path.join(artifact_dir, "kibana_discover_test.png")
    page.screenshot(path=screenshot_path)
    print(f"Screenshot saved to: {screenshot_path}")
    
    browser.close()
print("Finished.")
