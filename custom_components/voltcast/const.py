"""Constants for the Voltcast integration."""

DOMAIN = "voltcast"
BASE_URL = "https://voltcast.com/api"

CONF_API_KEY = "api_key"
CONF_ZONE = "zone"
CONF_DURATION_MINUTES = "duration_minutes"
CONF_OBJECTIVE = "objective"
CONF_GRID_FEE_EUR_KWH = "grid_fee_eur_kwh"
CONF_SUPPLIER_MARKUP_EUR_KWH = "supplier_markup_eur_kwh"
CONF_VAT_PERCENT = "vat_percent"

DEFAULT_DURATION_MINUTES = 120
DEFAULT_OBJECTIVE = "cost"
DEFAULT_GRID_FEE_EUR_KWH = 0.0
DEFAULT_SUPPLIER_MARKUP_EUR_KWH = 0.0
DEFAULT_VAT_PERCENT = 0.0

ATTRIBUTION = "Data by Voltcast (voltcast.com); DE-LU/AT verbatim prices: SMARD.de, Bundesnetzagentur, CC BY 4.0"
