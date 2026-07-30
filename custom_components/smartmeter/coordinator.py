"""DataUpdateCoordinator for the Smartmeter integration.

Will poll GET /v1/readings?point=<id>&since=<last statistic timestamp> on
the configured smartmeter-fetch instance, resuming from the last
successfully imported point rather than from a fixed "yesterday" offset —
upstream grid operator portals can publish data several days late.

Not yet implemented.
"""
