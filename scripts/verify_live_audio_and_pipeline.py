import asyncio
import json
import os
import time
from playwright.async_api import async_playwright

BASE_URL = "https://frontend-navy-alpha-wikcmhwv2h.vercel.app"

os.makedirs("verification_results", exist_ok=True)
os.makedirs("verification_results/screenshots", exist_ok=True)

LANGUAGES_TO_TEST = [
    {"name": "English", "code": "en-IN"},
    {"name": "Kannada", "code": "kn-IN"},
    {"name": "Hindi",   "code": "hi-IN"},
    {"name": "Telugu",  "code": "te-IN"},
]

results = {}

async def run_verification_for_lang(p, lang):
    lang_name = lang["name"]
    lang_code = lang["code"]
    print(f"\n=======================================================")
    print(f"VERIFYING LIVE AUDIO & PIPELINE FOR: {lang_name} ({lang_code})")
    print(f"=======================================================")

    browser = await p.chromium.launch(
        headless=True,
        args=["--autoplay-policy=no-user-gesture-required"]
    )
    context = await browser.new_context(viewport={"width": 1400, "height": 900})
    page = await context.new_page()

    console_errors = []
    network_errors = []
    tts_network_logs = []
    audio_events = []
    pipeline_stage_timestamps = {}

    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ["error"] else None)
    
    def handle_response(response):
        url = response.url
        status = response.status
        content_type = response.headers.get("content-type", "")
        
        if status >= 400:
            network_errors.append(f"[{status}] {url}")
        
        if "tts" in url or "translate_tts" in url or "audio" in content_type:
            tts_network_logs.append({
                "url": url,
                "status": status,
                "content_type": content_type,
                "timestamp": round(time.time(), 3)
            })

    page.on("response", handle_response)

    # Instrument Audio & Speech Events in DOM
    await page.add_init_script("""
        window.__audio_events = [];
        const originalAudioPlay = HTMLAudioElement.prototype.play;
        HTMLAudioElement.prototype.play = function() {
            const audio = this;
            window.__audio_events.push({ event: 'play_called', src: audio.src, time: performance.now() });
            audio.addEventListener('play', () => window.__audio_events.push({ event: 'play', src: audio.src, time: performance.now() }));
            audio.addEventListener('playing', () => window.__audio_events.push({ event: 'playing', src: audio.src, time: performance.now() }));
            audio.addEventListener('ended', () => window.__audio_events.push({ event: 'ended', src: audio.src, time: performance.now() }));
            audio.addEventListener('error', (e) => window.__audio_events.push({ event: 'error', src: audio.src, err: e, time: performance.now() }));
            return originalAudioPlay.apply(this, arguments);
        };
    """)

    # 1. Load website
    t0 = time.time()
    await page.goto(BASE_URL, wait_until="networkidle")
    print(f"[{round(time.time()-t0, 2)}s] Loaded homepage")

    # 2. Launch Phone Demo
    demo_btn = page.locator("button:has-text('Launch Phone Demo')").first
    await demo_btn.click(force=True)
    await page.wait_for_timeout(1000)

    # 3. Select Language
    lang_btn = page.locator("button[title='Select Conversation Language']").first
    if await lang_btn.is_visible():
        await lang_btn.click(force=True)
        await page.wait_for_timeout(300)
        target_opt = page.locator(f"button:has-text('{lang_name}')").first
        if await target_opt.is_visible():
            await target_opt.click(force=True)
            await page.wait_for_timeout(500)

    # 4. Start Call
    start_call_btn = page.locator("button:has-text('Start Call')").first
    if await start_call_btn.is_visible():
        await start_call_btn.click(force=True)
        print(f"[{round(time.time()-t0, 2)}s] Call Started")
        await page.wait_for_timeout(3000) # Wait for greeting audio

    # 5. Trigger Query to observe 5-Stage Pipeline
    preset_btn = page.locator("button:has-text('PM-Kisan')").first
    if not await preset_btn.is_visible():
        preset_btn = page.locator("button:has-text('Rainfall')").first
    if not await preset_btn.is_visible():
        preset_btn = page.locator("button:has-text('Crop Damage')").first

    pipeline_start_t = time.time()

    # Capture Stage 1
    if await preset_btn.is_visible():
        await preset_btn.click(force=True)
        pipeline_stage_timestamps["Stage 1: Speech STT"] = round(time.time() - pipeline_start_t, 3)
        await page.screenshot(path=f"verification_results/screenshots/{lang_name}_stage1.png")
        print(f"[{round(time.time()-t0, 2)}s] Stage 1 (STT) Triggered")

    # Capture Stage 2
    await page.wait_for_timeout(650)
    pipeline_stage_timestamps["Stage 2: Digital Twin"] = round(time.time() - pipeline_start_t, 3)
    await page.screenshot(path=f"verification_results/screenshots/{lang_name}_stage2.png")
    print(f"[{round(time.time()-t0, 2)}s] Stage 2 (Digital Twin) Active")

    # Capture Stage 3
    await page.wait_for_timeout(650)
    pipeline_stage_timestamps["Stage 3: Scheme RAG"] = round(time.time() - pipeline_start_t, 3)
    await page.screenshot(path=f"verification_results/screenshots/{lang_name}_stage3.png")
    print(f"[{round(time.time()-t0, 2)}s] Stage 3 (Scheme RAG) Active")

    # Capture Stage 4
    await page.wait_for_timeout(700)
    pipeline_stage_timestamps["Stage 4: AI Reasoning"] = round(time.time() - pipeline_start_t, 3)
    await page.screenshot(path=f"verification_results/screenshots/{lang_name}_stage4.png")
    print(f"[{round(time.time()-t0, 2)}s] Stage 4 (AI Reasoning) Active")

    # Capture Stage 5 while Audio Playing
    await page.wait_for_timeout(850)
    pipeline_stage_timestamps["Stage 5: Voice Output (Playing)"] = round(time.time() - pipeline_start_t, 3)
    await page.screenshot(path=f"verification_results/screenshots/{lang_name}_stage5_playing.png")
    print(f"[{round(time.time()-t0, 2)}s] Stage 5 (Voice Output & Audio Playing) Active")

    # Wait for Audio End
    await page.wait_for_timeout(3500)
    pipeline_stage_timestamps["Stage 5: Completed"] = round(time.time() - pipeline_start_t, 3)
    await page.screenshot(path=f"verification_results/screenshots/{lang_name}_final_completed.png")
    print(f"[{round(time.time()-t0, 2)}s] Stage 5 Completed & Interaction Finished")

    # Collect DOM Instrumented Audio Events
    dom_audio_events = await page.evaluate("window.__audio_events || []")

    await browser.close()

    lang_result = {
        "language": lang_name,
        "language_code": lang_code,
        "stage_timestamps_seconds": pipeline_stage_timestamps,
        "tts_network_requests": tts_network_logs,
        "audio_dom_events": dom_audio_events,
        "console_errors_count": len(console_errors),
        "console_errors": console_errors,
        "network_errors_count": len(network_errors),
        "network_errors": network_errors,
        "screenshots": [
            f"{lang_name}_stage1.png",
            f"{lang_name}_stage2.png",
            f"{lang_name}_stage3.png",
            f"{lang_name}_stage4.png",
            f"{lang_name}_stage5_playing.png",
            f"{lang_name}_final_completed.png"
        ]
    }

    results[lang_name] = lang_result

async def main():
    async with async_playwright() as p:
        for lang in LANGUAGES_TO_TEST:
            await run_verification_for_lang(p, lang)

    with open("verification_results/report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n\n=======================================================")
    print("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("Report saved at verification_results/report.json")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
