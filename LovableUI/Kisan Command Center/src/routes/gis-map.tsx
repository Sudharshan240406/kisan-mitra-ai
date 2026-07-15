import { createFileRoute } from "@tanstack/react-router";
import { MapPin, Layers } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { IndiaMap } from "@/components/kisan/IndiaMap";
import { EmptyState } from "@/components/layout/EmptyState";

export const Route = createFileRoute("/gis-map")({
  head: () => ({ meta: [{ title: "GIS Map · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={MapPin}
        eyebrow="Geospatial"
        title="GIS Map"
        description="India-wide overlay of farmers, mandis, weather stations, disease outbreaks, and satellite indices."
      />

      <StatGrid stats={[
        { label: "Data layers", value: DASH, delta: "Waiting for backend", tone: "lime", icon: Layers },
        { label: "Points rendered", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Districts", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Tile cache hit", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <IndiaMap />

      <EmptyState icon={Layers} title="No active layers" description="Waiting for backend — configured overlay layers will appear here once the GIS service publishes them." />
    </AppShell>
  );
}
