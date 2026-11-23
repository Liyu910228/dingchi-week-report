"""Static dictionary data shared by role, report and organization features."""

from django.db import models

from apps.core.models.base import SnowflakeIdModel


class DictionaryItem(SnowflakeIdModel):
    """One selectable value in a named static-configuration dictionary."""

    dict_type = models.CharField(max_length=64)
    dict_code = models.CharField(max_length=64)
    dict_name = models.CharField(max_length=128)
    dict_value = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=16, default="active")
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_dictionary"
        constraints = [
            models.UniqueConstraint(
                fields=["dict_type", "dict_code"],
                name="uq_system_dictionary_type_code",
            ),
        ]
        indexes = [
            models.Index(
                fields=["dict_type", "status", "sort_order"],
                name="idx_system_dictionary_lookup",
            ),
        ]
        ordering = ["dict_type", "sort_order", "id"]
