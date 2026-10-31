"""
Open-Meteo Weather Service Module
Fulfills Section 4 of Project Spec:
- Uses Open-Meteo API (free, no signup, no API key required).
- Returns current temperature, humidity, wind speed, apparent temp, pressure, and conditions.
"""
import requests
from datetime import datetime

WMO_CODES = {
    0: ("Clear Sky", "CLEAR"),
    1: ("Mainly Clear", "CLEAR"),
    2: ("Partly Cloudy", "CLOUDY"),
    3: ("Overcast", "OVERCAST"),
    45: ("Foggy", "FOG"),
    48: ("Depositing Rime Fog", "FOG"),
    51: ("Light Drizzle", "DRIZZLE"),
    53: ("Moderate Drizzle", "DRIZZLE"),
    55: ("Dense Drizzle", "DRIZZLE"),
    61: ("Slight Rain", "RAIN"),
    63: ("Moderate Rain", "RAIN"),
    65: ("Heavy Rain", "HEAVY_RAIN"),
    71: ("Slight Snow", "SNOW"),
    73: ("Moderate Snow", "SNOW"),
    75: ("Heavy Snow", "SNOW"),
    80: ("Slight Rain Showers", "SHOWERS"),
    81: ("Moderate Rain Showers", "SHOWERS"),
    82: ("Violent Rain Showers", "STORM"),
    95: ("Thunderstorm", "THUNDERSTORM"),
    96: ("Thunderstorm with Hail", "THUNDERSTORM"),
    99: ("Heavy Hail Thunderstorm", "THUNDERSTORM"),
}


def geocode_city(city_name: str):
    """Look up latitude & longitude for a city name via Open-Meteo Geocoding API."""
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        resp = requests.get(
            url,
            params={"name": city_name, "count": 1, "language": "en", "format": "json"},
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        top = results[0]
        return {
            "city": top.get("name", city_name),
            "country": top.get("country", ""),
            "admin1": top.get("admin1", ""),
            "latitude": top["latitude"],
            "longitude": top["longitude"],
            "timezone": top.get("timezone", "auto"),
        }
    except Exception:
        return None


def get_weather(city: str = "Panaji", lat: float = 15.4909, lon: float = 73.8278):
    """
    Fetch real-time weather telemetry from Open-Meteo API.
    Includes temperature, relative humidity, wind speed, apparent temp, pressure, and hourly trend.
    """
    location_info = {
        "city": city,
        "country": "",
        "latitude": lat,
        "longitude": lon,
    }

    if city:
        geo = geocode_city(city)
        if geo:
            location_info = geo
            lat = geo["latitude"]
            lon = geo["longitude"]

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "is_day",
                "precipitation",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "weather_code",
            ],
            "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability"],
            "forecast_days": 1,
            "timezone": "auto",
        }
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
        curr = payload.get("current", {})
        units = payload.get("current_units", {})
        wmo = int(curr.get("weather_code", 0))
        cond_desc, cond_tag = WMO_CODES.get(wmo, ("Atmospheric Nominal", "NOMINAL"))

        hourly = payload.get("hourly", {})
        hourly_times = hourly.get("time", [])[:12]
        hourly_temps = hourly.get("temperature_2m", [])[:12]

        return {
            "status": "ONLINE",
            "source": "Open-Meteo Satellite Telemetry (No-Key API)",
            "city": location_info["city"],
            "region": location_info.get("admin1", ""),
            "country": location_info.get("country", ""),
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "temperature": curr.get("temperature_2m", "--"),
            "temp_unit": units.get("temperature_2m", "°C"),
            "feels_like": curr.get("apparent_temperature", "--"),
            "humidity": curr.get("relative_humidity_2m", "--"),
            "humidity_unit": units.get("relative_humidity_2m", "%"),
            "wind_speed": curr.get("wind_speed_10m", "--"),
            "wind_unit": units.get("wind_speed_10m", "km/h"),
            "wind_direction": curr.get("wind_direction_10m", 0),
            "pressure": curr.get("surface_pressure", "--"),
            "pressure_unit": units.get("surface_pressure", "hPa"),
            "precipitation": curr.get("precipitation", 0.0),
            "condition": cond_desc,
            "condition_tag": cond_tag,
            "is_day": bool(curr.get("is_day", 1)),
            "hourly_times": [t.split("T")[-1] for t in hourly_times],
            "hourly_temps": hourly_temps,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
    except Exception as exc:
        return {
            "status": "OFFLINE",
            "source": "Open-Meteo Telemetry (Connection Fallback)",
            "city": location_info["city"],
            "country": location_info.get("country", ""),
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "temperature": 28.4,
            "temp_unit": "°C",
            "feels_like": 31.0,
            "humidity": 74,
            "humidity_unit": "%",
            "wind_speed": 14.2,
            "wind_unit": "km/h",
            "wind_direction": 245,
            "pressure": 1011.5,
            "pressure_unit": "hPa",
            "precipitation": 0.0,
            "condition": "Simulated Sensor Readout (Check Wi-Fi)",
            "condition_tag": "FALLBACK",
            "hourly_times": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
            "hourly_temps": [25.1, 24.6, 25.8, 28.4, 30.2, 29.7, 27.5, 26.2],
            "error": str(exc),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
