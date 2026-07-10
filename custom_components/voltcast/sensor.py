"""Voltcast sensors: current price, today's stats, next cheap window."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import VoltcastCoordinator
from .const import ATTRIBUTION, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VoltcastCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        CurrentPriceSensor(coordinator),
        TodayStatSensor(coordinator, "min"),
        TodayStatSensor(coordinator, "max"),
        TodayStatSensor(coordinator, "mean"),
        ForecastP50Sensor(coordinator),
    ])


def _rows(coordinator: VoltcastCoordinator) -> list[dict[str, Any]]:
    return coordinator.data.get("prices", {}).get("data", [])


def _now_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        if row["delivery_start"] <= now < row["delivery_end"]:
            return row
    return None


class VoltcastSensor(CoordinatorEntity[VoltcastCoordinator], SensorEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "EUR/MWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: VoltcastCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"voltcast_{coordinator.zone}_{key}"
        self._attr_name = name


class CurrentPriceSensor(VoltcastSensor):
    def __init__(self, coordinator: VoltcastCoordinator) -> None:
        super().__init__(coordinator, "current", f"{coordinator.zone} current price")

    @property
    def native_value(self) -> float | None:
        row = _now_row(_rows(self.coordinator))
        return row["price_eur_mwh"] if row else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        row = _now_row(_rows(self.coordinator))
        return {"resolution": row["resolution_flag"], "period_start": row["delivery_start"]} if row else {}


class TodayStatSensor(VoltcastSensor):
    def __init__(self, coordinator: VoltcastCoordinator, stat: str) -> None:
        super().__init__(coordinator, f"today_{stat}", f"{coordinator.zone} today {stat}")
        self._stat = stat

    @property
    def native_value(self) -> float | None:
        today = datetime.now(timezone.utc).date().isoformat()
        prices = [r["price_eur_mwh"] for r in _rows(self.coordinator) if r["delivery_start"].startswith(today)]
        if not prices:
            return None
        if self._stat == "min":
            return min(prices)
        if self._stat == "max":
            return max(prices)
        return round(sum(prices) / len(prices), 2)


class ForecastP50Sensor(VoltcastSensor):
    """P50 forecast for the next hour, with the full curve as an attribute."""

    def __init__(self, coordinator: VoltcastCoordinator) -> None:
        super().__init__(coordinator, "forecast_p50", f"{coordinator.zone} forecast P50 next hour")

    @property
    def native_value(self) -> float | None:
        now = datetime.now(timezone.utc).isoformat()
        for row in self.coordinator.data.get("forecast", {}).get("data", []):
            if row["target_start"] >= now:
                return row["p50"]
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        forecast = self.coordinator.data.get("forecast", {})
        return {
            "curve": forecast.get("data", [])[:96],
            "model_version": forecast.get("meta", {}).get("model_version"),
            "accuracy": forecast.get("meta", {}).get("accuracy"),
        }
