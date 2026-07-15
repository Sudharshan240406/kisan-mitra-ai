import { createFileRoute } from "@tanstack/react-router";
import { FileText, Download } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";
import { ActionButton } from "@/components/layout/ActionButton";

export const Route = createFileRoute("/reports")({
  head: () => ({ meta: [{ title: "Reports · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={FileText}
        eyebrow="Compliance · Impact · Board"
        title="Reports"
        description="Regulator-ready reports, board packs, and scheduled exports for ministries and enterprise partners."
        actions={<ActionButton icon={Download} variant="primary">Export all</ActionButton>}
      />

      <StatGrid stats={[
        { label: "Reports generated", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Scheduled", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Subscribers", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Storage", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={FileText} title="No reports available" description="Waiting for backend — the report library and export history will appear here." />
    </AppShell>
  );
}
