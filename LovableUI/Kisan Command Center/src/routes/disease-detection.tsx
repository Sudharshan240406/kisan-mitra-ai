import { createFileRoute } from "@tanstack/react-router";
import { Bug, Camera, Upload } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { EmptyState } from "@/components/layout/EmptyState";
import { ActionButton } from "@/components/layout/ActionButton";

export const Route = createFileRoute("/disease-detection")({
  head: () => ({ meta: [{ title: "Disease Detection · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={Bug}
        eyebrow="Vision-Agri"
        title="Disease Detection"
        description="Multimodal leaf & pest recognition — farmer uploads triaged by AI, confirmed by agronomist panel."
        actions={<><ActionButton icon={Camera}>Live capture</ActionButton><ActionButton icon={Upload} variant="primary">Upload sample</ActionButton></>}
      />

      <StatGrid stats={[
        { label: "Diagnoses · 24h", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Model accuracy", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Diseases covered", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Outbreaks flagged", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <EmptyState icon={Bug} title="No detections yet" description="Waiting for backend — live triage results and agronomist reviews will surface here as they arrive." />
    </AppShell>
  );
}
