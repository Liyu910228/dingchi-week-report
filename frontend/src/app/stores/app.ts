import { defineStore } from "pinia"
import { ref } from "vue"

export const useAppStore = defineStore("app", () => {
  const theme = ref<"light" | "dark">(
    localStorage.getItem("theme") === "dark" ? "dark" : "light",
  )

  function applyTheme() {
    document.documentElement.dataset.theme = theme.value
    localStorage.setItem("theme", theme.value)
  }

  function toggleTheme() {
    theme.value = theme.value === "light" ? "dark" : "light"
    applyTheme()
  }

  applyTheme()

  return { theme, toggleTheme }
})
