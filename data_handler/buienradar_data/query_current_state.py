"""Quick CLI to get Buienradar current state for Eindoven's Achtseweg Zuid 151 C."""

from __future__ import annotations

import argparse
from typing import Any, Iterable, Optional, Tuple

import requests
from buienradar.buienradar import get_data, parse_data
from buienradar.constants import CONTENT, RAINCONTENT, SUCCESS

DEFAULT_ADDRESS = "Achtseweg Zuid 151 C Eindhoven"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode(address: str, session: Optional[requests.Session] = None) -> Tuple[float, float]:
	"""Resolve an address to latitude and longitude using Nominatim."""

	session = session or requests.Session()
	response = session.get(
		NOMINATIM_URL,
		params={"q": address, "format": "json", "limit": 1},
		headers={"User-Agent": "sensors_to_HA/1.0"},
		timeout=15,
	)
	response.raise_for_status()
	data = response.json()
	if not data:
		raise ValueError("No coordinates returned for %s" % address)
	location = data[0]
	return float(location["lat"]), float(location["lon"])


def fetch_current_state(latitude: float, longitude: float, timeframe: int) -> dict[str, Any]:
	"""Call buienradar, parse the API response, and return structured data."""

	result = get_data(latitude=latitude, longitude=longitude)
	if not result.get(SUCCESS):
		raise RuntimeError("Could not get Buienradar data for %s, %s" % (latitude, longitude))
	parsed = parse_data(
		result[CONTENT],
		result[RAINCONTENT],
		latitude,
		longitude,
		timeframe,
	)
	return parsed


def weather_summary_from_state(state: dict[str, Any]) -> dict[str, Any]:
	"""Extract a compact weather summary from the parsed Buienradar response."""

	data = state.get("data") or {}
	condition = data.get("condition") or {}
	precip = data.get("precipitation_forecast") or {}
	measured = data.get("measured")
	measured_iso = measured.isoformat() if hasattr(measured, "isoformat") else None

	return {
		"temperature_c": data.get("temperature"),
		"feel_temperature_c": data.get("feeltemperature"),
		"humidity_pct": data.get("humidity"),
		"pressure_hpa": data.get("pressure"),
		"wind_speed_ms": data.get("windspeed"),
		"wind_gust_ms": data.get("windgust"),
		"wind_direction": data.get("winddirection"),
		"wind_azimuth": data.get("windazimuth"),
		"condition": condition.get("exact") or condition.get("condition"),
		"condition_raw": condition,  # keep raw dict for debugging/UIs
		"precip_total_mm": precip.get("total"),
		"precip_timeframe_min": precip.get("timeframe"),
		"measured_iso": measured_iso,
		"distance_km": state.get("distance"),
	}


def fetch_weather_summary(
	address: str = DEFAULT_ADDRESS,
	timeframe: int = 45,
	session: Optional[requests.Session] = None,
) -> dict[str, Any]:
	"""Geocode once (if needed) and return a concise weather dict."""

	session = session or requests.Session()
	lat, lon = geocode(address, session)
	state = fetch_current_state(lat, lon, timeframe)
	return weather_summary_from_state(state)


def _format_value(label: str, value: Optional[float], unit: str = "", default: str = "n/a") -> str:
	if value is None:
		return f"{label}: {default}"
	formatted = f"{value:.1f}" if isinstance(value, float) else str(value)
	return f"{label}: {formatted}{unit}"


def _format_range(min_value: Optional[float], max_value: Optional[float]) -> str:
	if min_value is None or max_value is None:
		return "n/a"
	return f"{min_value:.1f} / {max_value:.1f}"


def display_state(state: dict[str, Any]) -> None:
	"""Print a short readable overview of the current weather data."""

	data = state.get("data", {})
	measured = data.get("measured")
	condition = data.get("condition", {})
	forecast = data.get("forecast", [])

	header = f"Buienradar report (distance {state.get('distance', 'unknown')} km)"
	print("=" * len(header))
	print(header)
	print("=" * len(header))

	if measured:
		print(f"Measured at {measured:%Y-%m-%d %H:%M %Z}")
	if condition:
		print(f"Condition: {condition.get('exact')} ({condition.get('condition')})")

	print(_format_value("Temperature", data.get("temperature"), "°C"))
	print(_format_value("Feels like", data.get("feeltemperature"), "°C"))
	print(_format_value("Humidity", data.get("humidity"), "%"))
	print(_format_value("Pressure", data.get("pressure"), " hPa"))
	print(_format_value("Wind speed", data.get("windspeed"), " m/s"))
	print(_format_value("Wind gust", data.get("windgust"), " m/s"))
	print(f"Wind direction: {data.get('winddirection', 'n/a')} (azimuth {data.get('windazimuth', 'n/a')})")

	precipitation = data.get("precipitation_forecast", {})
	if precipitation:
		print(
			"Precipitation forecast: total %.1f mm over %s min"
			% (precipitation.get("total", 0.0), precipitation.get("timeframe", "unknown"))
		)

	if forecast:
		print("Next days:")
		for entry in forecast[:3]:
			date = entry.get("datetime")
			date_label = date.strftime("%a %d %b") if date else "??"
			temps = _format_range(entry.get("mintemp"), entry.get("maxtemp"))
			condition_label = entry.get("condition", {}).get("exact", "n/a")
			rain = entry.get("rain", "n/a")
			print(f"  {date_label}: {condition_label} ({temps} °C, rain {rain} mm)")


def main() -> None:
	parser = argparse.ArgumentParser(description="Query Buienradar current state for a fixed address.")
	parser.add_argument("--address", default=DEFAULT_ADDRESS, help="Address to look up via Nominatim")
	parser.add_argument("--latitude", type=float, help="Skip geocoding and use this latitude")
	parser.add_argument("--longitude", type=float, help="Skip geocoding and use this longitude")
	parser.add_argument(
		"--timeframe",
		type=int,
		default=45,
		choices=range(5, 121),
		help="How many minutes to look ahead for precipitation (5-120)",
	)
	parser.add_argument("--raw", action="store_true", help="Output the raw parsed dictionary")

	args = parser.parse_args()
	if args.latitude is not None and args.longitude is not None:
		latitude, longitude = args.latitude, args.longitude
	else:
		latitude, longitude = geocode(args.address)

	state = fetch_current_state(latitude, longitude, args.timeframe)
	if args.raw:
		print(state)
	else:
		display_state(state)


if __name__ == "__main__":
	main()
