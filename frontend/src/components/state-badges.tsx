import { Badge } from "@/components/ui/badge"
import { formatTickRate } from "@/lib/format"

type Variant = "default" | "secondary" | "destructive" | "outline"

const STATE_VARIANTS: Record<string, Variant> = {
  Playing: "default",
  Idle: "secondary",
  Loading: "outline",
  Starting: "outline",
  Offline: "destructive",
}

export function ServerStateBadge({ name }: { name: string }) {
  return <Badge variant={STATE_VARIANTS[name] ?? "outline"}>{name}</Badge>
}

export function TickRateBadge({ value }: { value: number | null | undefined }) {
  const tick = value ?? 0
  const variant: Variant = tick >= 25 ? "default" : tick >= 10 ? "secondary" : "destructive"
  return <Badge variant={variant}>{formatTickRate(value)}</Badge>
}

export function HealthBadge({ health }: { health: string | null }) {
  if (!health) return <span className="text-muted-foreground">-</span>
  return <Badge variant={health === "healthy" ? "default" : "secondary"}>{health}</Badge>
}

export function OnOffBadge({ on, labels = ["on", "off"] }: { on: boolean; labels?: [string, string] }) {
  return <Badge variant={on ? "default" : "secondary"}>{on ? labels[0] : labels[1]}</Badge>
}

export function SaveFlagBadges({ header }: { header: { modded: boolean; edited: boolean; creative: boolean } }) {
  const flags = [
    header.modded && "modded",
    header.edited && "edited",
    header.creative && "AGS",
  ].filter(Boolean) as string[]

  if (flags.length === 0) return <span className="text-muted-foreground">-</span>
  return (
    <div className="flex flex-wrap gap-1">
      {flags.map((flag) => (
        <Badge key={flag} variant="outline">
          {flag}
        </Badge>
      ))}
    </div>
  )
}
