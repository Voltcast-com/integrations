# Voltcast integrations

Official integrations for [Voltcast](https://voltcast.com) — native-resolution
European day-ahead power prices and measured forecasts, by API.

| Integration | What you get |
|---|---|
| [Home Assistant](./home-assistant) ([component code](./custom_components/voltcast)) | Current price, today min/max/mean and next-hour P50 sensors (HACS-compatible) |
| [evcc](./evcc) | Merged upstream tariff template with a 48h forecast for smart EV charging |
| [n8n](./n8n) | Verified community node plus three Home-compatible workflow templates |

**This repo is the home for all Voltcast integrations** — new ones (Grafana
plugin, Zapier/Make, …) land here, not in the product monorepo.

New accounts start with [Home](https://voltcast.com/register?plan=home&utm_source=github&utm_medium=integration-repository&utm_campaign=home-integrations)
at €9/month after a 7-day card-required trial. Home includes one selected
European bidding zone, day-ahead prices, the P50 forecast, 90 days of history,
and one webhook rule. Existing Free accounts remain grandfathered.

SDKs (Python / TypeScript) live at [Voltcast-com/sdk](https://github.com/Voltcast-com/sdk).
API reference: [voltcast.com/docs](https://voltcast.com/docs) ·
Live forecast accuracy: [voltcast.com/accuracy](https://voltcast.com/accuracy) ·
[Home Assistant guide](https://voltcast.com/integrations/home-assistant?utm_source=github&utm_medium=integration-repository&utm_campaign=home-assistant) ·
[evcc guide](https://voltcast.com/integrations/evcc?utm_source=github&utm_medium=integration-repository&utm_campaign=evcc) ·
[n8n workflows](https://voltcast.com/integrations/n8n?utm_source=github&utm_medium=integration-repository&utm_campaign=n8n)
