/** Explicit /mobile URLs always win; device detection does not depend on window width. */
export function isMobileDevice(): boolean {
  return /Android|iPhone|iPod|Windows Phone|Mobile/i.test(navigator.userAgent)
}
export function mobilePath(path: string): string {
  return path === "/" ? "/mobile" : `/mobile${path}`
}
