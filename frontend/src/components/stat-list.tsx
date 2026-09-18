import type { ReactNode } from "react"

export type Stat = { label: string; value: ReactNode }

/** Key/value rows, the React counterpart of the old `dl.kv` blocks. */
export function StatList({ items }: { items: Stat[] }) {
  return (
    <dl className="flex flex-col gap-2 text-sm">
      {items.map(({ label, value }) => (
        <div
          key={label}
          className="flex items-baseline justify-between gap-4 border-b border-border pb-2 last:border-0 last:pb-0"
        >
          <dt className="text-muted-foreground">{label}</dt>
          <dd className="min-w-0 truncate text-right font-medium">{value}</dd>
        </div>
      ))}
    </dl>
  )
}
