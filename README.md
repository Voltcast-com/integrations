# Voltcast integrations

Official integrations for [Voltcast](https://voltcast.com) — 15-minute European
day-ahead power prices and probabilistic forecasts, by API.

| Integration | What you get |
|---|---|
| [Home Assistant](./home-assistant) ([component code](./custom_components/voltcast)) | Current price, today min/max/mean and next-hour P50 sensors (HACS-compatible) |
| [evcc](./evcc) | Dynamic grid tariff with 48h forecast for smart EV charging — works with stock evcc today |
| [n8n](./n8n) | Community node `n8n-nodes-voltcast` — prices, forecasts, carbon, imbalance and cheapest-window in your workflows |

**This repo is the home for all Voltcast integrations** — new ones (Grafana
plugin, Zapier/Make, …) land here, not in the product monorepo.

Get a free API key at [voltcast.com/dashboard](https://voltcast.com/dashboard) —
the free tier includes DE-LU prices and a 48h P50 forecast, no card required.

SDKs (Python / TypeScript) live at [Voltcast-com/sdk](https://github.com/Voltcast-com/sdk).
API reference: [voltcast.com/docs](https://voltcast.com/docs) ·
Live forecast accuracy: [voltcast.com/accuracy](https://voltcast.com/accuracy)
