import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export function SavesPage() {
  return (
    <div className="px-4 lg:px-6">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Save name</TableHead>
            <TableHead>Session</TableHead>
            <TableHead>Play time</TableHead>
            <TableHead>Saved at</TableHead>
            <TableHead>Flags</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell colSpan={5} className="text-center text-muted-foreground">
              Save list will be wired up to `/saves` once the backend exposes
              a JSON API.
              <Badge variant="outline" className="ml-2">
                TODO
              </Badge>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  )
}
