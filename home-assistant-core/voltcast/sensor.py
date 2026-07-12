"""Voltcast sensors: current price, daily stats, next-hour forecast."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import VoltcastConfigEntry, VoltcastCoordinator


def _rows(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return data.get(key, {}).get("data", [])


def _current_price(data: dict[str, Any]) -> float | None:
    now = datetime.now(timezone.utc).isoformat()
    current = None
    for row in _rows(data, "prices"):
        if row["delivery_start"] <= now:
            current = row["price_eur_mwh"]
        else:
            break
    return current


def _today_stat(data: dict[str, Any], fn: Callable[[list[float]], float]) -> float | None:
    today = datetime.now(timezone.utc).date().isoformat()
    values = [
        row["price_eur_mwh"]
        for row in _rows(data, "prices")
        if row["delivery_start"].startswith(today)
    ]
    return round(fn(values), 2) if values else None


def _next_hour_forecast(data: dict[str, Any]) -> float | None:
    now = datetime.now(timezone.utc).isoformat()
    for row in _rows(data, "forecast"):
        if row["target_start"] >= now:
            return row.get("p50")
    return None


@dataclass(frozen=True, kw_only=True)
class VoltcastSensorDescription(SensorEntityDescription):
    """Describes a Voltcast sensor."""

    value_fn: Callable[[dict[str, Any]], float | None]


SENSORS: tuple[VoltcastSensorDescription, ...] = (
    VoltcastSensorDescription(
        key="current_price",
        translation_key="current_price",
        native_unit_of_measurement="EUR/MWh",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_current_price,
    ),
    VoltcastSensorDescription(
        key="today_min",
        translation_key="today_min",
        native_unit_of_measurement="EUR/MWh",
        value_fn=lambda data: _today_stat(data, min),
    ),
    VoltcastSensorDescription(
        key="today_max",
        translation_key="today_max",
        native_unit_of_measurement="EUR/MWh",
        value_fn=lambda data: _today_stat(data, max),
    ),
    VoltcastSensorDescription(
        key="today_mean",
        translation_key="today_mean",
        native_unit_of_measurement="EUR/MWh",
        value_fn=lambda data: _today_stat(data, lambda v: sum(v) / len(v)),
    ),
    VoltcastSensorDescription(
        key="forecast_next_hour",
        translation_key="forecast_next_hour",
        native_unit_of_measurement="EUR/MWh",
        value_fn=_next_hour_forecast,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VoltcastConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Voltcast sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        VoltcastSensor(coordinator, description) for description in SENSORS
    )


class VoltcastSensor(CoordinatorEntity[VoltcastCoordinator], SensorEntity):
    """A Voltcast price sensor."""

    entity_description: VoltcastSensorDescription
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VoltcastCoordinator,
        description: VoltcastSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.zone}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.zone)},
            name=f"Voltcast {coordinator.zone}",
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Voltcast",
            configuration_url="https://voltcast.com/dashboard",
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
