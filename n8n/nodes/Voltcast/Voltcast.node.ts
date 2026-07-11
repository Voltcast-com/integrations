import type { INodeType, INodeTypeDescription } from 'n8n-workflow';

export class Voltcast implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Voltcast',
		name: 'voltcast',
		icon: 'file:voltcast.svg',
		group: ['input'],
		version: 1,
		subtitle: '={{$parameter["operation"] + ": " + $parameter["zone"]}}',
		description: 'European electricity prices, forecasts, carbon intensity and optimization',
		defaults: { name: 'Voltcast' },
		inputs: ['main'],
		outputs: ['main'],
		credentials: [{ name: 'voltcastApi', required: true }],
		requestDefaults: {
			baseURL: 'https://voltcast.com/api/v1',
			headers: { Accept: 'application/json' },
		},
		properties: [
			{
				displayName: 'Operation',
				name: 'operation',
				type: 'options',
				noDataExpression: true,
				default: 'getPrices',
				options: [
					{
						name: 'Get Prices',
						value: 'getPrices',
						action: 'Get day-ahead prices',
						routing: { request: { method: 'GET', url: '=/prices/{{$parameter.zone}}' } },
					},
					{
						name: 'Get Forecast',
						value: 'getForecast',
						action: 'Get price forecast',
						routing: { request: { method: 'GET', url: '=/forecasts/{{$parameter.zone}}' } },
					},
					{
						name: 'Get Carbon Intensity',
						value: 'getCarbon',
						action: 'Get carbon intensity and green score',
						routing: { request: { method: 'GET', url: '=/carbon/{{$parameter.zone}}' } },
					},
					{
						name: 'Get Imbalance Prices',
						value: 'getImbalance',
						action: 'Get imbalance prices',
						routing: { request: { method: 'GET', url: '=/imbalance/{{$parameter.zone}}' } },
					},
					{
						name: 'Find Cheapest Window',
						value: 'cheapestWindow',
						action: 'Find the cheapest time window',
						routing: {
							request: {
								method: 'POST',
								url: '/optimize/cheapest-window',
								body: {
									zone: '={{$parameter.zone}}',
									duration_minutes: '={{$parameter.durationMinutes}}',
								},
							},
						},
					},
				],
			},
			{
				displayName: 'Zone',
				name: 'zone',
				type: 'string',
				default: 'DE-LU',
				required: true,
				description: 'Bidding zone code, e.g. DE-LU, FR, SE3 — see GET /v1/zones',
			},
			{
				displayName: 'Duration (Minutes)',
				name: 'durationMinutes',
				type: 'number',
				default: 120,
				displayOptions: { show: { operation: ['cheapestWindow'] } },
			},
		],
	};
}
