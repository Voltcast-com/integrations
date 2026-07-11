# n8n-nodes-voltcast

n8n community node for [Voltcast](https://voltcast.com) — European electricity
prices, forecasts, carbon intensity and optimization.

Operations: Get Prices · Get Forecast · Get Carbon Intensity · Get Imbalance
Prices · Find Cheapest Window. Declarative-style node (no custom execute code).

## Install (self-hosted n8n)

Settings → Community Nodes → Install → `n8n-nodes-voltcast`

Add a **Voltcast API** credential with an API key from
[voltcast.com/dashboard](https://voltcast.com/dashboard) (free tier available).

## No node? Use plain HTTP

Until the node is published/approved you can call the API with n8n's HTTP
Request node — import the ready-made workflow from
[voltcast.com/integrations/n8n-voltcast-workflow.json](https://voltcast.com/integrations/n8n-voltcast-workflow.json).

## Publish (maintainers)

```bash
npm run build && npm publish --access public
```

Then submit for n8n community-node verification. This package lives in the
Voltcast monorepo under `integrations/n8n/` and mirrors to
github.com/Voltcast-com/integrations.

Add `tsconfig.json` + `nodes/Voltcast/voltcast.svg` (logo) before first publish.
