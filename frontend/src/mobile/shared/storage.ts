/** Mobile UI preferences never overwrite desktop preferences. Auth tokens remain shared. */
export const mobileStorage = {
  getItem: (key: string) => window.localStorage.getItem(`mobile:${key}`),
  setItem: (key: string, value: string) => window.localStorage.setItem(`mobile:${key}`, value),
  removeItem: (key: string) => window.localStorage.removeItem(`mobile:${key}`),
}
