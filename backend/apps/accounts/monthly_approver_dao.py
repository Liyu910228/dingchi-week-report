from .models import UserMonthlyApprover


def ordered_ids(user_id):
    return list(UserMonthlyApprover.objects.filter(user_id=user_id)
                .order_by("sort_order", "id").values_list("approver_id", flat=True))


def replace(user_id, ids):
    UserMonthlyApprover.objects.filter(user_id=user_id).delete()
    UserMonthlyApprover.objects.bulk_create([
        UserMonthlyApprover(user_id=user_id, approver_id=value, sort_order=index)
        for index, value in enumerate(ids)
    ])


def has_applicants(approver_id):
    return UserMonthlyApprover.objects.filter(approver_id=approver_id).exists()
