"""Logical organization models.

The project intentionally does not declare Django ForeignKey fields.  All
relationships are logical IDs so organizational data can be synchronized from
an external HR system without database-level coupling.
"""

from django.db import models

from apps.core.models.base import SnowflakeIdModel
from apps.core.security.fields import EncryptedPasswordField


class OrganizationGroup(SnowflakeIdModel):
    group_code = models.CharField(max_length=64, unique=True)
    group_name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, default="")
    parent_group_id = models.BigIntegerField(null=True, blank=True)
    is_system = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organization_group"
        ordering = ["group_code"]


class Role(SnowflakeIdModel):
    role_code = models.CharField(max_length=64)
    deletion_key = models.BigIntegerField(default=0, editable=False)
    role_name = models.CharField(max_length=128)
    scope = models.CharField(max_length=16, default="self")
    description = models.CharField(max_length=255, blank=True, default="")
    # 角色可以暂不绑定模板；填写或查看周报时由业务层明确提示配置模板，
    # 不再隐式落到已经废弃的通用周报页面。
    report_template_code = models.CharField(max_length=64, blank=True, default="")
    role_group_code = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="角色所属分组编码，逻辑关联 organization_group.group_code。",
    )
    status = models.CharField(max_length=16, default="active")
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "role"
        ordering = ["deletion_key", "sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["role_code", "deletion_key"], name="uq_role_code_live"),
        ]


class UserAccount(SnowflakeIdModel):
    username = models.CharField(max_length=64)
    deletion_key = models.BigIntegerField(default=0, editable=False)
    employee_no = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=128)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    password_ciphertext = EncryptedPasswordField()
    manager_id = models.BigIntegerField(null=True, blank=True)
    group_id = models.BigIntegerField(null=True, blank=True)
    avatar_color = models.CharField(max_length=16, default="#2f80ed")
    status = models.CharField(max_length=16, default="active")
    is_super = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_account"
        ordering = ["employee_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["username", "deletion_key"], name="uq_user_username_live"
            ),
        ]


class UserRole(SnowflakeIdModel):
    user_id = models.BigIntegerField()
    role_id = models.BigIntegerField()
    is_default = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_role"
        constraints = [
            models.UniqueConstraint(fields=["user_id", "role_id"], name="uq_user_role_pair"),
        ]


class UserManager(SnowflakeIdModel):
    user_id = models.BigIntegerField()
    manager_id = models.BigIntegerField()
    sort_order = models.PositiveIntegerField()

    class Meta:
        db_table = "user_manager"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["user_id", "manager_id"], name="uq_user_manager_pair"),
            models.UniqueConstraint(fields=["user_id", "sort_order"], name="uq_user_manager_order"),
        ]


class UserGroupMembership(SnowflakeIdModel):
    """Optional multi-group membership while UserAccount keeps a primary group."""

    user_id = models.BigIntegerField()
    group_id = models.BigIntegerField()
    is_primary = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_group_membership"
        constraints = [
            models.UniqueConstraint(fields=["user_id", "group_id"], name="uq_user_group_pair"),
        ]


class UserMonthlyApprover(SnowflakeIdModel):
    """月报审批配置独立于组织上下级，顺序为选择顺序。"""

    user_id = models.BigIntegerField()
    approver_id = models.BigIntegerField()
    sort_order = models.PositiveIntegerField()

    class Meta:
        db_table = "user_monthly_approver"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "approver_id"], name="uq_monthly_approver_pair"
            ),
            models.UniqueConstraint(
                fields=["user_id", "sort_order"], name="uq_monthly_approver_order"
            ),
        ]


class RoleCustomer(SnowflakeIdModel):
    role_id = models.BigIntegerField()
    customer_id = models.BigIntegerField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "role_customer"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["role_id", "customer_id"], name="uq_role_customer")
        ]


class UserRoleCustomer(SnowflakeIdModel):
    user_id = models.BigIntegerField()
    role_id = models.BigIntegerField()
    customer_id = models.BigIntegerField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "user_role_customer"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "role_id", "customer_id"], name="uq_user_role_customer"
            )
        ]


class UserReportShare(SnowflakeIdModel):
    """owner将全部月度计划与周报只读共享给recipient，非传递授权。"""

    owner_id = models.BigIntegerField()
    recipient_id = models.BigIntegerField()

    class Meta:
        db_table = "user_report_share"
        constraints = [
            models.UniqueConstraint(
                fields=["owner_id", "recipient_id"], name="uq_user_report_share"
            ),
        ]
        indexes = [models.Index(fields=["recipient_id"], name="idx_report_share_recipient")]
