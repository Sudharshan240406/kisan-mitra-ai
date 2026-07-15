import { createFileRoute } from "@tanstack/react-router";
import { Sprout } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";

export const Route = createFileRoute("/crops")({
  head: () => ({ meta: [{ title: "Crop Management · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={Sprout}
        eyebrow="Crop calendar"
        title="Crop Management"
        description="Season-wide crop tracking with growth-stage advisories, input schedules, and yield forecasts."
      />

      <StatGrid stats={[
        { label: "Crops tracked", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Total area", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Advisories sent", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Predicted yield", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={Sprout} title="No crop data" description="Waiting for backend — crop portfolio, growth stages, and yield forecasts will appear here once the ingest pipeline is connected." />
    </AppShell>
  );
}
