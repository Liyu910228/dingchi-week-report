"""所有已登录用户可用的职位筛选选项。"""

from ..dao import list_role_options


def get_role_options():
    return list_role_options()
