import { createFileRoute } from "@tanstack/react-router";
import { FlaskConical } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";

export const Route = createFileRoute("/soil")({
  head: () => ({ meta: [{ title: "Soil Health · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={FlaskConical}
        eyebrow="Sensor · SHC · Labs"
        title="Soil Health"
        description="Aggregated soil intelligence from IoT probes, Soil Health Cards, and partner labs."
      />

      <StatGrid stats={[
        { label: "Samples · 30d", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "IoT probes", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Districts covered", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Advisories issued", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={FlaskConical} title="No soil data" description="Waiting for backend — nutrient profiles and AI advisories will appear here once samples stream in." />
    </AppShell>
  );
}
