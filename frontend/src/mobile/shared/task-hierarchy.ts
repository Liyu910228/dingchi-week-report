export interface ContentGroup<T> { key:string; rows:T[] }
export interface TaskGroup<T> { key:string; row:T; contents:ContentGroup<T>[] }
/** Group by persisted identities, never by equal text. Preserve first appearance and record order. */
export function taskHierarchy<T>(rows:readonly T[], taskKey:(row:T)=>string, contentKey:(row:T)=>string):TaskGroup<T>[] {
 const tasks=new Map<string,TaskGroup<T>>()
 for(const row of rows){
  const key=taskKey(row)
  let group=tasks.get(key)
  if(!group){group={key,row,contents:[]};tasks.set(key,group)}
  const childKey=contentKey(row)
  let content=group.contents.find(item=>item.key===childKey)
  if(!content){content={key:childKey,rows:[]};group.contents.push(content)}
  content.rows.push(row)
 }
 return [...tasks.values()]
}
