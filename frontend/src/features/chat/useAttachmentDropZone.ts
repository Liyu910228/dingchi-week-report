import { ref } from "vue"

export function useAttachmentDropZone(
  addFiles: (files: File[]) => void,
  isDisabled: () => boolean,
) {
  const isDragging = ref(false)
  let dragDepth = 0

  function handlePaste(event: ClipboardEvent) {
    const files = Array.from(event.clipboardData?.files ?? [])
    if (!files.length || isDisabled()) return
    event.preventDefault()
    addFiles(files)
  }

  function handleDragEnter(event: DragEvent) {
    event.preventDefault()
    dragDepth += 1
    if (isDisabled() || !event.dataTransfer?.types.includes("Files")) return
    isDragging.value = true
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault()
    if (event.dataTransfer) event.dataTransfer.dropEffect = isDisabled() ? "none" : "copy"
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault()
    dragDepth = Math.max(0, dragDepth - 1)
    if (dragDepth === 0) isDragging.value = false
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    dragDepth = 0
    isDragging.value = false
    if (isDisabled()) return
    const files = Array.from(event.dataTransfer?.files ?? [])
    if (files.length) addFiles(files)
  }

  return {
    isDragging,
    handlePaste,
    handleDragEnter,
    handleDragOver,
    handleDragLeave,
    handleDrop,
  }
}
