-- 返回主流程或未删除子流程匹配指定状态的主流程ID；参数：主状态、子状态。
SELECT id FROM monthly_plan WHERE status = %s
UNION
SELECT monthly_plan_id FROM monthly_plan_change WHERE status = %s AND status <> 'deleted'
