import { request } from "@/shared/api/http"
import type { TodoItem, TodoList } from "./types"
/** GET /v1/todos/?page=1；当前账号及认证角色的未完成待办（响应含role_code），每页10条，返回列表/未读数/实际待审批数；Bearer、X-Trace-ID；400/401/500；新增通用v1契约。 */
export function listTodos(page=1):Promise<TodoList>{return request({method:"GET",url:"/v1/todos/",params:{page}})}
/** POST /v1/todos/{id}/read/；字符串ID、无请求体，幂等标记当前账号及认证角色事项已读，返回事项；不改变业务状态；Bearer/trace，401/404；v1。 */
export function markTodoRead(id:string):Promise<TodoItem>{return request({method:"POST",url:`/v1/todos/${id}/read/`})}
