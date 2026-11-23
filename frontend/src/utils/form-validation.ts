type FormField = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement

function isFormField(value: EventTarget | null): value is FormField {
  return value instanceof HTMLInputElement || value instanceof HTMLTextAreaElement
    || value instanceof HTMLSelectElement
}

/** 清理普通输入项的临时校验信息；自定义选择控件自行维护其选择有效性。 */
export function clearFieldValidity(event: Event) {
  const field = event.target
  if (isFormField(field) && (field.required
    || (!(field instanceof HTMLSelectElement) && field.maxLength >= 0))) {
    field.setCustomValidity("")
  }
}

/** 两种确认操作统一使用浏览器字段浮动提示，纯空白也视为未填写。 */
export function reportFormValidity(form: HTMLFormElement | null): boolean {
  if (!form) return false
  const fields = Array.from(form.querySelectorAll<FormField>("input, textarea, select"))
  for (const field of fields) {
    if (!field.willValidate) continue
    const maxLength = field instanceof HTMLSelectElement ? -1 : field.maxLength
    if (!field.required && maxLength < 0) continue
    const blank = field.required && Boolean(field.value) && !field.value.trim()
    const tooLong = maxLength >= 0 && field.value.length > maxLength
    field.setCustomValidity(blank ? "请填写此字段。" : tooLong ? `最多填写 ${maxLength} 个字符。` : "")
  }
  const invalid = fields.find((field) => field.willValidate && !field.validity.valid)
  if (invalid) {
    invalid.scrollIntoView({ block: "nearest" })
    invalid.focus({ preventScroll: true })
  }
  return form.reportValidity()
}

/** 草稿仅检查长度、范围和格式，必填非空在周报提交时由服务端统一检查。 */
export function reportDraftValidity(form: HTMLFormElement | null): boolean {
  if (!form) return false
  const fields = Array.from(form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>("input, textarea, select"))
  for (const field of fields) {
    const maxLength = field instanceof HTMLSelectElement ? -1 : field.maxLength
    const tooLong = maxLength >= 0 && field.value.length > maxLength
    field.setCustomValidity(tooLong ? `最多填写 ${maxLength} 个字符。` : "")
    const validity = field.validity
    if (tooLong || validity.badInput || validity.typeMismatch || validity.rangeOverflow || validity.rangeUnderflow || validity.stepMismatch) {
      field.scrollIntoView({ block: "nearest" }); field.focus(); field.reportValidity(); return false
    }
  }
  return true
}
