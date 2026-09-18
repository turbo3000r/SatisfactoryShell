import { MoonIcon, SunIcon } from "lucide-react"

import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

export function ModeToggle() {
  const { resolvedTheme, toggleTheme } = useTheme()
  const next = resolvedTheme === "dark" ? "light" : "dark"

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon" className="size-8" onClick={toggleTheme}>
          {resolvedTheme === "dark" ? <MoonIcon /> : <SunIcon />}
          <span className="sr-only">Switch to {next} theme</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent>Switch to {next} theme</TooltipContent>
    </Tooltip>
  )
}
