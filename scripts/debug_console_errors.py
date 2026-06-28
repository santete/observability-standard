"""
debug_browser_console.py - Capture browser console errors from Kibana dashboard
to get the full stack trace for lnsDatatable failures.
"""
import os
import time
from playwright.sync_api import sync_playwright

artifact_dir = r"C:\Users\nangh\.gemini\antigravity\brain\ebba6e7b-5d89-46c8-bb3c-76a747786481"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    # Collect all console messages and errors
    console_errors = []
    page_errors = []
    
    page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
    page.on("pageerror", lambda err: page_errors.append(str(err)))
    
    url = "http://localhost:5601/app/dashboards#/view/developer-deepdive-dashboard"
    print(f"Loading: {url}")
    page.goto(url)
    page.wait_for_timeout(18000)
    
    screenshot_path = os.path.join(artifact_dir, "developer_deepdive_debug.png")
    page.screenshot(path=screenshot_path)
    print(f"Screenshot: {screenshot_path}")
    
    print("\n=== BROWSER CONSOLE ERRORS ===")
    for i, err in enumerate(console_errors[:30]):
        print(f"  [{i}] {err[:300]}")
    
    print("\n=== PAGE ERRORS (uncaught exceptions) ===")
    for i, err in enumerate(page_errors[:10]):
        print(f"  [{i}] {err[:500]}")
    
    # Also try to get the full Kibana error message from the page
    print("\n=== VISIBLE ERROR TEXT IN PAGE ===")
    error_texts = page.eval_on_selector_all(
        ".euiPanel, .lens-embeddable-error, [data-test-subj*='embeddable-panel-error']",
        "els => els.map(el => el.innerText).filter(t => t && t.length > 5)"
    )
    for t in error_texts[:10]:
        print(f"  - {t[:400]}")
    
    # Also get all text content containing "Cannot" or "Error"
    print("\n=== ALL ERROR-LIKE TEXT ===")
    all_errors = page.eval_on_selector_all(
        "*",
        "els => [...new Set(els.map(el => el.innerText).filter(t => t && t.includes('Cannot read')))].slice(0, 5)"
    )
    for t in all_errors:
        print(f"  - {t[:300]}")
    
    browser.close()

print("\nDone.")
