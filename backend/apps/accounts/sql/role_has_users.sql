-- 参数：职位ID；已解除的inactive关联不属于挂载用户。
SELECT 1 FROM user_role ur JOIN user_account u ON u.id = ur.user_id
WHERE ur.role_id = %s AND ur.status = 'active' AND u.status <> 'deleted' LIMIT 1
