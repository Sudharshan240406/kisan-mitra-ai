import { createFileRoute } from "@tanstack/react-router";
import { Satellite } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";

export const Route = createFileRoute("/satellite")({
  head: () => ({ meta: [{ title: "Satellite Monitoring · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={Satellite}
        eyebrow="Sentinel · Landsat · SMAP · CartoSat"
        title="Satellite Monitoring"
        description="Multi-mission remote sensing pipeline computing NDVI, EVI, LSWI, and soil moisture at plot resolution."
      />

      <StatGrid stats={[
        { label: "Missions", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Scenes / day", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Plots monitored", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Storage", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={Satellite} title="No satellite data" description="Waiting for backend — upcoming passes and vegetation indices will appear here once the ingest pipeline is connected." />
    </AppShell>
  );
}
