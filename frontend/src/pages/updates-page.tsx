import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export function UpdatesPage() {
  return (
    <div className="px-4 lg:px-6">
      <Card>
        <CardHeader>
          <CardTitle>SteamCMD updates</CardTitle>
          <CardDescription>Check and apply dedicated server updates.</CardDescription>
          <CardAction>
            <Badge variant="outline">Up to date</Badge>
          </CardAction>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Button variant="outline">Check for updates</Button>
          <Button>Run update</Button>
        </CardContent>
      </Card>
    </div>
  )
}
