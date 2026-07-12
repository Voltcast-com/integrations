# Home Assistant CORE submission plan — Voltcast

Why core, not just HACS: verified distribution gap is ~10–15× (co2signal in
core: 63,040 reporting installs vs nordpool on HACS: 4,383, of 516k reporting).
The core review pipeline takes months and is queue-bound — everything below is
ready so the clock starts NOW.

## What's in this folder

- `voltcast/` — the integration, written to core standards (2026):
  - config flow with live key/zone validation + typed error mapping
  - `DataUpdateCoordinator` via `entry.runtime_data` (modern pattern)
  - library-based I/O: [`aiovoltcast`](https://github.com/Voltcast-com/sdk/tree/main/python-async)
    (aiohttp, session-injected, typed) — core requires a published PyPI lib
  - `has_entity_name`, translation keys, device grouped per zone, attribution
  - `quality_scale: bronze` target for first submission
- `tests/` — config-flow tests in core test style

## Operator steps (in order)

1. **Publish `aiovoltcast` to PyPI** (one command, kit in the sdk repo):
   `cd sdk/python-async && python -m build && twine upload dist/*`
   (Use the same PyPI account as `voltcast`; add a Trusted Publisher later.)
2. **Fork + branch**: fork `home-assistant/core`, create `voltcast` branch,
   copy `voltcast/` to `homeassistant/components/voltcast/` and `tests/` to
   `tests/components/voltcast/`.
3. **Scaffold the boring parts** inside the core checkout:
   `python -m script.scaffold config_flow` artifacts we already have; then run
   `python -m script.hassfest` and `pytest tests/components/voltcast` until green.
4. **Brands PR**: submit logo/icon to `home-assistant/brands` (required
   before/alongside the core PR). Assets: voltcast.com favicon SVG set.
5. **Docs PR**: `home-assistant.io` page — source draft in this folder's
   `docs-page.md` (create from the README quickstart).
6. **Open the core PR** with the quality-scale checklist filled; expect
   several review rounds over weeks-to-months. Respond fast — review latency
   is the whole timeline.
7. After merge: keep the HACS `custom_components/voltcast` version published
   for early adopters until the core version ships in a release, then mark it
   deprecated with a migration note.

## Quality-scale ladder

- Bronze (submission target): config-flow tests ✓, typed coordinator ✓,
  runtime_data ✓, docs, brands.
- Silver (fast follow): reauth flow on `ConfigEntryAuthFailed` (raised
  already), entity availability handling, diagnostics.
