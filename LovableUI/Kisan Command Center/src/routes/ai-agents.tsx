import { createFileRoute } from "@tanstack/react-router";
import { Bot, Plus, Activity } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { AgentGrid } from "@/components/kisan/AgentGrid";
import { EmptyState } from "@/components/layout/EmptyState";
import { ActionButton } from "@/components/layout/ActionButton";

export const Route = createFileRoute("/ai-agents")({
  head: () => ({ meta: [{ title: "AI Agents · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  return (
    <AppShell>
      <PageHeader
        icon={Bot}
        eyebrow="Neural fleet"
        title="AI Agents"
        description="Specialized agents handling advisory, market, weather, disease detection, and government scheme orchestration."
        actions={<><ActionButton icon={Activity}>Logs</ActionButton><ActionButton icon={Plus} variant="primary">New agent</ActionButton></>}
      />

      <StatGrid stats={[
        { label: "Active agents", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Avg latency", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Handoffs · 24h", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Escalation rate", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <AgentGrid />

      <EmptyState icon={Bot} title="No orchestrations" description="Waiting for backend — recent agent handoffs and guardrail metrics will appear here." />
    </AppShell>
  );
}
