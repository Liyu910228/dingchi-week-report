/** 按实际rowspan计算连通的合并组，变更行不参与主记录奇偶计数。 */
export interface BandRow { spans: number[]; kind?: "change" | "empty" }
export function rowBands(rows: BandRow[]): ("base" | "alternate" | "change" | "empty")[] {
  let groupEnd = 0
  let group = -1
  return rows.map((row, index) => {
    if (row.kind === "change" || row.kind === "empty") return row.kind
    if (index >= groupEnd) group++
    groupEnd = Math.max(groupEnd, index + 1, ...row.spans.map(span => span === 0 ? rows.length : index + span))
    return group % 2 === 0 ? "base" : "alternate"
  })
}
