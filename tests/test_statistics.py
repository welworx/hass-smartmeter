"""Tests for the Smartmeter statistics import."""

from datetime import UTC, datetime

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import get_last_statistics
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.smartmeter.statistics import (
    async_import_statistics,
    async_last_reading_timestamp,
    statistic_id_for,
)

POINT = {"provider": "evn", "id": "AT001"}
STATISTIC_ID = "smartmeter:evn_at001"


def test_statistic_id_for_slugs_provider_and_id():
    assert (
        statistic_id_for({"provider": "EVN", "id": "AT-001"}) == "smartmeter:evn_at_001"
    )


async def test_last_reading_timestamp_none_when_unimported(recorder_mock, hass):
    assert await async_last_reading_timestamp(hass, STATISTIC_ID) is None


async def test_import_statistics_first_run(recorder_mock, hass):
    readings = [
        {"timestamp": "2026-01-01T00:15:00Z", "value": 100.0},
        {"timestamp": "2026-01-01T00:45:00Z", "value": 50.0},
        {"timestamp": "2026-01-01T01:15:00Z", "value": 20.0},
    ]

    await async_import_statistics(hass, {STATISTIC_ID: (POINT, readings)})
    await async_wait_recording_done(hass)

    last = await async_last_reading_timestamp(hass, STATISTIC_ID)
    assert last == datetime(2026, 1, 1, 1, tzinfo=UTC)


async def test_import_statistics_recomputes_last_bucket_on_correction(
    recorder_mock, hass
):
    first = [{"timestamp": "2026-01-01T00:15:00Z", "value": 100.0}]
    await async_import_statistics(hass, {STATISTIC_ID: (POINT, first)})
    await async_wait_recording_done(hass)

    # A poll that re-requests "since" the last bucket's own start will
    # naturally re-include that hour's readings — simulating a late
    # correction landing in an hour already imported.
    corrected = [
        {"timestamp": "2026-01-01T00:15:00Z", "value": 100.0},
        {"timestamp": "2026-01-01T00:45:00Z", "value": 30.0},
        {"timestamp": "2026-01-01T01:15:00Z", "value": 20.0},
    ]
    await async_import_statistics(hass, {STATISTIC_ID: (POINT, corrected)})
    await async_wait_recording_done(hass)

    result = await get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 2, STATISTIC_ID, True, {"state", "sum"}
    )
    rows = sorted(result[STATISTIC_ID], key=lambda r: r["start"])
    assert [r["state"] for r in rows] == [130.0, 20.0]
    assert [r["sum"] for r in rows] == [130.0, 150.0]


async def test_import_statistics_skips_point_with_no_new_readings(recorder_mock, hass):
    await async_import_statistics(hass, {STATISTIC_ID: (POINT, [])})
    await async_wait_recording_done(hass)

    assert await async_last_reading_timestamp(hass, STATISTIC_ID) is None


async def test_import_statistics_isolates_broken_point(recorder_mock, hass):
    broken_point = {"provider": "evn", "id": "AT002"}
    broken_statistic_id = "smartmeter:evn_at002"

    healthy_readings = [
        {"timestamp": "2026-01-01T00:15:00Z", "value": 100.0},
    ]

    # Missing "value" key raises a KeyError during bucketing — a per-point
    # failure Fix 4's try/except must isolate from the healthy point below.
    broken_readings = [{"timestamp": "2026-01-01T00:15:00Z"}]

    await async_import_statistics(
        hass,
        {
            broken_statistic_id: (broken_point, broken_readings),
            STATISTIC_ID: (POINT, healthy_readings),
        },
    )
    await async_wait_recording_done(hass)

    assert await async_last_reading_timestamp(hass, broken_statistic_id) is None
    assert await async_last_reading_timestamp(hass, STATISTIC_ID) == datetime(
        2026, 1, 1, 0, tzinfo=UTC
    )


async def test_bucket_to_hour_skips_unparseable_timestamp(recorder_mock, hass):
    readings = [
        {"timestamp": "not-a-timestamp", "value": 999.0},
        {"timestamp": "2026-01-01T00:15:00Z", "value": 100.0},
        {"timestamp": "2026-01-01T00:45:00Z", "value": 50.0},
    ]

    await async_import_statistics(hass, {STATISTIC_ID: (POINT, readings)})
    await async_wait_recording_done(hass)

    result = await get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, STATISTIC_ID, True, {"state", "sum"}
    )
    rows = result[STATISTIC_ID]
    assert rows[0]["state"] == 150.0
    assert rows[0]["sum"] == 150.0
