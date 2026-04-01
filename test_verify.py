from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("http://localhost:8502")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="/tmp/01_home.png", full_page=True)

    page.fill("input", "AAPL")
    page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="/tmp/02_aapl_loaded.png", full_page=True)

    page.locator("text=Finanzas").click()
    page.wait_for_load_state("networkidle")
    page.screenshot(path="/tmp/03_finanzas_tab.png", full_page=True)

    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

    print("Console logs:", console_logs)
    print("Page title:", page.title())

    browser.close()
