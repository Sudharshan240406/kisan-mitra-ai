import { createFileRoute } from "@tanstack/react-router";
import { Shield } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";

export const Route = createFileRoute("/governance")({
  head: () => ({ meta: [{ title: "Governance · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={Shield}
        eyebrow="Trust · Safety · Compliance"
        title="Governance"
        description="AI governance program covering data protection, model risk, ethics, and regulatory obligations."
      />

      <StatGrid stats={[
        { label: "Audit score", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Consent coverage", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Model reviews", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Incidents", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={Shield} title="No governance controls loaded" description="Waiting for backend — control framework, audit posture, and incident logs will appear here." />
    </AppShell>
  );
}
