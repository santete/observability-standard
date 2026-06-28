import os
import time
from playwright.sync_api import sync_playwright

url = "http://localhost:5601/app/dashboards#/view/executive-overview-dashboard"

print(f"Launching browser to listen to page errors on: {url}")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    
    # Listen to console messages
    page.on("console", lambda msg: print(f"[CONSOLE {msg.type.upper()}] {msg.text}") if msg.type in ["error", "warning"] else None)
    
    # Listen to page errors (uncaught exceptions)
    page.on("pageerror", lambda err: print(f"[PAGE EXCEPTION] {err.message}\n{err.stack}"))
    
    print("Navigating to page...")
    page.goto(url)
    
    print("Waiting 15 seconds for rendering...")
    time.sleep(15)
    
    browser.close()
print("Finished.")
