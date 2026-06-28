"""
debug_headed.py - Run Playwright in HEADED mode to simulate real browser behavior
and capture actual JavaScript errors including 'reading map'.
"""
import os
import time
from playwright.sync_api import sync_playwright

artifact_dir = r"C:\Users\nangh\.gemini\antigravity\brain\ebba6e7b-5d89-46c8-bb3c-76a747786481"

with sync_playwright() as p:
    # Use headed=True to simulate real browser, and use a fresh browser context
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        # Force fresh cache - no cached state
        ignore_https_errors=True
    )
    page = context.new_page()
    
    # Capture ALL javascript errors
    page_errors = []
    console_errors = []
    
    page.on("pageerror", lambda err: page_errors.append(str(err)))
    page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") 
            if msg.type in ("error", "warning") else None)
    
    url = "http://localhost:5601/app/dashboards#/view/executive-overview-dashboard"
    print(f"Loading: {url}")
    page.goto(url)
    
    # Wait for either panels to render OR errors to appear
    # Look for either success or error state
    print("Waiting 25 seconds for full render...")
    page.wait_for_timeout(25000)
    
    # Take screenshot
    screenshot_path = os.path.join(artifact_dir, "headed_debug.png")
    page.screenshot(path=screenshot_path, full_page=False)
    print(f"Screenshot: {screenshot_path}")
    
    # Get page title
    print(f"Page title: {page.title()}")
    
    # Check for ANY errors in page content
    all_text = page.eval_on_selector_all(
        "body *",
        "els => [...new Set(els.map(el => el.innerText).filter(t => t && t.includes('Cannot read')))].slice(0, 5)"
    )
    
    print("\n=== VISIBLE ERRORS ===")
    for t in all_text:
        print(f"  - {t[:300]}")
    
    print("\n=== PAGE ERRORS (uncaught JS exceptions) ===")
    for e in page_errors[:10]:
        print(f"  - {e[:400]}")
    
    print("\n=== CONSOLE ERRORS ===")
    for e in console_errors[:10]:
        print(f"  - {e[:300]}")
    
    # Check panel render status
    panels_ok = page.eval_on_selector_all(
        "[data-test-subj='embeddablePanel']",
        "els => els.map(el => ({ title: el.querySelector('[data-test-subj=\"embeddablePanelHeading-\"]')?.innerText || '?', hasError: !!el.querySelector('.euiEmptyPrompt') }))"
    )
    print("\n=== PANEL STATUS ===")
    for p_info in panels_ok:
        print(f"  {p_info}")
    
    browser.close()
    print("\nDone.")
