import time

from utils.snowflake import SnowflakeIdGenerator


def test_snowflake_ids_are_unique_and_monotonic() -> None:
    generator = SnowflakeIdGenerator(
        epoch_ms=int(time.time() * 1000) - 1_000,
        worker_id=1,
        datacenter_id=2,
    )

    identifiers = [generator.next_id() for _ in range(500)]

    assert len(set(identifiers)) == len(identifiers)
    assert identifiers == sorted(identifiers)
    assert all(identifier > 0 for identifier in identifiers)
