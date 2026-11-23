-- 参数：共享接收人ID；只读、直接授权，已删除用户不提供共享。
SELECT s.owner_id FROM user_report_share s JOIN user_account u ON u.id=s.owner_id
WHERE s.recipient_id=%s AND u.status<>'deleted'
