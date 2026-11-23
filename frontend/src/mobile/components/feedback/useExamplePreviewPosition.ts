import { nextTick, onBeforeUnmount, ref, watch, type Ref } from "vue"

export function useExamplePreviewPosition(
  isOpen: Ref<boolean>,
  trigger: Ref<HTMLButtonElement | null>,
  panel: Ref<HTMLDivElement | null>,
) {
  const position = ref({ left: "16px", top: "16px", width: "720px", maxHeight: "calc(100dvh - 32px)" })
  const isPositioned = ref(false)
  let observer: ResizeObserver | undefined
  let frame = 0

  function updatePosition() {
    if (!isOpen.value || !trigger.value || !panel.value) return
    const viewport = window.visualViewport
    const leftEdge = viewport?.offsetLeft || 0
    const topEdge = viewport?.offsetTop || 0
    const viewportWidth = viewport?.width || document.documentElement.clientWidth
    const viewportHeight = viewport?.height || window.innerHeight
    const margin = 16
    const gap = 8
    const width = Math.max(1, Math.min(720, viewportWidth - margin * 2))
    const maxHeight = Math.max(1, Math.min(760, viewportHeight - margin * 2))
    const height = Math.min(panel.value.offsetHeight, maxHeight)
    const anchor = trigger.value.getBoundingClientRect()
    if (anchor.bottom < topEdge || anchor.top > topEdge + viewportHeight) {
      isOpen.value = false
      return
    }
    const minLeft = leftEdge + margin
    const maxLeft = leftEdge + viewportWidth - margin - width
    const minTop = topEdge + margin
    const maxTop = topEdge + viewportHeight - margin - height
    let left = anchor.right - width
    let top = anchor.top + anchor.height / 2 - height / 2
    if (anchor.left - gap - width >= minLeft) {
      left = anchor.left - gap - width
    } else if (anchor.right + gap + width <= leftEdge + viewportWidth - margin) {
      left = anchor.right + gap
    } else if (anchor.bottom + gap + height <= topEdge + viewportHeight - margin) {
      top = anchor.bottom + gap
    } else if (anchor.top - gap - height >= minTop) {
      top = anchor.top - gap - height
    }
    position.value = {
      left: `${Math.max(minLeft, Math.min(left, maxLeft))}px`,
      top: `${Math.max(minTop, Math.min(top, maxTop))}px`,
      width: `${width}px`,
      maxHeight: `${maxHeight}px`,
    }
    isPositioned.value = true
  }

  function schedulePosition() {
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(updatePosition)
  }

  function cleanup() {
    cancelAnimationFrame(frame)
    observer?.disconnect()
    window.removeEventListener("resize", schedulePosition)
    window.removeEventListener("scroll", schedulePosition, true)
    window.visualViewport?.removeEventListener("resize", schedulePosition)
    window.visualViewport?.removeEventListener("scroll", schedulePosition)
  }

  watch(isOpen, async (open) => {
    cleanup()
    isPositioned.value = false
    if (!open) return
    await nextTick()
    if (!isOpen.value) return
    updatePosition()
    observer = new ResizeObserver(schedulePosition)
    if (panel.value) observer.observe(panel.value)
    if (trigger.value) observer.observe(trigger.value)
    window.addEventListener("resize", schedulePosition)
    window.addEventListener("scroll", schedulePosition, true)
    window.visualViewport?.addEventListener("resize", schedulePosition)
    window.visualViewport?.addEventListener("scroll", schedulePosition)
  })

  onBeforeUnmount(cleanup)
  return { position, isPositioned }
}
