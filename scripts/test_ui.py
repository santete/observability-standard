import sys
import subprocess
import os
import time

# Ensure playwright is installed
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not found. Installing playwright...")
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    print("Installing chromium browser...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.sync_api import sync_playwright

script_dir = os.path.dirname(os.path.abspath(__file__))
# The artifact directory where we can save the screenshot
artifact_dir = r"C:\Users\nangh\.gemini\antigravity\brain\ebba6e7b-5d89-46c8-bb3c-76a747786481"
screenshot_path = os.path.join(artifact_dir, "kibana_dashboard.png")

print(f"Artifact directory: {artifact_dir}")
print(f"Screenshot will be saved to: {screenshot_path}")

url = "http://localhost:5601/app/dashboards#/view/executive-overview-dashboard"

print(f"Launching headless browser to load: {url}")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    
    print("Navigating to Kibana dashboard...")
    page.goto(url)
    
    print("Waiting 15 seconds for dashboard charts to render...")
    # Wait for the loading indicators to disappear or just sleep to let JS execute
    time.sleep(15)
    
    # Save screenshot
    print("Taking screenshot...")
    page.screenshot(path=screenshot_path)
    print("Screenshot saved successfully!")
    
    # Check if there are any error blocks in the DOM
    print("Analyzing DOM for errors...")
    errors = page.eval_on_selector_all(
        "*[class*='error'], *[class*='warning'], p, div", 
        "elements => elements.map(el => el.innerText).filter(text => text && text.includes('Cannot read properties'))"
    )
    
    if errors:
        print("\n--- FOUND ERRORS IN RENDERING ---")
        for err in set(errors):
            print(f"- {err}")
    else:
        print("\n--- NO RENDERING ERRORS DETECTED ---")
        # Let's print some panel titles to verify they loaded
        panels = page.eval_on_selector_all(
            "span, div",
            "elements => elements.map(el => el.innerText).filter(text => text && (text.includes('Health') || text.includes('Latency') || text.includes('RPS') || text.includes('Requests')))"
        )
        print("Detected panel texts:")
        for p_text in set(panels)[:10]:
            print(f"- {p_text}")
            
    browser.close()
print("UI Verification finished.")
