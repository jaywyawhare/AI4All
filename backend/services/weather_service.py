import asyncio
from typing import Dict, Any, Optional, Tuple
import json
from datetime import datetime, timedelta
import pytz

import httpx

from config.settings import Settings

class WeatherService:
    """Service for weather information and forecasts."""
    
    def __init__(self):
        self.settings = Settings()
        self.base_url = "https://api.open-meteo.com/v1"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
    
    async def get_weather_forecast(self, location: str, forecast_days: int = 7) -> Dict[str, Any]:
        """
        Get weather forecast for specified location.
        
        Args:
            location: Location name or coordinates
            forecast_days: Number of forecast days
            
        Returns:
            Raw weather forecast data
        """
        try:
            # Get coordinates for location
            coords = await self._get_coordinates(location)
            if not coords:
                return {
                    "success": False,
                    "error": f"Could not find location: {location}"
                }
            
            lat, lon, location_name = coords
            
            # Get current weather
            current_weather = await self._get_current_weather(lat, lon)
            
            # Get forecast
            forecast = await self._get_forecast(lat, lon, forecast_days)
            
            return {
                "success": True,
                "location": location_name,
                "coordinates": {"lat": lat, "lon": lon},
                "current_weather": current_weather,
                "forecast": forecast,
                "forecast_days": forecast_days
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Weather service error: {str(e)}"
            }
    
    async def _get_coordinates(self, location: str) -> Optional[Tuple[float, float, str]]:
        """Get latitude, longitude and location name for location."""
        try:
            # Check if location is already coordinates
            if "," in location:
                parts = location.split(",")
                if len(parts) == 2:
                    try:
                        lat = float(parts[0].strip())
                        lon = float(parts[1].strip())
                        return (lat, lon, f"{lat}, {lon}")
                    except ValueError:
                        pass
            
            # Use Open-Meteo geocoding API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.geocoding_url}/search",
                    params={
                        "name": location,
                        "count": 1,
                        "language": "en",
                        "format": "json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        result = data["results"][0]
                        return (
                            result["latitude"],
                            result["longitude"], 
                            result["name"]
                        )
            
            return None
            
        except Exception:
            return None
    
    async def _get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data from Open-Meteo."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current_weather": "true",
                        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                        "timezone": "auto"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def _get_forecast(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Get weather forecast data from Open-Meteo."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum",
                        "forecast_days": min(days, 7),
                        "timezone": "auto"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def get_agricultural_weather_alert(self, location: str, crop_type: str) -> Dict[str, Any]:
        """Get weather alerts specific to agriculture."""
        try:
            coords = await self._get_coordinates(location)
            if not coords:
                return {
                    "success": False,
                    "error": f"Could not find location: {location}"
                }
            
            lat, lon, location_name = coords
            current = await self._get_current_weather(lat, lon)
            forecast = await self._get_forecast(lat, lon, 3)
            
            return {
                "success": True,
                "location": location_name,
                "crop_type": crop_type,
                "coordinates": {"lat": lat, "lon": lon},
                "current_weather": current,
                "forecast": forecast,
                "alert_type": "agricultural",
                "note": "Weather alert service not fully configured"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Weather alert service error: {str(e)}"
            }

