import type { ReactNode } from "react";
import { AlertTriangle, Inbox, RefreshCw, WifiOff } from "lucide-react";
import type { ResourceState } from "@/hooks/useResource";
import { Skeleton } from "./Skeleton";

type Props<T> = {
  state: ResourceState<T>;
  children: (data: T) => ReactNode;
  skeleton?: ReactNode;
  emptyTitle?: string;
  emptyHint?: string;
  minHeight?: string;
};

// Wraps any data-driven section with a uniform loading / error / empty /
// offline treatment so every page behaves the same way.
export function StateWrapper<T>({ state, children, skeleton, emptyTitle = "Nothing here yet", emptyHint, minHeight = "min-h-[160px]" }: Props<T>) {
  if (state.isOffline) {
    return (
      <div className={`${minHeight} grid place-items-center rounded-xl bg-white/[0.02] p-6 text-center ring-1 ring-inset ring-white/5`}>
        <div>
          <WifiOff className="mx-auto size-6 text-white/40" />
          <div className="mt-2 text-sm font-semibold text-white/80">You're offline</div>
          <div className="mt-1 text-xs text-white/50">Cached data will sync once you're back online.</div>
        </div>
      </div>
    );
  }
  if (state.loading) {
    return <div className={minHeight}>{skeleton ?? <DefaultSkeleton />}</div>;
  }
  if (state.error) {
    return (
      <div className={`${minHeight} grid place-items-center rounded-xl bg-red-500/[0.06] p-6 text-center ring-1 ring-inset ring-red-500/20`}>
        <div>
          <AlertTriangle className="mx-auto size-6 text-red-300" />
          <div className="mt-2 text-sm font-semibold text-white/85">Something went wrong</div>
          <div className="mt-1 text-xs text-white/50">{state.error.message}</div>
          <button
            onClick={state.refetch}
            className="mt-3 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold text-white/90 ring-1 ring-inset ring-white/15 hover:bg-white/15"
          >
            <RefreshCw className="size-3" /> Retry
          </button>
        </div>
      </div>
    );
  }
  if (state.isEmpty) {
    return (
      <div className={`${minHeight} grid place-items-center rounded-xl bg-white/[0.02] p-6 text-center ring-1 ring-inset ring-white/5`}>
        <div>
          <Inbox className="mx-auto size-6 text-white/40" />
          <div className="mt-2 text-sm font-semibold text-white/80">{emptyTitle}</div>
          {emptyHint && <div className="mt-1 text-xs text-white/50">{emptyHint}</div>}
        </div>
      </div>
    );
  }
  return (
    <div className="relative">
      {state.refreshing && (
        <div className="pointer-events-none absolute right-0 top-0 flex items-center gap-1.5 text-[10px] text-mono text-white/40">
          <RefreshCw className="size-3 animate-spin" /> refreshing
        </div>
      )}
      {children(state.data as T)}
    </div>
  );
}

function DefaultSkeleton() {
  return (
    <div className="space-y-2">
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-8 w-11/12" />
      <Skeleton className="h-8 w-10/12" />
    </div>
  );
}
