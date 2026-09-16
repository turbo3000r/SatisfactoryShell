import { useEffect, useRef } from "react"

import { cn } from "@/lib/utils"

type LogViewProps = {
  text: string
  follow?: boolean
  className?: string
  empty?: string
}

/** Monospace tail view for FactoryGame.log and SteamCMD output. */
export function LogView({ text, follow = true, className, empty = "(no output yet)" }: LogViewProps) {
  const ref = useRef<HTMLPreElement>(null)

  useEffect(() => {
    if (follow && ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [text, follow])

  return (
    <pre
      ref={ref}
      className={cn(
        "h-96 overflow-auto rounded-md border border-border bg-muted/30 p-3 font-mono text-xs whitespace-pre-wrap text-muted-foreground",
        className,
      )}
    >
      {text || empty}
    </pre>
  )
}
