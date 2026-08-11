/**
 * Live Production Pipeline Verification v2
 * Tests: https://frontend-navy-alpha-wikcmhwv2h.vercel.app
 */

import { chromium } from "playwright";
import { writeFileSync } from "fs";
import { mkdirSync } from "fs";

const URL = "https://frontend-navy-alpha-wikcmhwv2h.vercel.app";
const SS = "./scripts/live_ss";

mkdirSync(SS, { recursive: true });

const ts = () => new Date().toISOString().split("T")[1].slice(0, 8);
const log = (msg) => console.log(`[${ts()}] ${msg}`);

const errors = [];
const netFails = [];
const timings = {};

(async () => {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  page.on("console", (m) => { if (m.type() === "error") { errors.push(m.text()); log(`❌ CONSOLE: ${m.text().slice(0, 120)}`); } });
  page.on("pageerror", (e) => { errors.push(e.message); log(`❌ PAGEERROR: ${e.message}`); });
  page.on("response", (r) => { if (r.status() >= 400) { netFails.push({ url: r.url(), status: r.status() }); log(`❌ HTTP ${r.status()}: ${r.url().slice(0, 100)}`); } });

  try {
    // STEP 1: Load
    log("→ Loading https://frontend-navy-alpha-wikcmhwv2h.vercel.app");
    await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: `${SS}/01_home.png` });
    log("✓ Page loaded");

    // STEP 2: Mission Control
    log("→ Clicking Mission Control");
    await page.locator("text=Mission Control").first().click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `${SS}/02_mc.png` });

    // STEP 3: Launch Demo
    log("→ Launching Phone Demo");
    await page.locator("text=Launch Phone Demo").first().click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SS}/03_demo.png` });

    // STEP 4: Trigger + Accept call
    log("→ Triggering incoming call (clicking Priya Kumari)");
    // Click farmer tab to trigger incoming call
    await page.locator("button").filter({ hasText: /Priya|Ramesh|Sunita|Anji/ }).first().click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: `${SS}/04_incoming.png` });

    // Accept call
    log("→ Accepting call");
    const acceptBtn = page.locator("button[title='Accept Call']").first();
    if (await acceptBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await acceptBtn.click();
    } else {
      // Alternative: find green phone button
      await page.locator("button").filter({ hasText: "" }).nth(0).click();
    }
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${SS}/05_connected.png` });
    log("✓ Call accepted");

    // STEP 5: Click a REAL sample question (not farmer tab)
    // The question buttons appear AFTER the call is connected inside the questions section
    // They are longer text buttons in the Sample Questions area
    log("→ Looking for sample question buttons...");
    await page.waitForTimeout(1000);
    
    // Dump all button texts for debugging
    const allBtns = await page.locator("button").all();
    log(`  Total buttons on page: ${allBtns.length}`);
    for (let i = 0; i < allBtns.length; i++) {
      const txt = await allBtns[i].textContent().catch(() => "");
      if (txt && txt.trim().length > 15) {
        log(`  btn[${i}]: "${txt.trim().slice(0, 80)}"`);
      }
    }

    // Find a question: must be long text, NOT a farmer name, NOT Restart/Speak/Mute/End
    const SKIP = ["Priya", "Ramesh", "Sunita", "Anji", "Restart", "Speak", "Mute", "Listening", "Accept", "Reject", "End", "Launch", "Mission"];
    let questionText = "";
    let questionIdx = -1;
    for (let i = 0; i < allBtns.length; i++) {
      const txt = (await allBtns[i].textContent().catch(() => "")).trim();
      const isControl = SKIP.some(s => txt.includes(s));
      if (!isControl && txt.length > 25 && txt.length < 300) {
        log(`  ✓ Found question at btn[${i}]: "${txt.slice(0, 80)}"`);
        questionText = txt;
        questionIdx = i;
        break;
      }
    }

    if (questionIdx >= 0) {
      timings.questionAt = ts();
      timings.questionStartMs = Date.now();
      log(`→ Clicking question: "${questionText.slice(0, 60)}"`);
      await allBtns[questionIdx].click();
      await page.screenshot({ path: `${SS}/06_q_clicked.png` });
    } else {
      log("⚠ No question button found! Will still monitor pipeline...");
      await page.screenshot({ path: `${SS}/06_no_q.png` });
    }

    // STEP 6: Monitor pipeline stages for 40 seconds
    log("→ Monitoring pipeline stages...");
    let lastStep = 0;
    const stageStart = {};

    for (let tick = 0; tick < 80; tick++) {
      await page.waitForTimeout(500);
      const elapsedMs = Date.now() - (timings.questionStartMs || Date.now());
      const elapsedS = (elapsedMs / 1000).toFixed(2);

      // Get pipeline header text
      const header = await page.evaluate(() => {
        const spans = document.querySelectorAll("span");
        for (const sp of spans) {
          if (sp.textContent?.includes("Phase") && sp.textContent?.includes("/5")) {
            return sp.textContent.trim();
          }
        }
        return "";
      });

      if (header) {
        const m = header.match(/Phase (\d)\/5/);
        const step = m ? parseInt(m[1]) : 0;

        if (step && step !== lastStep) {
          log(`  ★ Stage ${step} ACTIVE at ${elapsedS}s — "${header}"`);
          stageStart[step] = elapsedS;
          timings[`stage${step}At`] = elapsedS;
          await page.screenshot({ path: `${SS}/07_stage${step}_${elapsedS}s.png` });
          lastStep = step;
        }
      }

      // Also watch for Speaking label
      const isSpeaking = await page.locator("text=Speaking").count().catch(() => 0);
      if (isSpeaking > 0 && !timings.speakingAt) {
        timings.speakingAt = elapsedS;
        log(`  🔊 Voice SPEAKING detected at ${elapsedS}s`);
      }

      // Watch for completion
      const isStandby = await page.locator("text=Standby").count().catch(() => 0);
      if (isStandby > 0 && lastStep >= 4) {
        timings.pipelineDoneAt = elapsedS;
        log(`  ✓ Pipeline COMPLETE at ${elapsedS}s`);
        await page.screenshot({ path: `${SS}/08_done_${elapsedS}s.png` });
        break;
      }
    }

    // STEP 7: Voice engine banner
    log("→ Capturing voice engine status...");
    const voiceBanner = await page.evaluate(() => {
      const els = [...document.querySelectorAll("*")];
      for (const el of els) {
        if (el.children.length === 0 && el.textContent?.includes("Cloud Neural Voice")) {
          return el.textContent.trim();
        }
        if (el.children.length === 0 && el.textContent?.includes("Native Browser Voice")) {
          return el.textContent.trim();
        }
      }
      // Broader search
      const spans = [...document.querySelectorAll("span, div, p")];
      for (const sp of spans) {
        if (sp.textContent?.toLowerCase().includes("voice engine")) {
          return sp.closest("div")?.textContent?.trim().slice(0, 200) || sp.textContent?.trim();
        }
      }
      return "NOT FOUND";
    });
    log(`  Voice Engine Banner: "${voiceBanner}"`);
    timings.voiceBannerEnglish = voiceBanner;
    await page.screenshot({ path: `${SS}/09_voice_banner.png` });

    // STEP 8: Switch to Hindi
    log("→ Switching to Hindi...");
    const langBtn = page.locator("button").filter({ hasText: /English|Kannada|Hindi/ }).first();
    if (await langBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await langBtn.click();
      await page.waitForTimeout(600);
      await page.screenshot({ path: `${SS}/10_lang_open.png` });
      await page.locator("text=Hindi").first().click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: `${SS}/11_hindi.png` });
      
      const hindiBanner = await page.evaluate(() => {
        const spans = [...document.querySelectorAll("span, div, p")];
        for (const sp of spans) {
          if (sp.textContent?.toLowerCase().includes("voice engine")) {
            return sp.closest("div")?.textContent?.trim().slice(0, 200) || sp.textContent?.trim();
          }
        }
        return "NOT FOUND";
      });
      timings.voiceBannerHindi = hindiBanner;
      log(`  Hindi Voice Engine Banner: "${hindiBanner}"`);
    }

    await page.screenshot({ path: `${SS}/12_final.png`, fullPage: true });

  } catch (err) {
    log(`SCRIPT ERROR: ${err.message}`);
    await page.screenshot({ path: `${SS}/error.png` }).catch(() => {});
  }

  // FINAL REPORT
  console.log("\n════════════════════════════════════════");
  console.log("     LIVE PRODUCTION PIPELINE REPORT");
  console.log("════════════════════════════════════════");
  console.log("\n📊 TIMINGS:");
  console.log(JSON.stringify(timings, null, 2));
  console.log("\n🔴 CONSOLE ERRORS:", errors.length, errors.length ? errors : "NONE");
  console.log("\n🔴 NETWORK FAILURES:", netFails.length);
  netFails.forEach(n => console.log(`  [${n.status}] ${n.url}`));

  writeFileSync(`${SS}/report.json`, JSON.stringify({ timings, errors, netFails }, null, 2));
  log("✓ Report saved to scripts/live_ss/report.json");

  await context.close();
  await browser.close();
})();
