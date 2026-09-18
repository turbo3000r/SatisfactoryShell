import { toast } from "sonner"

import { ApiError } from "@/lib/api"

/** Friendly text for the game-API error codes the backend passes through. */
const FRIENDLY: Record<string, string> = {
  wrong_password: "Wrong password.",
  unauthorized: "Wrong password.",
  passwordless_login_not_possible: "This server requires the admin password.",
  api_unavailable: "Server API unreachable (server offline or loading a save). Try again in a moment.",
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) return FRIENDLY[error.code] ?? (error.message || error.code)
  return error instanceof Error ? error.message : String(error)
}

export function toastError(error: unknown) {
  toast.error(describeError(error))
}
