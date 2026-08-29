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

New accounts start with
[Voltcast Home](https://voltcast.com/register?plan=home&utm_source=github&utm_medium=home-assistant-integration&utm_campaign=home-assistant&task=home-assistant):
one selected European bidding zone, native-resolution prices, the 48h P50
forecast, 90 days of history, and one webhook rule for €9/month after a
7-day card-required trial. Existing Free accounts remain grandfathered.

The maintained step-by-step guide is at
[voltcast.com/integrations/home-assistant](https://voltcast.com/integrations/home-assistant?utm_source=github&utm_medium=home-assistant-integration&utm_campaign=home-assistant).

## Example automation

```yaml
automation:
  - alias: "Charge when power is cheap"
    trigger:
      - platform: numeric_state
        entity_id: sensor.de_lu_current_price
        below: 20
    action:
      - service: notify.notify
        data:
          message: "Voltcast price is below 20 EUR/MWh"
```

Start notification-only and inspect the source timestamps and interval
resolution. Add physical-control actions only after applying your device's own
safety limits and testing the automation.
