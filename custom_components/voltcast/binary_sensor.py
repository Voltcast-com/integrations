"""Voltcast action signals for safe Home Assistant automations."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import VoltcastCoordinator
from .const import ATTRIBUTION
from .helpers import charge_now, negative_risk, parse_utc, recommended_window


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: VoltcastCoordinator = entry.runtime_data
    async_add_entities(
        [
            ChargeNowBinarySensor(coordinator),
            NegativePriceIncomingBinarySensor(coordinator),
        ]
    )


class VoltcastBinarySensor(
    CoordinatorEntity[VoltcastCoordinator],
    BinarySensorEntity,
):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: VoltcastCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"voltcast_{coordinator.zone}_{key}"
        self._attr_name = name


class ChargeNowBinarySensor(VoltcastBinarySensor):
    """True only while the API's highest-ranked window is active."""

    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator: VoltcastCoordinator) -> None:
        super().__init__(coordinator, "charge_now", f"{coordinator.zone} charge now")
        self._cancel_boundary: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._schedule_boundary()

    async def async_will_remove_from_hass(self) -> None:
        if self._cancel_boundary is not None:
            self._cancel_boundary()
            self._cancel_boundary = None
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._schedule_boundary()
        self.async_write_ha_state()

    @callback
    def _handle_boundary(self, _now) -> None:
        self._cancel_boundary = None
        self.async_write_ha_state()
        self._schedule_boundary()

    @callback
    def _schedule_boundary(self) -> None:
        if self._cancel_boundary is not None:
            self._cancel_boundary()
            self._cancel_boundary = None

        window = recommended_window(self.coordinator.data)
        if window is None:
            return

        now = datetime.now(timezone.utc)
        boundaries = [
            boundary
            for boundary in (
                parse_utc(window.get("start")),
                parse_utc(window.get("end")),
            )
            if boundary is not None and boundary > now
        ]
        if boundaries:
            self._cancel_boundary = async_track_point_in_utc_time(
                self.hass,
                self._handle_boundary,
                min(boundaries),
            )

    @property
    def available(self) -> bool:
        return super().available and recommended_window(self.coordinator.data) is not None

    @property
    def is_on(self) -> bool:
        return charge_now(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        window = recommended_window(self.coordinator.data)
        if window is None:
            return {}
        carbon_meta = (
            self.coordinator.data.get("optimization", {})
            .get("meta", {})
            .get("carbon_estimate", {})
        )

        return {
            "window_start": window.get("start"),
            "window_end": window.get("end"),
            "objective": window.get("objective"),
            "avg_all_in_eur_kwh": window.get("avg_all_in_eur_kwh"),
            "estimated_carbon_gco2eq_kwh": window.get(
                "estimated_carbon_gco2eq_kwh"
            ),
            "carbon_profile_status": carbon_meta.get("status"),
            "is_forward_carbon_forecast": carbon_meta.get(
                "is_forward_carbon_forecast"
            ),
            "supports_emissions_reduction_claim": carbon_meta.get(
                "supports_emissions_reduction_claim"
            ),
            "safety_note": "Recommendation only; keep charger, battery, and thermal safety limits authoritative.",
        }


class NegativePriceIncomingBinarySensor(VoltcastBinarySensor):
    """True when P(price < 0) reaches 50% inside the next 24 hours."""

    _attr_icon = "mdi:flash-alert"

    def __init__(self, coordinator: VoltcastCoordinator) -> None:
        super().__init__(
            coordinator,
            "negative_price_incoming",
            f"{coordinator.zone} negative price incoming",
        )

    @property
    def available(self) -> bool:
        risk_data = self.coordinator.data.get("risk", {}).get("data", {})
        return super().available and isinstance(risk_data, dict)

    @property
    def is_on(self) -> bool:
        return bool(negative_risk(self.coordinator.data)["incoming"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return negative_risk(self.coordinator.data)
