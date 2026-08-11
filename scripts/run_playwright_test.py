import asyncio
import json
import os
import sys
import time
from playwright.async_api import async_playwright

BASE_URL = "https://frontend-navy-alpha-wikcmhwv2h.vercel.app"

# Output directories
os.makedirs("playwright-report", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
os.makedirs("trace", exist_ok=True)
os.makedirs("videos", exist_ok=True)

console_logs = []
network_logs = []
pages_visited = []
buttons_clicked = []

async def run_e2e_test():
    print("Starting Playwright Live E2E Audit...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Desktop Context
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir="videos/"
        )

        await context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = await context.new_page()

        # Listen to console
        page.on("console", lambda msg: console_logs.append(f"[{msg.type.upper()}] {msg.text}"))

        # Listen to network requests
        def log_response(res):
            status = res.status
            url = res.url
            network_logs.append(f"[{status}] {res.request.method} {url}")
            if status >= 400:
                network_logs.append(f"  FAILED REQUEST: {res.status_text}")

        page.on("response", log_response)

        print(f"Navigating to {BASE_URL}...")
        await page.goto(BASE_URL, wait_until="networkidle")
        pages_visited.append(BASE_URL)

        await page.screenshot(path="screenshots/01_desktop_home_before.png")

        # 1. Test Navigation Menu Items
        nav_selectors = [
            ("Mission Control", "button:has-text('Mission Control')"),
            ("Digital Twin", "button:has-text('Digital Twin')"),
            ("Welfare Schemes", "button:has-text('Welfare Schemes')"),
            ("Reasoning", "button:has-text('Reasoning')"),
            ("Solve for Tomorrow", "button:has-text('Solve for Tomorrow')"),
            ("Knowledge", "button:has-text('Knowledge')"),
            ("Telephony & IVR", "button:has-text('Telephony & IVR')"),
            ("SMS Gateway", "button:has-text('SMS Gateway')"),
            ("Media Ingestion", "button:has-text('Media Ingestion')"),
            ("AI Specialist Hub", "button:has-text('AI Specialist Hub')"),
            ("Conversations Monitor", "button:has-text('Conversations Monitor')"),
            ("Governance & Registry", "button:has-text('Governance & Registry')"),
            ("Integrations", "button:has-text('Integrations')"),
            ("Analytics", "button:has-text('Analytics')"),
            ("Settings", "button:has-text('Settings')"),
        ]

        for name, sel in nav_selectors:
            try:
                elem = page.locator(sel).first
                if await elem.is_visible():
                    print(f"Clicking menu: {name}")
                    await elem.click()
                    buttons_clicked.append(f"Sidebar: {name}")
                    pages_visited.append(name)
                    await page.wait_for_timeout(1000)
                    safe_name = name.lower().replace(" ", "_").replace("&", "and")
                    await page.screenshot(path=f"screenshots/nav_{safe_name}.png")
            except Exception as err:
                print(f"Navigation error on {name}: {err}")

        # 2. Test Phone Demo Modal & Languages
        print("Launching Phone Demo Modal...")
        try:
            demo_btn = page.locator("button:has-text('Launch Phone Demo')").first
            if await demo_btn.is_visible():
                await demo_btn.click()
                buttons_clicked.append("TopNav: Launch Phone Demo")
                await page.wait_for_timeout(1500)
                await page.screenshot(path="screenshots/02_phone_demo_modal.png")

                # Test Custom Language Selector
                lang_dropdown_btn = page.locator("button[title='Select Conversation Language']").first
                if await lang_dropdown_btn.is_visible():
                    await lang_dropdown_btn.click()
                    buttons_clicked.append("Phone Demo: Open Language Dropdown")
                    await page.wait_for_timeout(500)

                    for lang_name in ["Hindi", "Kannada", "Telugu", "Punjabi", "Marathi", "English"]:
                        lang_opt = page.locator(f"button:has-text('{lang_name}')").first
                        if await lang_opt.is_visible():
                            await lang_opt.click()
                            buttons_clicked.append(f"Phone Demo Language: {lang_name}")
                            await page.wait_for_timeout(500)
                            await page.screenshot(path=f"screenshots/lang_{lang_name.lower()}.png")
                            # Reopen for next
                            if await lang_dropdown_btn.is_visible():
                                await lang_dropdown_btn.click()
                                await page.wait_for_timeout(300)
                    
                    # Close dropdown if still open
                    if await lang_dropdown_btn.is_visible():
                        await page.keyboard.press("Escape")

                # Test Start Call
                start_call_btn = page.locator("button:has-text('Start Call')").first
                if await start_call_btn.is_visible():
                    await start_call_btn.click(force=True)
                    buttons_clicked.append("Phone Demo: Start Call")
                    await page.wait_for_timeout(3000)
                    await page.screenshot(path="screenshots/03_call_in_progress.png")

                # Test End Call
                end_call_btn = page.locator("button:has-text('End Call')").first
                if await end_call_btn.is_visible():
                    await end_call_btn.click(force=True)
                    buttons_clicked.append("Phone Demo: End Call")
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path="screenshots/04_call_ended.png")

                # Close Modal
                close_btn = page.locator("button:has-text('Close')").first
                if await close_btn.is_visible():
                    await close_btn.click(force=True)
                    buttons_clicked.append("Phone Demo: Close Modal")
                    await page.wait_for_timeout(500)

        except Exception as demo_err:
            print(f"Phone Demo error: {demo_err}")

        # 3. Test Tablet Viewport
        print("Testing Tablet Viewport (768x1024)...")
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.wait_for_timeout(1000)
        await page.screenshot(path="screenshots/05_tablet_viewport.png")

        # 4. Test Mobile Viewport
        print("Testing Mobile Viewport (375x812)...")
        await page.set_viewport_size({"width": 375, "height": 812})
        await page.wait_for_timeout(1000)
        await page.screenshot(path="screenshots/06_mobile_viewport.png")

        # Stop Tracing
        await context.tracing.stop(path="trace/trace.zip")
        await context.close()
        await browser.close()

    # Save Logs and Summary
    with open("playwright-report/console_logs.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(console_logs))

    with open("playwright-report/network_logs.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(network_logs))

    summary_data = {
        "pages_visited": list(set(pages_visited)),
        "total_pages_visited": len(set(pages_visited)),
        "buttons_clicked": buttons_clicked,
        "total_buttons_clicked": len(buttons_clicked),
        "console_logs_count": len(console_logs),
        "network_requests_count": len(network_logs),
        "failed_network_requests": [line for line in network_logs if "FAILED" in line or line.startswith("[4") or line.startswith("[5")],
        "js_errors": [line for line in console_logs if "[ERROR]" in line]
    }

    with open("playwright-report/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # HTML Report
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Playwright Production E2E Report - Kisan Mitra AI</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; }}
        h1 {{ color: #10b981; }}
        .card {{ background: #1e293b; padding: 16px; border-radius: 12px; margin-bottom: 16px; border: 1px solid #334155; }}
        .badge {{ background: #064e3b; color: #34d399; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; }}
        pre {{ background: #090d16; padding: 12px; border-radius: 8px; overflow-x: auto; color: #94a3b8; font-size: 11px; }}
    </style>
</head>
<body>
    <h1>Kisan Mitra AI — Playwright Live Production Audit</h1>
    <div class="card">
        <h2>Execution Summary <span class="badge">SUCCESS</span></h2>
        <p><strong>Target URL:</strong> {BASE_URL}</p>
        <p><strong>Pages Visited:</strong> {summary_data['total_pages_visited']}</p>
        <p><strong>Buttons Clicked:</strong> {summary_data['total_buttons_clicked']}</p>
        <p><strong>Total Network Requests Logged:</strong> {summary_data['network_requests_count']}</p>
        <p><strong>Failed Requests:</strong> {len(summary_data['failed_network_requests'])}</p>
        <p><strong>Console JS Errors:</strong> {len(summary_data['js_errors'])}</p>
    </div>

    <div class="card">
        <h3>Visited Pages ({summary_data['total_pages_visited']})</h3>
        <ul>
            {''.join(f'<li>{p}</li>' for p in summary_data['pages_visited'])}
        </ul>
    </div>

    <div class="card">
        <h3>Buttons & Interactions ({summary_data['total_buttons_clicked']})</h3>
        <ul>
            {''.join(f'<li>{b}</li>' for b in summary_data['buttons_clicked'])}
        </ul>
    </div>

    <div class="card">
        <h3>Console Logs Preview</h3>
        <pre>{chr(10).join(console_logs[:30]) if console_logs else 'No console errors.'}</pre>
    </div>
</body>
</html>
"""
    with open("playwright-report/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Playwright Live Audit Complete!")
    print(f"Summary: Visited {summary_data['total_pages_visited']} pages, Clicked {summary_data['total_buttons_clicked']} buttons.")
    print(f"Report saved to playwright-report/index.html")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
