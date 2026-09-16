import { useCallback, useEffect, useRef, useState } from "react"

type PollResult<T> = {
  data: T | null
  error: Error | null
  loading: boolean
  reload: () => Promise<void>
}

/**
 * Fetch once, then on an interval. Replaces the `hx-trigger="every Ns"`
 * polling of the old HTMX pages.
 */
export function usePoll<T>(fetcher: () => Promise<T>, intervalMs: number, enabled = true): PollResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(enabled)
  const fetcherRef = useRef(fetcher)

  useEffect(() => {
    fetcherRef.current = fetcher
  }, [fetcher])

  const reload = useCallback(async () => {
    try {
      setData(await fetcherRef.current())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return
    void reload()
    const id = window.setInterval(() => void reload(), intervalMs)
    return () => window.clearInterval(id)
  }, [enabled, intervalMs, reload])

  return { data, error, loading, reload }
}
