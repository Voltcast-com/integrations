# Voltcast — Home Assistant integration

15-minute European day-ahead electricity prices and P50 forecasts as Home Assistant
sensors, straight from the [Voltcast API](https://voltcast.com/docs).

## Entities

- `sensor.<zone>_current_price` — the price of the running 15-minute period (EUR/MWh)
- `sensor.<zone>_today_min` / `_today_max` / `_today_mean`
- `sensor.<zone>_forecast_p50_next_hour` — with the full 48h curve as an attribute
  (perfect for template-driven automations and ApexCharts cards)
- `sensor.<zone>_next_recommended_window` — timestamp of the best upcoming
  cost window, with its end and user-entered bill context as attributes;
  experimental historical-profile modes also expose their estimate and status
- `binary_sensor.<zone>_charge_now` — on only while that recommended window is active
- `binary_sensor.<zone>_negative_price_incoming` — on when the modeled
  probability of a negative price reaches 50% in the next 24 hours

## Install

**HACS (recommended):** add `https://github.com/Voltcast-com/integrations` as a custom repository
(category: Integration), install "Voltcast", restart, then add the integration via
Settings → Devices & Services → Add Integration → Voltcast.

**Manual:** copy this repo's `custom_components/voltcast/` into your `config/custom_components/`.

New accounts start with
[Voltcast Home](https://voltcast.com/register?plan=home&utm_source=github&utm_medium=home-assistant-integration&utm_campaign=home-assistant&task=home-assistant):
one selected European bidding zone, native-resolution prices, the P50
forecast, 90 days of history, 14-day negative-price risk, tariff-aware
optimization, unlimited webhooks, SSE, and these action entities for €9/month
after a 7-day card-required trial. Existing Free accounts remain grandfathered
without the Home action upgrade.

During setup—or later under Settings → Devices & Services → Voltcast →
Configure—choose the action-window duration and objective:

- **Cost:** lowest user-adjusted import price (production default).
- **Carbon:** experimental trailing historical local-time production-profile
  heuristic—not a forward carbon forecast.
- **Balanced:** experimental equal-weight cost + historical-profile heuristic.

You can enter variable grid fee, supplier markup, and VAT from your bill.
These values stay in Home Assistant and are sent only with each optimization
request. Fixed monthly charges, export remuneration, time-varying network
charges, and tiered taxes are not modeled. Flat adders do not change interval
ranking. The optional carbon value is not a weather-conditioned forecast,
flow-traced consumption intensity, marginal-emissions estimate, or evidence
that a schedule reduces emissions.

The maintained step-by-step guide is at
[voltcast.com/integrations/home-assistant](https://voltcast.com/integrations/home-assistant?utm_source=github&utm_medium=home-assistant-integration&utm_campaign=home-assistant).

## Example automation

```yaml
automation:
  - alias: "Notify when Voltcast says charge"
    trigger:
      - platform: state
        entity_id: binary_sensor.de_lu_charge_now
        to: "on"
    action:
      - service: notify.notify
        data:
          message: >
            Recommended charging window started.
            It ends at
            {{ state_attr('binary_sensor.de_lu_charge_now', 'window_end') }}.
```

Start notification-only and inspect the timestamps, objective, bill inputs,
source basis, and interval-resolution attributes. Add physical-control actions
only after applying your device's own SoC, temperature, current, charger, and
manufacturer safety limits and testing the automation.
