/** 周报提醒按人员+周期归一，role_code为空表示跨职位；target仅携带周期，审批待办仍保留职位。 */
export interface TodoTarget {kind:string;approval_id?:string;role_code?:string;period_start?:string}
export interface TodoItem {id:string;role_code:string;source:string;title:string;target:TodoTarget;status:string;read_at:string|null;created_at:string;completed_at:string|null}
export interface TodoList {role_code:string;items:TodoItem[];total:number;unread_count:number;pending_approval_count:number;page:number;page_size:number;total_pages:number}
