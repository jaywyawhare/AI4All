import asyncio
import requests
from typing import Dict, Any, Optional, Tuple
import json
from datetime import datetime, timedelta
import pytz

import httpx

from config.settings import Settings
from config.logging import get_logger

# Initialize logger for weather service
logger = get_logger('weather_service')

class WeatherService:
    """Service for weather information and forecasts."""
    
    def __init__(self):
        self.settings = Settings()
        self.base_url = "https://api.open-meteo.com/v1"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
    
    async def get_weather_forecast(self, location: str, days: int = 7) -> Dict[str, Any]:
        """
        Get weather forecast for a location.
        
        Args:
            location: Location name or coordinates
            days: Number of forecast days (1-7)
            
        Returns:
            Raw weather forecast data
        """
        try:
            logger.info(f"Getting weather forecast for location: {location}, days: {days}")
            
            if not self.api_key:
                logger.warning("Weather API key not configured")
                return {
                    "success": False,
                    "error": "Weather API key not configured"
                }
            
            # Validate days parameter
            if days < 1 or days > 7:
                logger.warning(f"Invalid days parameter: {days}, using default 7")
                days = 7
            
            # Get coordinates for location
            coords = await self._get_coordinates(location)
            if not coords:
                logger.error(f"Could not get coordinates for location: {location}")
                return {
                    "success": False,
                    "error": f"Location not found: {location}"
                }
            
            lat, lon = coords
            logger.debug(f"Coordinates for {location}: lat={lat}, lon={lon}")
            
            # Get weather data
            weather_data = await self._fetch_weather_data(lat, lon, days)
            if not weather_data:
                logger.error(f"Failed to fetch weather data for {location}")
                return {
                    "success": False,
                    "error": "Failed to fetch weather data"
                }
            
            logger.info(f"Weather forecast retrieved successfully for {location}")
            return {
                "success": True,
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "forecast": weather_data,
                "days": days,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Weather forecast failed for {location}: {str(e)}")
            return {
                "success": False,
                "error": f"Weather forecast failed: {str(e)}"
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

