import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Settings as SettingsIcon, User, Bell, Globe, Shield, Palette, Flag, Key } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings · Kisan Mitra" }] }),
  component: Page,
});

type Section = "profile" | "notifications" | "language" | "appearance" | "security" | "api" | "flags";

const NAV: { key: Section; icon: React.ComponentType<{ className?: string }>; label: string; desc: string }[] = [
  { key: "profile", icon: User, label: "Profile", desc: "Name, role, contact and team assignment." },
  { key: "notifications", icon: Bell, label: "Notifications", desc: "Channels, escalation, quiet hours." },
  { key: "language", icon: Globe, label: "Language & region", desc: "22 Indian languages · IST · units." },
  { key: "appearance", icon: Palette, label: "Appearance", desc: "Theme, density, motion." },
  { key: "security", icon: Shield, label: "Security", desc: "MFA, sessions, audit log." },
  { key: "api", icon: Key, label: "API & webhooks", desc: "Tokens, rate limits, endpoints." },
  { key: "flags", icon: Flag, label: "Feature flags", desc: "Experimental agents & rollouts." },
];

function Page() {
  const [section, setSection] = useState<Section>("profile");

  return (
    <AppShell>
      <PageHeader
        icon={SettingsIcon}
        eyebrow="Preferences"
        title="Settings"
        description="Personalize your workspace, control notifications, and manage security posture."
      />

      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <GlassCard eyebrow="Sections" strong>
          <ul className="space-y-1">
            {NAV.map((n) => {
              const Icon = n.icon;
              const active = section === n.key;
              return (
                <li key={n.key}>
                  <button
                    onClick={() => setSection(n.key)}
                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition ring-1 ring-inset ${active ? "bg-[var(--lime-glow)]/10 text-[var(--lime-glow)] ring-[var(--lime-glow)]/25" : "ring-transparent text-white/70 hover:bg-white/[0.03]"}`}
                  >
                    <Icon className="size-4" />
                    <span className="font-semibold">{n.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </GlassCard>

        <div className="space-y-6">
          {section === "profile" && <ProfileSection />}
          {section === "notifications" && <NotificationsSection />}
          {section === "language" && <LanguageSection />}
          {section === "appearance" && <AppearanceSection />}
          {section === "security" && <SecuritySection />}
          {section === "api" && <ApiSection />}
          {section === "flags" && <FlagsSection />}
        </div>
      </div>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-white/50">{label}</div>
      {children}
    </label>
  );
}
const inputCls = "w-full rounded-xl bg-white/[0.04] px-3 py-2 text-sm text-white outline-none ring-1 ring-inset ring-white/10 focus:ring-[var(--lime-glow)]/40";

function ProfileSection() {
  return (
    <GlassCard title="Profile" eyebrow="Account" strong>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Full name"><input defaultValue="Aditi Deshmukh" className={inputCls} /></Field>
        <Field label="Role"><input defaultValue="Operations Lead" className={inputCls} /></Field>
        <Field label="Email"><input defaultValue="aditi@kisanmitra.gov.in" className={inputCls} /></Field>
        <Field label="Phone"><input defaultValue="+91 98220 44821" className={inputCls} /></Field>
      </div>
    </GlassCard>
  );
}
function NotificationsSection() {
  const rows: [string, boolean][] = [["Critical alerts", true], ["Weather warnings", true], ["Market swings", true], ["Weekly digest", false], ["Product updates", false]];
  return (
    <GlassCard title="Notifications" eyebrow="Channels" strong>
      <ul className="space-y-2">
        {rows.map(([label, on]) => (
          <li key={label} className="flex items-center justify-between rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
            <span className="text-sm">{label}</span>
            <span className={`inline-flex h-5 w-9 rounded-full p-0.5 transition ${on ? "bg-[var(--lime-glow)]/70" : "bg-white/15"}`}>
              <span className={`size-4 rounded-full bg-white transition ${on ? "translate-x-4" : ""}`} />
            </span>
          </li>
        ))}
      </ul>
    </GlassCard>
  );
}
function LanguageSection() {
  return (
    <GlassCard title="Language & region" eyebrow="Locale" strong>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Interface language">
          <select className={inputCls} defaultValue="en-IN">
            {["en-IN","hi-IN","mr-IN","ta-IN","te-IN","kn-IN","bn-IN","pa-IN","gu-IN"].map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </Field>
        <Field label="Timezone"><input defaultValue="Asia/Kolkata (IST)" className={inputCls} /></Field>
        <Field label="Units"><select className={inputCls}><option>Metric · hectares · quintals</option><option>Imperial · acres · tons</option></select></Field>
      </div>
    </GlassCard>
  );
}
function AppearanceSection() {
  return (
    <GlassCard title="Appearance" eyebrow="Theme" strong>
      <div className="text-sm text-white/70">Dark theme is currently enforced across the platform to preserve the mission-control aesthetic.</div>
      <div className="mt-3 flex flex-wrap gap-2">
        <StatusBadge tone="lime" dot>Dark</StatusBadge>
        <StatusBadge tone="muted">Auto</StatusBadge>
        <StatusBadge tone="muted">Light (soon)</StatusBadge>
      </div>
    </GlassCard>
  );
}
function SecuritySection() {
  return (
    <GlassCard title="Security" eyebrow="Session" strong>
      <div className="grid gap-3 sm:grid-cols-2">
        {[
          ["Signed in as", "Aditi Deshmukh · Ops lead"],
          ["Organization", "Kisan Mitra AI · Central"],
          ["Region", "IN · ap-south-1"],
          ["Last sign-in", "Today · 08:12 IST · Mumbai"],
        ].map(([k, v]) => (
          <div key={k} className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
            <div className="text-[10px] text-mono uppercase text-white/40">{k}</div>
            <div className="mt-0.5 text-sm text-white">{v}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <StatusBadge tone="lime" dot>MFA · TOTP</StatusBadge>
        <StatusBadge tone="sky">SSO · Google Workspace</StatusBadge>
        <StatusBadge tone="wheat">Session · 8h idle</StatusBadge>
      </div>
    </GlassCard>
  );
}
function ApiSection() {
  return (
    <GlassCard title="API & webhooks" eyebrow="Developer" strong>
      <div className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
        <div className="text-[10px] text-mono uppercase text-white/40">Base URL</div>
        <div className="mt-1 text-mono text-sm text-[var(--lime-glow)]">https://api.kisanmitra.ai/v1</div>
      </div>
      <div className="mt-3 rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
        <div className="text-[10px] text-mono uppercase text-white/40">Rate limit</div>
        <div className="mt-1 text-sm">1,000 req / min · burst 200</div>
      </div>
    </GlassCard>
  );
}
function FlagsSection() {
  const flags: [string, boolean, string][] = [
    ["voice_ivr_v2", true, "Bhashini bilingual routing"],
    ["disease_vision_multimodal", true, "Fuse text + image evidence"],
    ["market_forecast_ensemble", false, "New ensemble forecaster"],
    ["farmer_360_beta", false, "Unified farmer intelligence drawer"],
  ];
  return (
    <GlassCard title="Feature flags" eyebrow="Experiments" strong>
      <ul className="space-y-2">
        {flags.map(([k, on, desc]) => (
          <li key={k} className="flex items-center justify-between rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
            <div>
              <div className="text-mono text-sm">{k}</div>
              <div className="text-[11px] text-white/50">{desc}</div>
            </div>
            <StatusBadge tone={on ? "lime" : "muted"} dot>{on ? "on" : "off"}</StatusBadge>
          </li>
        ))}
      </ul>
    </GlassCard>
  );
}
