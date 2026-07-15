// Mission Control data contract.
//
// The UI depends ONLY on the `MissionControlDataSource` interface below.
// No mock data, no timers, no simulated events are generated here.
//
// A concrete implementation (e.g. `WebSocketMissionDataSource`) will be
// wired in later — it must translate backend messages into `MissionEvent`s
// and hand a `MissionSnapshot` on `connect()`.

// ---------- Domain types ----------

export type CallStage =
  | "speech-recognition"
  | "intent-detection"
  | "farmer-identification"
  | "digital-twin"
  | "scheme-search"
  | "eligibility"
  | "knowledge-retrieval"
  | "reasoning"
  | "response-generation"
  | "voice-playback";

export const STAGES: { id: CallStage; label: string; hint: string }[] = [
  { id: "speech-recognition", label: "Speech Recognition", hint: "ASR pipeline" },
  { id: "intent-detection", label: "Intent Detection", hint: "LLM classifier" },
  { id: "farmer-identification", label: "Farmer Identification", hint: "Aadhaar + phone match" },
  { id: "digital-twin", label: "Digital Twin Loaded", hint: "Land · crop · history" },
  { id: "scheme-search", label: "Scheme Search", hint: "Vector + rule retrieval" },
  { id: "eligibility", label: "Eligibility Evaluation", hint: "Rule engine + LLM" },
  { id: "knowledge-retrieval", label: "Knowledge Retrieval", hint: "RAG · gov circulars" },
  { id: "reasoning", label: "AI Reasoning", hint: "Chief agent" },
  { id: "response-generation", label: "Response Generation", hint: "TTS script" },
  { id: "voice-playback", label: "Voice Playback", hint: "IVR outbound stream" },
];

export type TranscriptLine = {
  id: string;
  speaker: "farmer" | "ai";
  text: string;
  at: string;
  lang?: string;
};

export type LiveCall = {
  id: string;
  status: "ringing" | "active" | "wrap-up";
  farmer: {
    name: string;
    phone: string;
    state: string;
    district: string;
    village: string;
    crop: string;
    language: string;
    landHa: number;
    category: "Marginal" | "Small" | "Semi-medium" | "Medium" | "Large";
    aadhaarMasked: string;
    lastInteraction: string;
    twinConfidence: number;
    previousScheme?: string;
    avatarInitials: string;
  };
  startedAt: string;
  durationSec: number;
  currentStage: CallStage;
  latencyMs: number;
  connection: "5G" | "4G" | "3G" | "2G";
};

export type SchemeRecommendation = {
  id: string;
  name: string;
  department: string;
  eligibility: "Eligible" | "Likely" | "Review";
  confidence: number;
  benefit: string;
  documents: { name: string; status: "have" | "missing" }[];
  deadline: string;
  helpline: string;
  why: string;
};

export type EligibilityCheck = {
  label: string;
  status: "pass" | "warn" | "fail";
  detail: string;
};

export type AgentSnapshot = {
  id: string;
  name: string;
  role: string;
  status: "active" | "idle" | "degraded";
  latencyMs: number;
  task: string;
};

export type TelemetryVitals = {
  activeCalls: number | null;
  activeFarmers: number | null;
  avgLatencyMs: number | null;
  recommendationsToday: number | null;
  systemHealthPct: number | null;
  cpuPct: number | null;
  gpuPct: number | null;
};

export type TimelineEntry = {
  at: string;
  stage: CallStage;
  note?: string;
};

// ---------- Snapshot + events ----------

export type MissionSnapshot = {
  call: LiveCall | null;
  transcript: TranscriptLine[];
  schemes: SchemeRecommendation[];
  eligibility: EligibilityCheck[];
  agents: AgentSnapshot[];
  telemetry: TelemetryVitals;
  timeline: TimelineEntry[];
  thinking: boolean;
};

export const EMPTY_SNAPSHOT: MissionSnapshot = {
  call: null,
  transcript: [],
  schemes: [],
  eligibility: [],
  agents: [],
  telemetry: {
    activeCalls: null,
    activeFarmers: null,
    avgLatencyMs: null,
    recommendationsToday: null,
    systemHealthPct: null,
    cpuPct: null,
    gpuPct: null,
  },
  timeline: [],
  thinking: false,
};

export type ConnectionState = "idle" | "connecting" | "open" | "closed" | "error";

export type MissionEvent =
  | { type: "snapshot"; snapshot: MissionSnapshot }
  | { type: "call"; call: LiveCall | null }
  | { type: "stage"; stage: CallStage }
  | { type: "transcript"; line: TranscriptLine }
  | { type: "schemes"; schemes: SchemeRecommendation[] }
  | { type: "eligibility"; checks: EligibilityCheck[] }
  | { type: "agents"; agents: AgentSnapshot[] }
  | { type: "telemetry"; vitals: TelemetryVitals }
  | { type: "timeline"; entry: TimelineEntry }
  | { type: "thinking"; value: boolean }
  | { type: "connection"; state: ConnectionState };

export type MissionListener = (event: MissionEvent) => void;
export type Unsubscribe = () => void;

// ---------- Data source interface ----------

export interface MissionControlDataSource {
  /** Snapshot exposed to first subscribers before any events arrive. */
  getSnapshot(): MissionSnapshot;
  /** Current transport state. */
  getConnectionState(): ConnectionState;
  /** Open the underlying transport (e.g. WebSocket). No-op until implemented. */
  connect(): Promise<void> | void;
  /** Close the transport and release listeners. */
  disconnect(): Promise<void> | void;
  /** Subscribe to backend events. Returns an unsubscribe function. */
  subscribe(listener: MissionListener): Unsubscribe;
  /** Explicit removal (kept for parity with the requested interface). */
  unsubscribe(listener: MissionListener): void;
}

// ---------- Null data source ----------
// Produces no events. Used until the real transport is wired in.

export class NullMissionDataSource implements MissionControlDataSource {
  private listeners = new Set<MissionListener>();
  private state: ConnectionState = "idle";

  getSnapshot(): MissionSnapshot {
    return EMPTY_SNAPSHOT;
  }

  getConnectionState(): ConnectionState {
    return this.state;
  }

  connect(): void {
    this.state = "closed";
    for (const l of this.listeners) l({ type: "connection", state: this.state });
  }

  disconnect(): void {
    this.state = "closed";
    for (const l of this.listeners) l({ type: "connection", state: this.state });
  }

  subscribe(listener: MissionListener): Unsubscribe {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  unsubscribe(listener: MissionListener): void {
    this.listeners.delete(listener);
  }
}

/**
 * Factory the UI consumes. Swap the body with a `WebSocketMissionDataSource`
 * once the FastAPI backend exposes the mission stream — no component changes
 * required.
 */
export function createMissionDataSource(): MissionControlDataSource {
  return new NullMissionDataSource();
}
