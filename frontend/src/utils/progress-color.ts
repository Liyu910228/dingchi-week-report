/** Shared dashboard thresholds; compare raw values before rounding. */
export function progressColor(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "#74839a"
  return value > 80 ? "#16834a" : value > 50 ? "#b78103" : "#dc4147"
}
