import type { TeamMemberSummary, TeamReportEntry } from "./types"
export function memberSubmissionStatus(reports: TeamReportEntry[], employeeId: string): "unwritten" | "pending" | "submitted" {
  const own=reports.filter(report=>report.employeeId===employeeId)
  if(!own.length)return "unwritten"
  return own.every(report=>report.status==='completed') ? "submitted" : "pending"
}
export function latestMemberUpdates(reports: TeamReportEntry[], members: TeamMemberSummary[]) {
  const ids=new Set(members.map(member=>member.employeeId)),latest=new Map<string,TeamReportEntry>()
  for(const report of reports){
    if(!ids.has(report.employeeId) || !Number.isFinite(Date.parse(report.updatedAt)))continue
    const previous=latest.get(report.employeeId)
    if(!previous || Date.parse(report.updatedAt)>Date.parse(previous.updatedAt))latest.set(report.employeeId,report)
  }
  return [...latest.values()].sort((a,b)=>Date.parse(b.updatedAt)-Date.parse(a.updatedAt) || a.employeeId.localeCompare(b.employeeId))
}
