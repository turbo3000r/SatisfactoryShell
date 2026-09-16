import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"

import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { MetricsSample } from "@/lib/api"
import { formatClock } from "@/lib/format"

type Row = {
  time: string
  proc_cpu: number | null
  proc_rss_mb: number | null
  players: number | null
  tick_rate: number | null
  host_cpu: number
  host_mem_pct: number
}

const VIEWS: { value: string; label: string; description: string; config: ChartConfig }[] = [
  {
    value: "cpu",
    label: "Process CPU",
    description: "FactoryServer.exe CPU usage in percent of the whole host.",
    config: { proc_cpu: { label: "CPU %", color: "var(--chart-1)" } },
  },
  {
    value: "memory",
    label: "Memory",
    description: "FactoryServer.exe resident memory in MB.",
    config: { proc_rss_mb: { label: "RSS MB", color: "var(--chart-2)" } },
  },
  {
    value: "game",
    label: "Players & tick rate",
    description: "Connected players and the average server tick rate.",
    config: {
      players: { label: "Players", color: "var(--chart-3)" },
      tick_rate: { label: "Tick rate", color: "var(--chart-4)" },
    },
  },
  {
    value: "host",
    label: "Host",
    description: "Host CPU and memory utilisation in percent.",
    config: {
      host_cpu: { label: "Host CPU %", color: "var(--chart-1)" },
      host_mem_pct: { label: "Host mem %", color: "var(--chart-5)" },
    },
  },
]

function MetricChart({ rows, config }: { rows: Row[]; config: ChartConfig }) {
  return (
    <ChartContainer config={config} className="aspect-auto h-64 w-full">
      <AreaChart data={rows} margin={{ left: 4, right: 4, top: 8 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="time" tickLine={false} axisLine={false} tickMargin={8} minTickGap={48} />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} width={44} />
        <ChartTooltip content={<ChartTooltipContent indicator="line" />} />
        {Object.keys(config).map((key) => (
          <Area
            key={key}
            dataKey={key}
            type="monotone"
            stroke={`var(--color-${key})`}
            fill={`var(--color-${key})`}
            fillOpacity={0.15}
            strokeWidth={2}
            dot={false}
            connectNulls
          />
        ))}
      </AreaChart>
    </ChartContainer>
  )
}

/** The four Chart.js canvases of the old dashboard, as one tabbed card. */
export function MetricsCharts({ samples }: { samples: MetricsSample[] }) {
  const rows: Row[] = samples.map((sample) => ({
    time: formatClock(sample.ts),
    proc_cpu: sample.proc_cpu,
    proc_rss_mb: sample.proc_rss_mb,
    players: sample.players,
    tick_rate: sample.tick_rate,
    host_cpu: sample.host_cpu,
    host_mem_pct: sample.host_mem_pct,
  }))

  return (
    <Card>
      <Tabs defaultValue={VIEWS[0].value}>
        <CardHeader>
          <CardTitle>Metrics</CardTitle>
          <CardDescription>Sampled by the shell every few seconds.</CardDescription>
          <CardAction>
            <TabsList>
              {VIEWS.map((view) => (
                <TabsTrigger key={view.value} value={view.value}>
                  {view.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </CardAction>
        </CardHeader>
        <CardContent>
          {VIEWS.map((view) => (
            <TabsContent key={view.value} value={view.value} className="flex flex-col gap-2">
              <p className="text-sm text-muted-foreground">{view.description}</p>
              {rows.length === 0 ? (
                <p className="text-sm text-muted-foreground">No samples collected yet.</p>
              ) : (
                <MetricChart rows={rows} config={view.config} />
              )}
            </TabsContent>
          ))}
        </CardContent>
      </Tabs>
    </Card>
  )
}
