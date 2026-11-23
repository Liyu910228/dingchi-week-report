"""Configured primary-key ID generation."""

from django.conf import settings

from utils.snowflake import SnowflakeIdGenerator

_generator = SnowflakeIdGenerator(
    epoch_ms=settings.SNOWFLAKE_EPOCH_MS,
    worker_id=settings.SNOWFLAKE_WORKER_ID,
    datacenter_id=settings.SNOWFLAKE_DATACENTER_ID,
)


def generate_primary_id() -> int:
    """Generate the single primary-key format used by all new models."""
    return _generator.next_id()
