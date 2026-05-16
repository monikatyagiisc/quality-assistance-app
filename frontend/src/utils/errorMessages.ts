import { ApiError } from '../api/client'

const QUOTA_PATTERNS = [
  /resource_exhausted/i,
  /quota exceeded/i,
  /insufficient_quota/i,
  /rate.?limit/i,
  /\b429\b/,
  /free_tier/i,
]

const API_KEY_PATTERNS = [
  /google_api_key/i,
  /openai_api_key/i,
  /invalid.?api.?key/i,
  /incorrect.?api.?key/i,
  /authenticationerror/i,
  /api key/i,
]

const CONTEXT_LENGTH_PATTERNS = [
  /context.?length/i,
  /token limit/i,
  /too many tokens/i,
  /maximum context/i,
]

const TIMEOUT_PATTERNS = [/timeout/i, /timed out/i]

const AGENT_UNREACHABLE_PATTERNS = [
  /agent service is not running/i,
  /not reachable/i,
  /connection refused/i,
  /failed to fetch/i,
]

function matchesAny(text: string, patterns: RegExp[]): boolean {
  return patterns.some((pattern) => pattern.test(text))
}

function extractRetrySeconds(text: string): number | null {
  const match = text.match(/retry in (\d+(?:\.\d+)?)s/i)
  if (!match) return null
  return Math.max(1, Math.round(Number(match[1])))
}

function mapQuotaMessage(raw: string): string {
  const waitSeconds = extractRetrySeconds(raw)
  let message =
    'The AI provider rate limit or free-tier quota was exceeded. Please wait a moment and try again.'
  if (waitSeconds) {
    message += ` Suggested wait: about ${waitSeconds} seconds.`
  }
  message += ' If this keeps happening, check your model provider plan and billing.'
  return message
}

/** Turn API/network errors into short, user-facing copy for the dashboard. */
export function getUserFriendlyError(error: unknown): string {
  if (error instanceof ApiError) {
    const raw = error.message
    const combined = `${raw} ${error.code ?? ''}`

    if (error.code === 'quota_exceeded' || matchesAny(combined, QUOTA_PATTERNS)) {
      return mapQuotaMessage(raw)
    }

    if (error.code === 'context_length_exceeded' || matchesAny(combined, CONTEXT_LENGTH_PATTERNS)) {
      return 'The prompt is too long for the selected model. Shorten your input and try again.'
    }

    if (error.code === 'model_not_found') {
      return 'The configured AI model is not available. Contact your administrator to update agent configuration.'
    }

    if (error.code === 'invalid_api_key' || matchesAny(combined, API_KEY_PATTERNS)) {
      return 'The AI API key is missing or invalid. Contact your administrator to fix agent configuration.'
    }

    if (error.code === 'agent_unreachable' || matchesAny(combined, AGENT_UNREACHABLE_PATTERNS)) {
      return 'The quality assistant service is offline. Start the agent service and try again.'
    }

    if (error.code === 'timeout' || matchesAny(combined, TIMEOUT_PATTERNS)) {
      return 'The request timed out. Try again with a shorter prompt.'
    }

    if (error.status === 401) {
      return 'Your session expired. Please sign in again.'
    }

    if (error.status === 503) {
      return raw.length < 220
        ? raw
        : 'The quality assistant is temporarily unavailable. Please try again shortly.'
    }

    if (error.status === 502 || error.status === 500) {
      if (matchesAny(combined, QUOTA_PATTERNS)) {
        return mapQuotaMessage(raw)
      }
      return 'We could not generate quality assistance right now. Please try again in a few minutes.'
    }

    if (error.status === 429) {
      return mapQuotaMessage(raw)
    }

    return raw.length < 220 ? raw : 'Something went wrong. Please try again.'
  }

  if (error instanceof Error && error.message) {
    if (matchesAny(error.message, AGENT_UNREACHABLE_PATTERNS)) {
      return 'Cannot reach the server. Check that the backend is running.'
    }
    return error.message
  }

  return 'Something went wrong. Please try again.'
}
