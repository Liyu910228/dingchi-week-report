/** Immediate task-action hints, rendered outside scrolling table containers. */
export function installTaskTooltips() {
  const tip = document.createElement("div")
  tip.className = "task-action-tooltip"
  tip.setAttribute("role", "tooltip")
  tip.id = "task-action-tooltip"
  tip.setAttribute("popover", "manual")
  let active: HTMLElement | null = null
  function hide() {
    active?.removeAttribute("aria-describedby")
    active = null
    if (tip.matches(":popover-open")) tip.hidePopover()
    tip.remove()
  }
  function show(event: Event) {
    const button = (event.target as Element)?.closest<HTMLElement>("[data-task-tip]")
    if (!button || button === active) return
    hide()
    active = button
    tip.textContent = button.dataset.taskTip || ""
    document.body.append(tip)
    tip.showPopover()
    button.setAttribute("aria-describedby", tip.id)
    const rect = button.getBoundingClientRect()
    tip.style.left = `${Math.max(8, Math.min(innerWidth - tip.offsetWidth - 8, rect.left + rect.width / 2 - tip.offsetWidth / 2))}px`
    tip.style.top = `${rect.top > tip.offsetHeight + 12 ? rect.top - tip.offsetHeight - 8 : rect.bottom + 8}px`
  }
  document.addEventListener("pointerover", show, true)
  document.addEventListener("focusin", show, true)
  document.addEventListener("pointerout", event => {
    if (active && !active.contains((event as PointerEvent).relatedTarget as Node | null)) hide()
  })
  document.addEventListener("focusout", hide)
  document.addEventListener("scroll", hide, true)
  document.addEventListener("pointerdown", hide)
  window.addEventListener("resize", hide)
}
