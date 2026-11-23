-- 月度主单状态筛选同时匹配其变更；参数为两次status，全部绑定。
SELECT submission_id FROM report_submission_change WHERE status = %s
UNION
SELECT p.submission_id FROM monthly_plan p
JOIN monthly_plan_change c ON c.monthly_plan_id = p.id
WHERE c.status = %s AND p.submission_id IS NOT NULL AND p.status <> 'deleted'
