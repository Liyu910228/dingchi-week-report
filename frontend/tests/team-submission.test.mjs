import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"
import ts from "typescript"
const source=readFileSync(new URL("../src/views/dashboard/team/v1/report-submission.ts",import.meta.url),"utf8")
const {outputText}=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}})
const {memberSubmissionStatus,latestMemberUpdates}=await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`)
test('保存不算提交，三种状态分别统计',()=>{
 const reports=[{employeeId:'1',status:'in_progress'},{employeeId:'2',status:'completed'}]
 assert.equal(memberSubmissionStatus(reports,'1'),'pending')
 assert.equal(memberSubmissionStatus(reports,'2'),'submitted')
 assert.equal(memberSubmissionStatus(reports,'3'),'unwritten')
})
test('动态只含成员、按人去重、按更新时间倒序',()=>{
 const rows=[{employeeId:'1',updatedAt:'2026-10-14T10:00:00+08:00'},{employeeId:'2',updatedAt:'2026-10-14T12:00:00+08:00'},{employeeId:'1',updatedAt:'2026-10-14T13:00:00+08:00'},{employeeId:'99',updatedAt:'2026-10-14T14:00:00+08:00'}]
 const result=latestMemberUpdates(rows,[{employeeId:'1'},{employeeId:'2'},{employeeId:'3'}])
 assert.deepEqual(result.map(r=>r.employeeId),['1','2'])
 assert.equal(result[0].updatedAt,rows[2].updatedAt)
})
