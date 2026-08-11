/**
 * Live Production Pipeline Verification
 * Tests: https://frontend-navy-alpha-wikcmhwv2h.vercel.app
 */

import { chromium } from "playwright";
import { writeFileSync } from "fs";
import { mkdirSync } from "fs";

const URL = "https://frontend-navy-alpha-wikcmhwv2h.vercel.app";
const SCREENSHOTS_DIR = "./scripts/live_screenshots";

mkdirSync(SCREENSHOTS_DIR, { recursive: true });

const log = (msg) => {
  const ts = new Date().toISOString().split("T")[1].split(".")[0];
  console.log(`[${ts}] ${msg}`);
};

const errors = [];
const networkFails = [];
const pipelineTimings = {};

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: SCREENSHOTS_DIR },
  });

  const page = await context.newPage();

  // Capture console errors
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push({ type: "error", text: msg.text() });
      log(`CONSOLE ERROR: ${msg.text()}`);
    }
  });

  page.on("pageerror", (err) => {
    errors.push({ type: "pageerror", text: err.message });
    log(`PAGE ERROR: ${err.message}`);
  });

  // Capture network failures
  page.on("response", (response) => {
    if (response.status() >= 400) {
      networkFails.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
      });
      log(`NETWORK FAIL [${response.status()}]: ${response.url()}`);
    }
  });

  try {
    // ── STEP 1: Load Homepage ─────────────────────────────────
    log("STEP 1: Loading homepage...");
    await page.goto(URL, { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/01_homepage.png`, fullPage: false });
    log("✓ Homepage loaded");

    // ── STEP 2: Navigate to Mission Control ──────────────────
    log("STEP 2: Navigating to Mission Control...");
    // Try to find Mission Control in the sidebar
    const missionControlLink = page.locator("text=Mission Control").first();
    if (await missionControlLink.isVisible()) {
      await missionControlLink.click();
      await page.waitForTimeout(1500);
      log("✓ Clicked Mission Control");
    } else {
      log("⚠ Mission Control link not found, trying sidebar nav...");
      // Try sidebar items
      const navItems = await page.locator("nav a, nav button, [role='navigation'] a").all();
      for (const item of navItems) {
        const text = await item.textContent();
        log(`  Found nav item: "${text?.trim()}"`);
      }
    }
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/02_mission_control.png` });

    // ── STEP 3: Find and Open Demo ────────────────────────────
    log("STEP 3: Looking for Demo launch button...");
    const demoButton = page.locator("text=Launch Demo, text=Start Demo, text=Demo Mode, button:has-text('Demo')").first();
    if (await demoButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await demoButton.click();
      await page.waitForTimeout(2000);
      log("✓ Clicked Demo button");
    } else {
      // Try finding the phone icon button
      log("  Trying to find phone/demo trigger...");
      const allButtons = await page.locator("button").all();
      for (const btn of allButtons.slice(0, 20)) {
        const text = await btn.textContent().catch(() => "");
        if (text && (text.toLowerCase().includes("demo") || text.toLowerCase().includes("launch"))) {
          log(`  Found button: "${text.trim()}"`);
          await btn.click();
          await page.waitForTimeout(2000);
          break;
        }
      }
    }
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/03_demo_opened.png` });

    // ── STEP 4: Handle Incoming Call UI ──────────────────────
    log("STEP 4: Looking for incoming call UI...");
    await page.waitForTimeout(1000);

    // Look for the INCOMING CALL display
    const incomingText = page.locator("text=INCOMING FARMER CALL").first();
    const hasIncoming = await incomingText.isVisible({ timeout: 3000 }).catch(() => false);
    log(`  Incoming call visible: ${hasIncoming}`);

    // Try clicking a farmer to trigger incoming call
    const farmerButtons = await page.locator("button").all();
    for (const btn of farmerButtons) {
      const text = await btn.textContent().catch(() => "");
      if (text && text.includes("Karnataka")) {
        log(`  Clicking farmer: "${text.trim()}"`);
        await btn.click();
        await page.waitForTimeout(1500);
        break;
      }
    }
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/04_call_triggered.png` });

    // Accept the call
    log("STEP 4b: Accepting the call...");
    // Phone accept button - green circle with phone icon
    const acceptBtn = page.locator("button[title='Accept Call']").first();
    if (await acceptBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await acceptBtn.click();
      log("✓ Clicked Accept Call button");
    } else {
      // Try to find by SVG or color
      const phoneButtons = page.locator("button").filter({ hasText: /accept|phone/i });
      if (await phoneButtons.count() > 0) {
        await phoneButtons.first().click();
        log("✓ Clicked phone button");
      }
    }
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/05_call_accepted.png` });

    // ── STEP 5: Submit Sample Question ───────────────────────
    log("STEP 5: Submitting a sample question...");
    // Wait for Sample Questions to appear
    await page.waitForTimeout(1000);

    // Find the first sample question button
    let questionClicked = false;
    const sampleQuestionSection = page.locator("text=Sample Questions").first();
    if (await sampleQuestionSection.isVisible({ timeout: 3000 }).catch(() => false)) {
      log("✓ Sample Questions section found");
      // The questions are buttons right after the label
      const questionButtons = await page.locator("button").all();
      for (const btn of questionButtons) {
        const text = await btn.textContent().catch(() => "");
        // Look for any non-control button (not Accept/Reject/End/Mic)
        if (text && text.length > 20 && !text.includes("Restart") && !text.includes("Speak")) {
          log(`  Clicking question: "${text.trim().substring(0, 60)}..."`);
          const questionClickTime = Date.now();
          pipelineTimings.questionClickedAt = questionClickTime;
          await btn.click();
          questionClicked = true;
          break;
        }
      }
    }

    if (!questionClicked) {
      log("⚠ Could not find question button, trying direct click on any visible button");
      await page.screenshot({ path: `${SCREENSHOTS_DIR}/05b_debug_before_question.png` });
    }

    await page.screenshot({ path: `${SCREENSHOTS_DIR}/06_question_submitted.png` });

    // ── STEP 6: Watch Pipeline Stages ────────────────────────
    log("STEP 6: Watching pipeline stages...");
    
    // Monitor pipeline for up to 30 seconds
    const startTime = Date.now();
    let lastActiveStep = 0;
    let stageScreenshots = {};

    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(500);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      // Check for pipeline active step by looking for pulsing elements
      // The active step has "Phase X/5 Active" text
      const phaseText = await page.locator("text=/Phase [1-5]\\/5/").first().textContent().catch(() => "");
      if (phaseText) {
        const match = phaseText.match(/Phase (\d)\/5/);
        const step = match ? parseInt(match[1]) : 0;

        if (step !== lastActiveStep) {
          log(`  Pipeline Step ${step} active at ${elapsed}s`);
          pipelineTimings[`step${step}StartAt`] = elapsed;
          if (lastActiveStep > 0) {
            pipelineTimings[`step${lastActiveStep}Duration`] = elapsed;
          }
          lastActiveStep = step;

          const ssName = `${SCREENSHOTS_DIR}/07_stage${step}_at_${elapsed}s.png`;
          await page.screenshot({ path: ssName });
          stageScreenshots[step] = ssName;
        }
      }

      // Also check for "Phase 5/5 Active • Speaking"
      const speakingText = await page.locator("text=Speaking").first().textContent().catch(() => "");
      if (speakingText && !stageScreenshots["5_speaking"]) {
        log(`  Stage 5 SPEAKING active at ${elapsed}s`);
        await page.screenshot({ path: `${SCREENSHOTS_DIR}/08_stage5_speaking_${elapsed}s.png` });
        stageScreenshots["5_speaking"] = elapsed;
      }

      // Check if pipeline is done (no active phase text, or "Standby")
      const standbyText = await page.locator("text=Standby").first().textContent().catch(() => "");
      if (standbyText && lastActiveStep === 5) {
        log(`  Pipeline complete at ${elapsed}s`);
        pipelineTimings.pipelineCompleteAt = elapsed;
        await page.screenshot({ path: `${SCREENSHOTS_DIR}/09_pipeline_complete.png` });
        break;
      }
    }

    // ── STEP 7: Check Voice Engine Banner ────────────────────
    log("STEP 7: Checking Voice Engine banner...");
    const voiceEngineSection = page.locator("text=Voice Engine").first();
    const voiceEngineBannerText = await page.evaluate(() => {
      const els = document.querySelectorAll("*");
      for (const el of els) {
        if (el.textContent?.includes("Voice Engine:") && el.children.length > 0) {
          return el.textContent?.trim();
        }
      }
      return null;
    });
    log(`  Voice Engine banner text: "${voiceEngineBannerText}"`);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/10_voice_banner.png` });

    // ── STEP 8: Switch to Hindi ──────────────────────────────
    log("STEP 8: Switching language to Hindi...");
    // Find the language selector dropdown
    const langSelector = page.locator("button:has-text('English'), button:has-text('Kannada'), button:has-text('Hindi')").first();
    if (await langSelector.isVisible({ timeout: 3000 }).catch(() => false)) {
      await langSelector.click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: `${SCREENSHOTS_DIR}/11_lang_dropdown.png` });
      
      // Click Hindi option
      const hindiOption = page.locator("text=Hindi").first();
      if (await hindiOption.isVisible({ timeout: 2000 }).catch(() => false)) {
        await hindiOption.click();
        await page.waitForTimeout(1000);
        log("✓ Switched to Hindi");
        await page.screenshot({ path: `${SCREENSHOTS_DIR}/12_hindi_selected.png` });
        
        // Check voice banner
        const hindiBannerText = await page.evaluate(() => {
          const els = document.querySelectorAll("*");
          for (const el of els) {
            if (el.textContent?.includes("Voice Engine:") && el.children.length > 0) {
              return el.textContent?.trim();
            }
          }
          return null;
        });
        log(`  Hindi Voice Engine banner: "${hindiBannerText}"`);
        await page.screenshot({ path: `${SCREENSHOTS_DIR}/13_hindi_voice_banner.png` });
      }
    }

    // ── STEP 9: Final Screenshot ─────────────────────────────
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/14_final_state.png`, fullPage: true });

  } catch (err) {
    log(`ERROR: ${err.message}`);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/error_state.png` });
  } finally {
    // ── REPORT ───────────────────────────────────────────────
    const report = {
      timestamp: new Date().toISOString(),
      url: URL,
      pipelineTimings,
      consoleErrors: errors,
      networkFailures: networkFails,
      voiceEngineBannerCapture: "See screenshots",
    };

    writeFileSync(`${SCREENSHOTS_DIR}/report.json`, JSON.stringify(report, null, 2));

    console.log("\n");
    console.log("═══════════════════════════════════════");
    console.log("  LIVE PRODUCTION TEST REPORT");
    console.log("═══════════════════════════════════════");
    console.log("\nPIPELINE TIMINGS:");
    console.log(JSON.stringify(pipelineTimings, null, 2));
    console.log("\nCONSOLE ERRORS:", errors.length);
    errors.forEach((e) => console.log("  -", e.text));
    console.log("\nNETWORK FAILURES:", networkFails.length);
    networkFails.forEach((n) => console.log(`  - [${n.status}] ${n.url}`));
    console.log("\nReport saved to:", `${SCREENSHOTS_DIR}/report.json`);
    console.log("Screenshots saved to:", SCREENSHOTS_DIR);

    await context.close();
    await browser.close();
  }
})();
