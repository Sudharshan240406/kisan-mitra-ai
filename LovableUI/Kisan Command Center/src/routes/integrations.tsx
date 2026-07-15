import { createFileRoute } from "@tanstack/react-router";
import { Zap } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";

export const Route = createFileRoute("/integrations")({
  head: () => ({ meta: [{ title: "Integrations · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={Zap}
        eyebrow="Ecosystem"
        title="Integrations"
        description="First-party government APIs, DPI stack, and enterprise partner connectors."
      />

      <StatGrid stats={[
        { label: "Live integrations", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "API calls · 24h", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Webhooks", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "SLA breaches · 30d", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={Zap} title="No integrations configured" description="Waiting for backend — connected services will appear here once the connector registry is available." />
    </AppShell>
  );
}
