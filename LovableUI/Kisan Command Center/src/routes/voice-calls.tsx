import { createFileRoute } from "@tanstack/react-router";
import { Phone, PhoneIncoming, PhoneMissed } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";

export const Route = createFileRoute("/voice-calls")({
  head: () => ({ meta: [{ title: "Voice Calls (IVR) · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={Phone}
        eyebrow="IVR · Multilingual"
        title="Voice Calls"
        description="Multilingual voice AI helpline, outbound campaigns, and human escalation."
      />

      <StatGrid stats={[
        { label: "Calls · today", value: DASH, delta: "Waiting for backend", icon: PhoneIncoming, tone: "lime" },
        { label: "Avg duration", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Resolution", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Missed", value: DASH, delta: "Waiting for backend", icon: PhoneMissed, tone: "leaf" },
      ]} />

      <EmptyState icon={Phone} title="No active IVR session" description="Waiting for backend — live call log and outbound campaign progress will appear here." />
    </AppShell>
  );
}
