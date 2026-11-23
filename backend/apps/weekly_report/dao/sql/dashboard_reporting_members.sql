-- 查询有有效周报填写职位的成员；参数为可见员工ID列表。
SELECT u.id AS employee_id, u.display_name AS employee_name,
               u.group_id, COALESCE(g.group_name, '未分组') AS group_name,
               COALESCE(
                   GROUP_CONCAT(DISTINCT r.role_code ORDER BY r.sort_order SEPARATOR ','),
                   ''
               ) AS role_code,
               COALESCE(
                   GROUP_CONCAT(DISTINCT r.role_name ORDER BY r.sort_order SEPARATOR '、'),
                   '团队成员'
               ) AS role_name
        FROM user_account u
        LEFT JOIN organization_group g ON g.id = u.group_id
        INNER JOIN user_role ur ON ur.user_id = u.id AND ur.status = 'active'
        INNER JOIN role r ON r.id = ur.role_id AND r.status = 'active'
            AND r.scope <> 'all' AND COALESCE(r.report_template_code, '') <> ''
        WHERE u.status = 'active' AND u.id IN ({employee_placeholders})
        GROUP BY u.id, u.display_name, u.group_id, g.group_name, u.employee_no
        ORDER BY u.employee_no, u.id
