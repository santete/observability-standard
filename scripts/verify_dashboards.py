"""
verify_dashboards.py - Playwright verification only (dashboards already imported)
"""
import os
import time
from playwright.sync_api import sync_playwright

artifact_dir = r"C:\Users\nangh\.gemini\antigravity\brain\ebba6e7b-5d89-46c8-bb3c-76a747786481"

dashboards_to_test = [
    ("executive-overview-dashboard", "executive_overview_v2.png"),
    ("developer-deepdive-dashboard", "developer_deepdive_v2.png"),
    ("infrastructure-runtime-dashboard", "infrastructure_runtime_v2.png")
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    for db_id, filename in dashboards_to_test:
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        url = f"http://localhost:5601/app/dashboards#/view/{db_id}"
        print(f"\nLoading: {db_id}")
        page.goto(url)
        page.wait_for_timeout(20000)
        
        screenshot_out = os.path.join(artifact_dir, filename)
        page.screenshot(path=screenshot_out, full_page=False)
        print(f"Screenshot saved: {screenshot_out}")
        
        # Check for render errors
        errors = page.eval_on_selector_all(
            "p, div, span",
            "els => els.map(el => el.innerText).filter(t => t && (t.includes('Cannot read properties') || t.includes('visualization error') || t.includes('Error loading') || t.includes('Unable to render')))"
        )
        unique_errors = list(set(e.strip() for e in errors if e.strip()))
        
        if unique_errors:
            print(f"[FAIL] ERRORS in {db_id}:")
            for err in unique_errors[:5]:
                print(f"  - {err[:200]}")
        else:
            print(f"[PASS] {db_id}: ZERO ERRORS!")
        
        # Also check page title to confirm we're on the right page
        title = page.title()
        print(f"Page title: {title[:80]}")
        
        page.close()
    
    browser.close()

print("\nAll verifications complete.")
