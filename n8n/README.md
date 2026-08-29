# n8n node — moved to its own repository

The Voltcast n8n community node now lives at
**[Voltcast-com/n8n-nodes-voltcast](https://github.com/Voltcast-com/n8n-nodes-voltcast)**
(the n8n Creator Portal vetting requires the standard scaffold layout at
the repository root, which a monorepo subfolder cannot satisfy).

npm: [`@voltcast/n8n-nodes-voltcast`](https://www.npmjs.com/package/@voltcast/n8n-nodes-voltcast)

The node is listed in n8n's verified integration directory. Three importable,
Home-compatible HTTP workflows are maintained with the product deployment:

- [Cheapest two-hour EV window](https://voltcast.com/integrations/n8n-voltcast-workflow.json)
- [Negative-price alert](https://voltcast.com/integrations/n8n-voltcast-negative-price-alert.json)
- [Battery charge notification](https://voltcast.com/integrations/n8n-voltcast-battery-charge-plan.json)

Each template reads prices or the P50 forecast included with Home and computes
locally in an n8n Code node. They do not call the Pro-only optimization API.
Setup and safety notes:
[voltcast.com/integrations/n8n](https://voltcast.com/integrations/n8n?utm_source=github&utm_medium=integration-repository&utm_campaign=n8n).
