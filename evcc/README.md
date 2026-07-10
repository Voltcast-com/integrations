# Voltcast — evcc tariff integration

[evcc](https://evcc.io) can consume Voltcast as a dynamic **grid tariff with forecast**
today via its built-in `custom` tariff type — no evcc code changes needed. A native
`template: voltcast` upstream PR is prepared separately (see below).

## Working recipe (evcc ≥ 0.200)

Add to your `evcc.yaml` (key from [voltcast.com/dashboard](https://voltcast.com/dashboard)):

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

The prepared Go template for `evcc-io/evcc` (`templates/definition/tariff/voltcast.yaml`)
lives in this folder as `evcc-template-voltcast.yaml` — submit it upstream once the
public launch happens so users get `type: template, template: voltcast` out of the box.
