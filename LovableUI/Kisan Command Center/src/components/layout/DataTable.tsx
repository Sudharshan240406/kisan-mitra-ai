import type { ReactNode } from "react";

export type Column<T> = {
  key: keyof T | string;
  header: string;
  render?: (row: T) => ReactNode;
  className?: string;
};

export function DataTable<T extends Record<string, any>>({
  columns,
  rows,
}: {
  columns: Column<T>[];
  rows: T[];
}) {
  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0">
      <table className="w-full min-w-[640px] border-separate border-spacing-y-1.5 px-4 sm:px-0">
        <thead>
          <tr className="text-left text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">
            {columns.map((c) => (
              <th key={String(c.key)} className={`px-3 pb-2 ${c.className ?? ""}`}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className="text-sm text-white/80 transition hover:bg-white/[0.03]"
            >
              {columns.map((c, ci) => (
                <td
                  key={String(c.key)}
                  className={[
                    "bg-white/[0.02] px-3 py-3 first:rounded-l-xl last:rounded-r-xl ring-1 ring-inset ring-white/5",
                    c.className ?? "",
                  ].join(" ")}
                >
                  {c.render ? c.render(row) : String(row[c.key as keyof T] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
