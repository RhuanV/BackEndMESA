/** Extracts the FastAPI `detail` message from an axios-style error, if present. */
export function extractErrorDetail(err: unknown): string | undefined {
  if (err && typeof err === 'object' && 'response' in err) {
    return (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
  }
  return undefined;
}
