import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Radio } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { LiveCallCard } from "@/components/mission/LiveCallCard";
import { TranscriptPanel } from "@/components/mission/TranscriptPanel";
import { ReasoningPipeline } from "@/components/mission/ReasoningPipeline";
import { SchemesPanel, EligibilityPanel } from "@/components/mission/SchemesPanel";
import { FarmerTwin } from "@/components/mission/FarmerTwin";
import { DocumentAdvisor } from "@/components/mission/DocumentAdvisor";
import { MissionTimeline } from "@/components/mission/MissionTimeline";
import { AgentsPanel } from "@/components/mission/AgentsPanel";
import { TelemetryPanel } from "@/components/mission/TelemetryPanel";
import { WorkflowCanvas } from "@/components/mission/WorkflowCanvas";
import {
  createMissionDataSource,
  EMPTY_SNAPSHOT,
  type ConnectionState,
  type MissionSnapshot,
} from "@/api/mission";

export const Route = createFileRoute("/mission-control")({
  head: () => ({
    meta: [
      { title: "Mission Control · Kisan Mitra AI" },
      { name: "description", content: "Live AI operations command center for Kisan Mitra — monitors active IVR calls, farmer identification, government scheme matching, and eligibility reasoning in real time." },
      { property: "og:title", content: "Mission Control · Kisan Mitra AI" },
      { property: "og:description", content: "Watch Kisan Mitra AI help farmers discover government schemes over a feature phone — live." },
    ],
  }),
  component: MissionControl,
});

function MissionControl() {
  const dataSource = useMemo(() => createMissionDataSource(), []);
  const [snapshot, setSnapshot] = useState<MissionSnapshot>(() => dataSource.getSnapshot());
  const [connection, setConnection] = useState<ConnectionState>(() => dataSource.getConnectionState());

  useEffect(() => {
    const unsub = dataSource.subscribe((e) => {
      switch (e.type) {
        case "snapshot":
          setSnapshot(e.snapshot);
          break;
        case "connection":
          setConnection(e.state);
          break;
        case "call":
          setSnapshot((s) => ({ ...s, call: e.call }));
          break;
        case "stage":
          setSnapshot((s) => (s.call ? { ...s, call: { ...s.call, currentStage: e.stage } } : s));
          break;
        case "transcript":
          setSnapshot((s) => ({ ...s, transcript: [...s.transcript, e.line] }));
          break;
        case "schemes":
          setSnapshot((s) => ({ ...s, schemes: e.schemes }));
          break;
        case "eligibility":
          setSnapshot((s) => ({ ...s, eligibility: e.checks }));
          break;
        case "agents":
          setSnapshot((s) => ({ ...s, agents: e.agents }));
          break;
        case "telemetry":
          setSnapshot((s) => ({ ...s, telemetry: e.vitals }));
          break;
        case "timeline":
          setSnapshot((s) => ({ ...s, timeline: [...s.timeline, e.entry] }));
          break;
        case "thinking":
          setSnapshot((s) => ({ ...s, thinking: e.value }));
          break;
      }
    });

    void dataSource.connect();

    return () => {
      unsub();
      void dataSource.disconnect();
    };
  }, [dataSource]);

  const { call, transcript, schemes, eligibility, agents, telemetry, timeline, thinking } = snapshot;
  // Reference to keep the empty snapshot in scope for future reset flows.
  void EMPTY_SNAPSHOT;

  return (
    <AppShell>
      <PageHeader
        icon={Radio}
        eyebrow={`Live · ${connection === "open" ? "stream connected" : "awaiting backend"}`}
        title="Mission Control"
        description="Real-time visualization of active farmer calls — from speech to government scheme recommendation. Connects to the FastAPI mission stream."
      />

      <LiveCallCard call={call} />

      <WorkflowCanvas snapshot={snapshot} />


      <section className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-8">
          <TranscriptPanel lines={transcript} thinking={thinking} />
          <SchemesPanel schemes={schemes} />
          <DocumentAdvisor schemes={schemes} />
        </div>

        <div className="space-y-6 xl:col-span-4">
          <ReasoningPipeline current={call?.currentStage ?? null} />
          <FarmerTwin farmer={call?.farmer ?? null} />
          <EligibilityPanel checks={eligibility} />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <MissionTimeline entries={timeline} currentStage={call?.currentStage ?? null} />
        <AgentsPanel agents={agents} />
        <TelemetryPanel vitals={telemetry} />
      </section>
    </AppShell>
  );
}
