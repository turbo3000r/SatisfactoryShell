/** Mirrors the backend `fmt_duration` Jinja filter. */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "-"
  const total = Math.max(0, Math.floor(seconds))
  const days = Math.floor(total / 86400)
  const hours = Math.floor((total % 86400) / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const parts: string[] = []
  if (days) parts.push(`${days}d`)
  if (days || hours) parts.push(`${hours}h`)
  parts.push(`${minutes}m`)
  if (!days) parts.push(`${total % 60}s`)
  return parts.join(" ")
}

/** Unix seconds to a local clock label, used for chart axes. */
export function formatClock(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}

export function formatTickRate(value: number | null | undefined): string {
  return value === null || value === undefined ? "-" : `${value.toFixed(1)} tps`
}

export function orDash(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "-"
  const text = String(value)
  return text.trim() === "" ? "-" : text
}
