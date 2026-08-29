# Voltcast tariff for evcc

[evcc](https://evcc.io) includes the Voltcast tariff template upstream after
[evcc-io/evcc#31848](https://github.com/evcc-io/evcc/pull/31848) merged. Use
the built-in template where available; the custom recipe below remains a
transparent fallback.

## Built-in template

Follow the fields exposed by your installed evcc version for
`template: voltcast`. Use the same bidding-zone code that you selected on your
Voltcast Home account and provide the API key from the dashboard.

The current end-to-end guide, with source attribution and a safe notification-first
rollout, is at
[voltcast.com/integrations/evcc](https://voltcast.com/integrations/evcc?utm_source=github&utm_medium=integration-repository&utm_campaign=evcc).

## Custom fallback (evcc ≥ 0.200)

Add to `evcc.yaml`:

```yaml
tariffs:
  currency: EUR
  grid:
    type: custom
    forecast:
      source: http
      uri: https://voltcast.com/api/v1/forecasts/DE-LU?horizon=48h
      headers:
        - Authorization: Bearer YOUR_API_KEY
      jq: |
        [ .data[] | { start: .target_start,
                      end: (.target_start | fromdate + 900 | todate),
                      value: (.p50 / 1000) } ]
```

Notes:

- `p50 / 1000` converts EUR/MWh → EUR/kWh, which evcc expects.
- For **published prices instead of forecasts** swap the `uri` to
  `https://voltcast.com/api/v1/prices/DE-LU` and `jq` to
  `[ .data[] | { start: .delivery_start, end: .delivery_end, value: (.price_eur_mwh / 1000) } ]`.
- Add your grid fees/taxes via evcc's `charges` and `tax` fields as usual.

evcc's smart-charging then plans charging into the cheapest 15-minute slots
automatically. The same pattern works for `tariffs: feedin`.

## Upstream template PR

The exact template merged upstream on 2026-07-16. `evcc-template-voltcast.yaml`
is retained here as a versioned reference, but the evcc repository is
authoritative for the current built-in fields.
