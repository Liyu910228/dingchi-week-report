-- 参数：姓名模糊匹配；人员授权过滤由主查询保留。
SELECT id FROM user_account WHERE display_name LIKE %s AND status<>'deleted'
