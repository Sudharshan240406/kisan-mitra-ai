import { createFileRoute } from "@tanstack/react-router";
import { MessageCircle, Send } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";
import { ActionButton } from "@/components/layout/ActionButton";

export const Route = createFileRoute("/sms")({
  head: () => ({ meta: [{ title: "SMS Center · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={MessageCircle}
        eyebrow="Broadcast"
        title="SMS Center"
        description="Vernacular SMS gateway with DLT compliance, template library, and per-district targeting."
        actions={<ActionButton icon={Send} variant="primary">New campaign</ActionButton>}
      />

      <StatGrid stats={[
        { label: "Sent · 24h", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Delivery rate", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Approved templates", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Cost · 24h", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={MessageCircle} title="No campaigns" description="Waiting for backend — active and scheduled SMS campaigns will appear here." />
    </AppShell>
  );
}
