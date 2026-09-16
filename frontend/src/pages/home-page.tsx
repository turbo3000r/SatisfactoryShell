import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export function HomePage() {
  return (
    <div className="px-4 lg:px-6">
      <Card className="@container/card">
        <CardHeader>
          <CardTitle>Server status</CardTitle>
          <CardDescription>
            Placeholder card &mdash; wire this up to the FastAPI status
            endpoint during the backend migration.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-2">
          <Badge variant="outline">Offline</Badge>
          <span className="text-sm text-muted-foreground">
            No connection to the dedicated server yet.
          </span>
        </CardContent>
        <CardFooter>
          <Button size="sm">Start server</Button>
        </CardFooter>
      </Card>
    </div>
  )
}
