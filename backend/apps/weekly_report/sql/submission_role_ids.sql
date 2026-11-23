-- 用途：按职位筛选主单；参数role_code；表名来自固定白名单。
SELECT submission_id FROM {part_table} WHERE role_code = %s AND submission_id IS NOT NULL AND status <> 'deleted'
