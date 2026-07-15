export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={[
        "relative overflow-hidden rounded-lg bg-white/5",
        "before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.6s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent",
        className,
      ].join(" ")}
    />
  );
}
