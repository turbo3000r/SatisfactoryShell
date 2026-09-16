import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

export function ConsolePage() {
  return (
    <div className="flex flex-col gap-4 px-4 lg:px-6">
      <Card>
        <CardHeader>
          <CardTitle>Server console</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="h-64 rounded-md border bg-muted/30 p-3 font-mono text-xs text-muted-foreground">
            Log tail / command history placeholder.
          </div>
          <div className="flex gap-2">
            <Input placeholder="Run a server command..." />
            <Button>Run</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
