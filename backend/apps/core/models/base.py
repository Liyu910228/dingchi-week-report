"""Abstract model bases shared by business applications."""

from django.db import models

from apps.core.services.id_generator import generate_primary_id


class SnowflakeIdModel(models.Model):
    """Provide the only supported primary-key field for new business models."""

    id = models.BigIntegerField(
        primary_key=True,
        default=generate_primary_id,
        editable=False,
    )

    class Meta:
        abstract = True
