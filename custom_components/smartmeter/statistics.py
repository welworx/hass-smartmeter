"""Long-term statistics import for the Smartmeter integration.

Will bucket readings to the hour and call
homeassistant.components.recorder.statistics.async_add_external_statistics
so consumption/production show up in the HA Energy dashboard, keyed by
metering point so each Zählpunkt (consumption, production/feed-in, ...)
gets its own statistic stream.

Not yet implemented.
"""
