import { ChartAreaInteractive } from "@/components/chart-area-interactive"
import { DataTable } from "@/components/data-table"
import { SectionCards } from "@/components/section-cards"

// Demo data from the shadcn `dashboard-01` block. Will be replaced with live
// data from the FastAPI `/api/metrics` and process-status endpoints once the
// backend migration lands.
import demoData from "./dashboard-data.json"

export function DashboardPage() {
  return (
    <>
      <SectionCards />
      <div className="px-4 lg:px-6">
        <ChartAreaInteractive />
      </div>
      <DataTable data={demoData} />
    </>
  )
}
