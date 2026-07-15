import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Users, UserPlus, Filter, Phone, MapPin, Sprout, Landmark, Layers, MessageSquare, IndianRupee } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { DataTable } from "@/components/layout/DataTable";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { ActionButton } from "@/components/layout/ActionButton";
import { SearchInput } from "@/components/layout/SearchInput";
import { FilterChips } from "@/components/layout/FilterChips";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { Drawer } from "@/components/layout/Drawer";
import { Timeline } from "@/components/layout/Timeline";
import { useResource } from "@/hooks/useResource";
import { farmersApi, type Farmer } from "@/api/farmers";

export const Route = createFileRoute("/farmers")({
  head: () => ({ meta: [{ title: "Farmers · Kisan Mitra" }] }),
  component: Page,
});

function Page() {
  const [q, setQ] = useState("");
  const [state, setState] = useState<string | null>(null);
  const [status, setStatus] = useState<Farmer["status"] | null>(null);
  const [selected, setSelected] = useState<Farmer | null>(null);

  const filters = useMemo(
    () => ({ q, state: state ?? undefined, status: status ?? undefined }),
    [q, state, status],
  );

  const farmers = useResource(() => farmersApi.list(filters), [q, state, status]);
  const states = useResource(() => farmersApi.states(), []);

  return (
    <AppShell>
      <PageHeader
        icon={Users}
        eyebrow="CRM"
        title="Farmers"
        description="Unified farmer directory across 28 states — Aadhaar-linked profiles, cropping history, and outreach status."
        actions={<>
          <ActionButton icon={Filter}>Advanced</ActionButton>
          <ActionButton icon={UserPlus} variant="primary">Enroll farmer</ActionButton>
        </>}
      />

      <StatGrid stats={[
        { label: "Enrolled", value: "—", delta: "Waiting for backend", tone: "lime" },
        { label: "Active · 30d", value: "—", delta: "Waiting for backend", tone: "sky" },
        { label: "Onboarding", value: "—", delta: "Waiting for backend", tone: "wheat" },
        { label: "Avg. land", value: "—", delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <GlassCard eyebrow="Directory" title="Registered farmers" strong
        actions={<SearchInput value={q} onChange={setQ} placeholder="Search name, village, ID, crop" className="hidden w-72 sm:flex" />}>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">State</div>
          <FilterChips
            options={(states.data ?? []).map((s) => ({ value: s, label: s }))}
            value={state}
            onChange={setState}
          />
          <div className="mx-2 h-4 w-px bg-white/10" />
          <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">Status</div>
          <FilterChips
            options={[
              { value: "Active", label: "Active" },
              { value: "Onboarding", label: "Onboarding" },
              { value: "Dormant", label: "Dormant" },
            ]}
            value={status ?? null}
            onChange={(v) => setStatus(v as Farmer["status"] | null)}
          />
          <div className="ml-auto sm:hidden">
            <SearchInput value={q} onChange={setQ} placeholder="Search…" className="w-full" />
          </div>
        </div>

        <StateWrapper state={farmers} emptyTitle="No farmers match your filters" emptyHint="Try clearing filters or search terms.">
          {(rows) => (
            <DataTable<Farmer>
              columns={[
                { key: "id", header: "ID", render: (r) => <span className="text-mono text-[11px] text-[var(--lime-glow)]">{r.id}</span> },
                { key: "name", header: "Name", render: (r) => (
                  <button onClick={() => setSelected(r)} className="text-left font-semibold text-white hover:text-[var(--lime-glow)]">{r.name}</button>
                ) },
                { key: "village", header: "Village", render: (r) => <span>{r.village}, {r.district}</span> },
                { key: "state", header: "State" },
                { key: "crop", header: "Primary crop" },
                { key: "landHa", header: "Land", render: (r) => `${r.landHa} ha` },
                { key: "status", header: "Status", render: (r) => (
                  <StatusBadge tone={r.status === "Active" ? "lime" : r.status === "Onboarding" ? "wheat" : "muted"} dot>{r.status}</StatusBadge>
                ) },
              ]}
              rows={rows}
            />
          )}
        </StateWrapper>
      </GlassCard>

      <FarmerDrawer farmer={selected} onClose={() => setSelected(null)} />
    </AppShell>
  );
}

function FarmerDrawer({ farmer, onClose }: { farmer: Farmer | null; onClose: () => void }) {
  const timeline = useResource(
    () => farmer ? farmersApi.timeline(farmer.id) : Promise.resolve({ data: [] as any[] }),
    [farmer?.id],
  );
  return (
    <Drawer open={!!farmer} onClose={onClose} eyebrow={farmer?.id} title={farmer?.name} widthClass="sm:max-w-lg">
      {farmer && (
        <div className="space-y-5">
          <div className="flex items-center gap-2 text-xs text-white/60">
            <Phone className="size-3.5 text-[var(--lime-glow)]" /> {farmer.phone}
            <span className="mx-1 h-3 w-px bg-white/10" />
            <MapPin className="size-3.5 text-[var(--sky-agri)]" /> {farmer.village}, {farmer.district}, {farmer.state}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Facet icon={Sprout} label="Primary crop" value={farmer.crop} />
            <Facet icon={Layers} label="Land" value={`${farmer.landHa} ha`} />
            <Facet icon={Landmark} label="Soil · irrigation" value={`${farmer.soil} · ${farmer.irrigation}`} />
            <Facet icon={IndianRupee} label="KCC limit" value={farmer.kccLimit ? `₹${(farmer.kccLimit / 1000).toFixed(0)}k` : "—"} />
          </div>

          <div>
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/40">Crops this season</div>
            <div className="flex flex-wrap gap-1.5">
              {farmer.crops.map((c) => <StatusBadge key={c} tone="lime">{c}</StatusBadge>)}
            </div>
          </div>

          <div>
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/40">Enrolled schemes</div>
            <div className="flex flex-wrap gap-1.5">
              {farmer.schemes.length ? farmer.schemes.map((s) => <StatusBadge key={s} tone="sky">{s}</StatusBadge>) : <span className="text-xs text-white/40">None yet</span>}
            </div>
          </div>

          <div>
            <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/40">Crop & advisory timeline</div>
            <StateWrapper state={timeline}>
              {(items) => <Timeline items={items.map((i) => ({ at: i.at, kind: i.kind, text: i.text, tone: i.kind === "disease" ? "red" : i.kind === "weather" ? "sky" : i.kind === "market" ? "wheat" : "lime" }))} />}
            </StateWrapper>
          </div>

          <div className="flex flex-wrap gap-2 border-t border-white/5 pt-4">
            <ActionButton icon={Phone} variant="primary">Call farmer</ActionButton>
            <ActionButton icon={MessageSquare}>Send advisory</ActionButton>
            <ActionButton icon={Landmark}>Check schemes</ActionButton>
          </div>
        </div>
      )}
    </Drawer>
  );
}

function Facet({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
      <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">
        <Icon className="size-3 text-[var(--lime-glow)]" /> {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-white">{value}</div>
    </div>
  );
}
