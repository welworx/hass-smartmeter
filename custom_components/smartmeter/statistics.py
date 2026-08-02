"""Long-term statistics import for the Smartmeter integration.

Buckets readings to the hour and calls
homeassistant.components.recorder.statistics.async_add_external_statistics
so consumption/production show up in the HA Energy dashboard, keyed by
metering point so each Zählpunkt (consumption, production/feed-in, ...)
gets its own statistic stream.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, TypedDict

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.models.statistics import StatisticMeanType
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify
from homeassistant.util.unit_conversion import EnergyConverter

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class PointRef(TypedDict):
    """One metering point, as returned by GET /v1/points."""

    provider: str
    id: str


class Reading(TypedDict):
    """One raw reading, as returned by GET /v1/readings."""

    timestamp: str
    value: float


def statistic_id_for(point: PointRef) -> str:
    """Build the external statistic_id for a metering point."""
    slug = slugify(f"{point['provider']}_{point['id']}")
    return f"{DOMAIN}:{slug}"


async def async_last_reading_timestamp(
    hass: HomeAssistant, statistic_id: str
) -> datetime | None:
    """Return the start of the most recently imported hourly bucket, or None."""
    last = await get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, statistic_id, True, {"state", "sum"}
    )
    rows = last.get(statistic_id)
    if not rows:
        return None
    return dt_util.utc_from_timestamp(rows[0]["start"])


async def async_import_statistics(
    hass: HomeAssistant, data: dict[str, tuple[PointRef, list[Reading]]]
) -> None:
    """Bucket readings to the hour and import them as external statistics."""
    for statistic_id, (point, readings) in data.items():
        if not readings:
            continue

        buckets = _bucket_to_hour(readings)

        last = await get_instance(hass).async_add_executor_job(
            get_last_statistics, hass, 1, statistic_id, True, {"state", "sum"}
        )
        rows = last.get(statistic_id)
        running_sum = rows[0]["sum"] - rows[0]["state"] if rows else 0.0

        stats: list[StatisticData] = []
        for hour_start in sorted(buckets):
            running_sum += buckets[hour_start]
            stats.append(
                StatisticData(
                    start=hour_start, state=buckets[hour_start], sum=running_sum
                )
            )

        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=f"{point['provider']} {point['id']}",
            source=DOMAIN,
            statistic_id=statistic_id,
            unit_class=EnergyConverter.UNIT_CLASS,
            unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        )
        async_add_external_statistics(hass, metadata, stats)


def _bucket_to_hour(readings: list[Reading]) -> dict[datetime, float]:
    """Sum reading values (Wh) into hourly buckets, keyed by hour start (UTC)."""
    buckets: dict[datetime, float] = defaultdict(float)
    for reading in readings:
        timestamp = dt_util.parse_datetime(reading["timestamp"])
        hour_start = timestamp.replace(minute=0, second=0, microsecond=0)
        buckets[hour_start] += reading["value"]
    return dict(buckets)
