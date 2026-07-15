import { createFileRoute } from "@tanstack/react-router";
import { Tractor } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";

export const Route = createFileRoute("/equipment")({
  head: () => ({ meta: [{ title: "Equipment · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={Tractor}
        eyebrow="Custom Hiring Centers"
        title="Equipment"
        description="Booking, telematics, and utilization analytics across Custom Hiring Centers."
      />

      <StatGrid stats={[
        { label: "Assets", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Bookings · 24h", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Utilization", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Farmer savings", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={Tractor} title="No equipment inventory" description="Waiting for backend — fleet inventory and live bookings will appear here." />
    </AppShell>
  );
}
