import { useCallback, useState } from "react"
import { toast } from "sonner"

import { toastError } from "@/lib/errors"

type ActionResult = { message?: string } | void

/**
 * Runs a mutating API call, reports the outcome as a toast (the successor of
 * the old server-side flash messages) and optionally refreshes page data.
 */
export function useAction() {
  const [pending, setPending] = useState(false)

  const run = useCallback(async (action: () => Promise<ActionResult>, onDone?: () => void | Promise<void>) => {
    setPending(true)
    try {
      const result = await action()
      if (result?.message) toast.success(result.message)
      await onDone?.()
    } catch (error) {
      toastError(error)
    } finally {
      setPending(false)
    }
  }, [])

  return { pending, run }
}
