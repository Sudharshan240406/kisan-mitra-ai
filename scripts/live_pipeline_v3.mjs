/**
 * Live Pipeline Test v3 — Direct index-based question click
 */
import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "fs";

const URL = "https://frontend-navy-alpha-wikcmhwv2h.vercel.app";
const SS = "./scripts/live_ss3";
mkdirSync(SS, { recursive: true });

const ts = () => new Date().toISOString().split("T")[1].slice(0, 8);
const log = (msg) => console.log(`[${ts()}] ${msg}`);

const errors = [];
const netFails = [];
const timings = {};

(async () => {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  page.on("console", m => { if (m.type() === "error") { errors.push(m.text().slice(0, 200)); } });
  page.on("response", r => { if (r.status() >= 400) netFails.push({ url: r.url(), status: r.status() }); });

  try {
    // Load
    log("Loading page...");
    await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: `${SS}/01_home.png` });

    // Mission Control
    log("Mission Control...");
    await page.locator("text=Mission Control").first().click();
    await page.waitForTimeout(1500);

    // Launch Demo
    log("Launch Phone Demo...");
    await page.locator("text=Launch Phone Demo").first().click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${SS}/02_demo_open.png` });

    // Trigger call via Priya Kumari (first farmer tab)
    log("Clicking Priya Kumari farmer tab...");
    await page.locator("button").filter({ hasText: "Priya Kumari" }).first().click();
    await page.waitForTimeout(1200);
    
    // Accept call
    log("Accepting call...");
    await page.locator("button[title='Accept Call']").first().click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: `${SS}/03_connected.png` });
    log("✓ Call connected. Greeting should be playing...");

    // Wait for TTS greeting to finish (up to 15s)
    log("Waiting for greeting to finish...");
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(500);
      const isProcessing = await page.locator("text=/processing|speaking/i").count().catch(() => 0);
      if (!isProcessing) break;
    }
    log("✓ Greeting done");
    await page.screenshot({ path: `${SS}/04_post_greeting.png` });

    // Now click a real question button using evaluate to get it precisely
    log("Clicking a real sample question using evaluate...");
    const clickResult = await page.evaluate(() => {
      const buttons = [...document.querySelectorAll("button")];
      // Find buttons that contain Indian language text (Kannada/Hindi/etc)
      // These are the preset question buttons
      for (const btn of buttons) {
        const txt = btn.textContent?.trim() || "";
        // Kannada questions start with ಮ, ಪ, ಬ, ಗ, ಹ etc.
        // Must be > 20 chars and not a farmer name / control button
        const isKannadaChar = /^[\u0C80-\u0CFF]/.test(txt);
        const isHindiChar = /^[\u0900-\u097F]/.test(txt);
        const isEnglishQuestion = txt.length > 30 && txt.includes("?") && !txt.includes("(");
        if ((isKannadaChar || isHindiChar || isEnglishQuestion) && !btn.disabled) {
          console.log("CLICK_TARGET:", txt.slice(0, 80));
          btn.click();
          return { clicked: true, text: txt.slice(0, 80) };
        }
      }
      return { clicked: false, text: "no question found" };
    });
    log(`Question click result: ${JSON.stringify(clickResult)}`);
    
    timings.questionStartMs = Date.now();
    timings.questionClickedAt = ts();
    await page.screenshot({ path: `${SS}/05_q_clicked.png` });

    // Monitor pipeline for 45 seconds
    log("Monitoring pipeline for 45 seconds...");
    let lastStep = 0;
    const MONITOR_DURATION = 90; // 45 seconds

    for (let tick = 0; tick < MONITOR_DURATION; tick++) {
      await page.waitForTimeout(500);
      const elapsedMs = Date.now() - timings.questionStartMs;
      const elapsedS = (elapsedMs / 1000).toFixed(2);

      // Get pipeline phase text from DOM
      const phaseInfo = await page.evaluate(() => {
        const allText = [...document.querySelectorAll("span, div, p")].map(el => el.textContent?.trim()).filter(Boolean);
        for (const txt of allText) {
          if (txt && txt.match(/Phase \d\/5/)) return txt;
          if (txt && txt.includes("Speaking")) return txt;
          if (txt && txt === "Standby") return txt;
        }
        return "";
      });

      if (phaseInfo) {
        const stepMatch = phaseInfo.match(/Phase (\d)\/5/);
        const step = stepMatch ? parseInt(stepMatch[1]) : 0;
        
        if (step && step !== lastStep) {
          timings[`stage${step}StartAt`] = elapsedS;
          log(`  ★ Stage ${step} active at ${elapsedS}s — "${phaseInfo}"`);
          await page.screenshot({ path: `${SS}/stage_${step}_at_${elapsedS}s.png` });
          lastStep = step;
        }

        if (phaseInfo.includes("Speaking") && !timings.speakingConfirmed) {
          timings.speakingConfirmed = elapsedS;
          log(`  🔊 SPEAKING confirmed at ${elapsedS}s`);
          await page.screenshot({ path: `${SS}/speaking_${elapsedS}s.png` });
        }

        if (phaseInfo === "Standby" && lastStep > 0) {
          timings.pipelineDoneAt = elapsedS;
          log(`  ✓ Pipeline DONE at ${elapsedS}s`);
          await page.screenshot({ path: `${SS}/done_${elapsedS}s.png` });
          break;
        }
      }
    }

    await page.screenshot({ path: `${SS}/06_after_pipeline.png` });

    // Check voice banner
    log("Checking voice engine banner...");
    const voiceBannerText = await page.evaluate(() => {
      // Find the "Voice Engine:" row
      const allDivs = [...document.querySelectorAll("div")];
      for (const d of allDivs) {
        const txt = d.textContent?.trim() || "";
        if (txt.includes("Voice Engine:") && txt.length < 300) {
          return txt;
        }
      }
      return "NOT_FOUND";
    });
    log(`Voice Engine Banner: "${voiceBannerText}"`);
    timings.voiceBannerText = voiceBannerText;
    await page.screenshot({ path: `${SS}/07_voice_banner.png` });

    // Change to Hindi
    log("Changing to Hindi...");
    // Language selector is a button with current language text
    const langBtnText = await page.locator("button").filter({ hasText: /English|Kannada|Hindi|Telugu/ }).first().textContent();
    log(`  Current language button: "${langBtnText?.trim()}"`);
    await page.locator("button").filter({ hasText: /English|Kannada|Hindi|Telugu/ }).first().click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SS}/08_lang_dropdown.png` });
    
    const hindiBtn = page.locator("button").filter({ hasText: /^.*Hindi/ }).first();
    if (await hindiBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await hindiBtn.click();
      await page.waitForTimeout(1000);
      log("✓ Switched to Hindi");
    } else {
      // Try clicking any visible "Hindi" text
      await page.locator("text=Hindi").first().click().catch(() => log("⚠ Could not click Hindi"));
      await page.waitForTimeout(1000);
    }
    await page.screenshot({ path: `${SS}/09_hindi_selected.png` });

    const hindiBannerText = await page.evaluate(() => {
      const allDivs = [...document.querySelectorAll("div")];
      for (const d of allDivs) {
        const txt = d.textContent?.trim() || "";
        if (txt.includes("Voice Engine:") && txt.length < 300) return txt;
      }
      return "NOT_FOUND";
    });
    log(`Hindi Voice Banner: "${hindiBannerText}"`);
    timings.hindiBannerText = hindiBannerText;
    await page.screenshot({ path: `${SS}/10_hindi_voice_banner.png` });

    // Final screenshot
    await page.screenshot({ path: `${SS}/11_final.png`, fullPage: true });

  } catch (err) {
    log(`ERROR: ${err.message}\n${err.stack?.split("\n").slice(0, 3).join("\n")}`);
    await page.screenshot({ path: `${SS}/error.png` }).catch(() => {});
  }

  // REPORT
  console.log("\n");
  console.log("═══════════════════════════════════════════════");
  console.log("       LIVE PRODUCTION PIPELINE REPORT v3");
  console.log("═══════════════════════════════════════════════");
  console.log("\n📊 PIPELINE TIMINGS:");
  Object.entries(timings).forEach(([k, v]) => console.log(`   ${k}: ${v}`));
  console.log(`\n🔴 CONSOLE ERRORS (${errors.length} total):`);
  if (errors.length) errors.forEach(e => console.log(`   - ${e}`));
  else console.log("   NONE ✓");
  console.log(`\n🔴 NETWORK FAILURES (${netFails.length} total):`);
  if (netFails.length) netFails.forEach(n => console.log(`   [${n.status}] ${n.url}`));
  else console.log("   NONE ✓");

  // Voice Engine Bug Analysis
  const vb = timings.voiceBannerText || "";
  const hb = timings.hindiBannerText || "";
  console.log("\n📢 VOICE ENGINE ANALYSIS:");
  console.log(`   Default language banner: "${vb}"`);
  console.log(`   Hindi banner:            "${hb}"`);
  if (hb.includes("Hindi")) {
    console.log("   ✅ Voice banner correctly shows Hindi after language change");
  } else if (hb.includes("Kannada")) {
    console.log("   ❌ BUG: Voice banner still shows Kannada after switching to Hindi");
  }

  // Pipeline speed check
  const s1 = parseFloat(timings.stage1StartAt || "0");
  const s5 = parseFloat(timings.stage5StartAt || "0");
  if (s1 > 0 && s5 > 0) {
    const totalTime = s5 - s1;
    console.log(`\n⏱  PIPELINE TOTAL TIME: ${totalTime.toFixed(2)}s (Stage 1→5)`);
    if (totalTime < 1) {
      console.log("   ❌ BUG: Pipeline ran too fast (< 1 second for all stages!)");
    } else {
      console.log("   ✅ Pipeline timing looks reasonable");
    }
  }

  writeFileSync(`${SS}/report.json`, JSON.stringify({ timings, errors, netFails }, null, 2));
  log(`✓ Report saved: ${SS}/report.json`);

  await ctx.close();
  await browser.close();
})();
