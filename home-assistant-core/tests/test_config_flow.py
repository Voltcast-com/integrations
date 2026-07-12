"""Config-flow tests for the Voltcast integration (core test style).

Run inside a home-assistant/core checkout after copying the integration:
    pytest tests/components/voltcast/
"""

from unittest.mock import AsyncMock, patch

from aiovoltcast import VoltcastAuthError, VoltcastConnectionError, VoltcastError

from homeassistant import config_entries
from homeassistant.components.voltcast.const import CONF_ZONE, DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

USER_INPUT = {CONF_API_KEY: "test-key", CONF_ZONE: "de-lu"}


async def test_full_user_flow(hass: HomeAssistant) -> None:
    """Happy path: key validates, entry created with normalized zone."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with (
        patch("homeassistant.components.voltcast.config_flow.VoltcastClient.validate_key"),
        patch("homeassistant.components.voltcast.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Voltcast DE-LU"
    assert result["data"][CONF_ZONE] == "DE-LU"


async def test_invalid_auth(hass: HomeAssistant) -> None:
    """A rejected key shows the invalid_auth error and recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.voltcast.config_flow.VoltcastClient.validate_key",
        side_effect=VoltcastAuthError(401, "unauthenticated", "bad key"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_cannot_connect(hass: HomeAssistant) -> None:
    """Network failure shows cannot_connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.voltcast.config_flow.VoltcastClient.validate_key",
        side_effect=VoltcastConnectionError("timeout"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["errors"] == {"base": "cannot_connect"}


async def test_unknown_zone(hass: HomeAssistant) -> None:
    """A bad zone code shows invalid_zone."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.voltcast.config_flow.VoltcastClient.validate_key",
        side_effect=VoltcastError(404, "zone_not_found", "nope"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "k", CONF_ZONE: "XX"}
        )

    assert result["errors"] == {"base": "invalid_zone"}


async def test_duplicate_zone_aborts(hass: HomeAssistant) -> None:
    """The same zone cannot be configured twice."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    MockConfigEntry(domain=DOMAIN, unique_id="DE-LU", data=USER_INPUT).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch("homeassistant.components.voltcast.config_flow.VoltcastClient.validate_key"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
