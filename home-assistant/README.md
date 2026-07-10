# Voltcast — Home Assistant integration

15-minute European day-ahead electricity prices and P50 forecasts as Home Assistant
sensors, straight from the [Voltcast API](https://voltcast.com/docs).

## Entities

- `sensor.<zone>_current_price` — the price of the running 15-minute period (EUR/MWh)
- `sensor.<zone>_today_min` / `_today_max` / `_today_mean`
- `sensor.<zone>_forecast_p50_next_hour` — with the full 48h curve as an attribute
  (perfect for template-driven automations and ApexCharts cards)

## Install

**HACS (recommended):** add `https://github.com/Voltcast-com/integrations` as a custom repository
(category: Integration), install "Voltcast", restart, then add the integration via
Settings → Devices & Services → Add Integration → Voltcast.

**Manual:** copy this repo's `custom_components/voltcast/` into your `config/custom_components/`.

You'll need a free API key from [voltcast.com/dashboard](https://voltcast.com/dashboard)
(the free tier covers DE-LU with a 48h P50 forecast).

## Example automation

```yaml
automation:
  - alias: "Charge when power is cheap"
    trigger:
      - platform: numeric_state
        entity_id: sensor.de_lu_current_price
        below: 20
    action:
      - service: switch.turn_on
        target: { entity_id: switch.ev_charger }
```
