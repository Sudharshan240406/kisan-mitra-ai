/**
 * Final UX Verification — Captures every pipeline stage screenshot
 * after the premium animation polish.
 */
import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "fs";

const URL = "https://frontend-navy-alpha-wikcmhwv2h.vercel.app";
const SS = "./scripts/live_ss4";
mkdirSync(SS, { recursive: true });

const ts = () => new Date().toISOString().split("T")[1].slice(0, 8);
const log = (msg) => console.log(`[${ts()}] ${msg}`);

const errors = [];
const netFails = [];
const timings = {};

(async () => {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();

  page.on("console", m => { if (m.type() === "error") errors.push(m.text().slice(0, 200)); });
  page.on("response", r => { if (r.status() >= 400) netFails.push({ url: r.url(), status: r.status() }); });

  try {
    log("→ Loading page");
    await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: `${SS}/01_home.png` });

    log("→ Mission Control");
    await page.locator("text=Mission Control").first().click();
    await page.waitForTimeout(1500);

    log("→ Launch Phone Demo");
    await page.locator("text=Launch Phone Demo").first().click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${SS}/02_demo_open.png` });

    log("→ Trigger call — Priya Kumari");
    await page.locator("button").filter({ hasText: "Priya Kumari" }).first().click();
    await page.waitForTimeout(1200);
    await page.screenshot({ path: `${SS}/03_incoming.png` });

    log("→ Accept call");
    await page.locator("button[title='Accept Call']").first().click();
    await page.waitForTimeout(3500);
    await page.screenshot({ path: `${SS}/04_connected.png` });

    log("→ Clicking first Kannada question via evaluate");
    const clicked = await page.evaluate(() => {
      const btns = [...document.querySelectorAll("button")];
      for (const btn of btns) {
        const txt = btn.textContent?.trim() || "";
        if (/^[\u0C80-\u0CFF\u0900-\u097F]/.test(txt) && !btn.disabled) {
          btn.click();
          return txt.slice(0, 60);
        }
      }
      return null;
    });
    log(`  Question: ${clicked}`);

    timings.questionStart = Date.now();
    await page.screenshot({ path: `${SS}/05_question_clicked.png` });

    // ── Monitor every 300ms for finer stage capture ──────────────
    log("→ Monitoring pipeline with 300ms interval (60s max)");
    let lastStep = 0;
    const stageTimes = {};
    const TOTAL_TICKS = 200; // 60 seconds

    for (let tick = 0; tick < TOTAL_TICKS; tick++) {
      await page.waitForTimeout(300);
      const elapsed = ((Date.now() - timings.questionStart) / 1000).toFixed(2);

      const phaseText = await page.evaluate(() => {
        for (const el of document.querySelectorAll("span, div")) {
          const t = el.textContent?.trim() || "";
          if (/Phase \d\/5/.test(t) && t.length < 40) return t;
        }
        return "";
      });

      if (phaseText) {
        const m = phaseText.match(/Phase (\d)\/5/);
        const step = m ? parseInt(m[1]) : 0;
        if (step && step !== lastStep) {
          stageTimes[step] = elapsed;
          timings[`stage${step}At`] = elapsed;
          log(`  ★ Stage ${step} at ${elapsed}s — "${phaseText}"`);
          await page.screenshot({ path: `${SS}/stage_${step}_at_${elapsed}s.png` });
          lastStep = step;
        }
        if (phaseText.includes("Speaking") && !timings.speakingAt) {
          timings.speakingAt = elapsed;
          log(`  🔊 SPEAKING at ${elapsed}s`);
          await page.screenshot({ path: `${SS}/speaking_${elapsed}s.png` });
        }
      }

      const done = await page.evaluate(() => {
        for (const el of document.querySelectorAll("span, div")) {
          if (el.textContent?.trim() === "Standby") return true;
        }
        return false;
      });
      if (done && lastStep >= 4) {
        timings.pipelineDone = ((Date.now() - timings.questionStart) / 1000).toFixed(2);
        log(`  ✓ Pipeline DONE at ${timings.pipelineDone}s`);
        await page.screenshot({ path: `${SS}/done_${timings.pipelineDone}s.png` });
        break;
      }
    }

    await page.screenshot({ path: `${SS}/06_after.png` });

    // Voice engine banner
    const voiceBanner = await page.evaluate(() => {
      for (const el of document.querySelectorAll("div")) {
        const t = el.textContent?.trim() || "";
        if (t.startsWith("Voice Engine:") && t.length < 80) return t;
      }
      return "NOT_FOUND";
    });
    log(`Voice banner: "${voiceBanner}"`);
    timings.voiceBanner = voiceBanner;
    await page.screenshot({ path: `${SS}/07_voice_banner.png` });

    // Change to Hindi
    log("→ Switching to Hindi");
    await page.locator("button").filter({ hasText: /English|Kannada|Hindi|Telugu/ }).first().click();
    await page.waitForTimeout(500);
    await page.locator("text=Hindi").first().click().catch(() => {});
    await page.waitForTimeout(800);
    const hindiBanner = await page.evaluate(() => {
      for (const el of document.querySelectorAll("div")) {
        const t = el.textContent?.trim() || "";
        if (t.startsWith("Voice Engine:") && t.length < 80) return t;
      }
      return "NOT_FOUND";
    });
    timings.hindiBanner = hindiBanner;
    log(`Hindi banner: "${hindiBanner}"`);
    await page.screenshot({ path: `${SS}/08_hindi_banner.png` });

    await page.screenshot({ path: `${SS}/09_final.png`, fullPage: true });

  } catch (err) {
    log(`ERROR: ${err.message}`);
    await page.screenshot({ path: `${SS}/error.png` }).catch(() => {});
  }

  // ── FINAL REPORT ────────────────────────────────────────────────
  console.log("\n═══════════════════════════════════════════════════");
  console.log("   FINAL UX VERIFICATION REPORT (POST-POLISH)");
  console.log("═══════════════════════════════════════════════════");
  console.log("\n📊 STAGE TIMINGS:");
  ["stage1At", "stage2At", "stage3At", "stage4At", "stage5At", "speakingAt", "pipelineDone"].forEach(k => {
    if (timings[k]) console.log(`   ${k}: ${timings[k]}s`);
  });

  // Stage durations
  if (timings.stage1At && timings.stage2At) {
    console.log(`\n⏱  STAGE HOLD TIMES (measured):`);
    const s = [1,2,3,4,5].map(n => parseFloat(timings[`stage${n}At`] || "0"));
    if (s[0]) console.log(`   Stage 1 (STT):      ${s[0].toFixed(2)}s start`);
    if (s[0] && s[1]) console.log(`   Stage 1 duration:   ${(s[1]-s[0]).toFixed(2)}s`);
    if (s[1] && s[2]) console.log(`   Stage 2 duration:   ${(s[2]-s[1]).toFixed(2)}s`);
    if (s[2] && s[3]) console.log(`   Stage 3 duration:   ${(s[3]-s[2]).toFixed(2)}s`);
    if (s[3] && s[4]) console.log(`   Stage 4 duration:   ${(s[4]-s[3]).toFixed(2)}s`);
    if (s[4] && timings.pipelineDone) console.log(`   Stage 5 duration:   ${(parseFloat(timings.pipelineDone)-s[4]).toFixed(2)}s`);
  }

  console.log(`\n📢 VOICE BANNER (Kannada): "${timings.voiceBanner}"`);
  console.log(`📢 VOICE BANNER (Hindi):   "${timings.hindiBanner}"`);
  const bannerOk = (timings.hindiBanner || "").includes("Hindi");
  console.log(`   Banner update: ${bannerOk ? "✅ PASS" : "❌ FAIL"}`);

  console.log(`\n🔴 CONSOLE ERRORS: ${errors.length} ${errors.length ? errors.join("; ") : "✅ NONE"}`);
  console.log(`🔴 NETWORK FAILS:  ${netFails.length} ${netFails.length === 0 ? "✅ NONE" : ""}`);
  netFails.slice(0, 10).forEach(n => console.log(`   [${n.status}] ${n.url.slice(0, 80)}`));

  writeFileSync(`${SS}/report.json`, JSON.stringify({ timings, errors, netFails }, null, 2));
  log(`✓ Saved: ${SS}/report.json`);

  await ctx.close();
  await browser.close();
})();
