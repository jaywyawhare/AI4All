import asyncio
from typing import Dict, Any, Optional, Tuple
import json
from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder

import httpx
from geopy.geocoders import Nominatim

from config.settings import Settings

class WeatherService:
    """Service for weather information and forecasts."""
    
    def __init__(self):
        self.settings = Settings()
        self.base_url = "https://api.open-meteo.com/v1"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
        self.geolocator = Nominatim(user_agent="whatsapp_weather_bot")
        self.tf = TimezoneFinder()
    
    async def get_weather_forecast(self, location: str, forecast_days: int = 7) -> str:
        """
        Get weather forecast for specified location.
        
        Args:
            location: Location name or coordinates
            forecast_days: Number of forecast days
            
        Returns:
            Formatted weather forecast
        """
        try:
            # Get coordinates for location
            coords = await self._get_coordinates(location)
            if not coords:
                return f"Could not find location: {location}"
            
            lat, lon = coords
            
            # Get current weather
            current_weather = await self._get_current_weather(lat, lon)
            
            # Get forecast
            forecast = await self._get_forecast(lat, lon, forecast_days)
            
            # Format response
            response = self._format_weather_response(location, current_weather, forecast)
            
            return response
            
        except Exception as e:
            return f"Weather service error: {str(e)}"
    
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
    
    def _format_weather_response(self, location: str, current: Dict, forecast: Dict) -> str:
        """Format weather data into readable response."""
        try:
            if "error" in current:
                return f"Weather service error: {current['error']}"
            
            # Current weather from Open-Meteo
            response = f"🌤️ **Weather for {location}**\n\n"
            response += f"**Current Weather:**\n"
            
            # Use Open-Meteo current weather data
            current_weather = current.get("current_weather", {})
            if current_weather:
                response += f"🌡️ Temperature: {current_weather.get('temperature', 'N/A')}°C\n"
                response += f"� Wind Speed: {current_weather.get('windspeed', 'N/A')} km/h\n"
                response += f"🧭 Wind Direction: {current_weather.get('winddirection', 'N/A')}°\n"
            
            # Add hourly data if available
            hourly = current.get("hourly", {})
            if hourly and hourly.get("time"):
                response += f"� Humidity: {hourly.get('relative_humidity_2m', [0])[0]}%\n"
            
            response += "\n"
            
            # Forecast from Open-Meteo
            if "error" not in forecast and forecast.get("daily"):
                response += "**7-Day Forecast:**\n"
                
                daily = forecast["daily"]
                times = daily.get("time", [])
                max_temps = daily.get("temperature_2m_max", [])
                min_temps = daily.get("temperature_2m_min", [])
                precip = daily.get("precipitation_sum", [])
                
                for i, date_str in enumerate(times[:7]):
                    if i < len(max_temps) and i < len(min_temps):
                        dt = datetime.fromisoformat(date_str)
                        day_name = dt.strftime("%A")
                        max_temp = max_temps[i]
                        min_temp = min_temps[i]
                        rain = precip[i] if i < len(precip) else 0
                        
                        response += f"📅 {day_name}: {max_temp}°C / {min_temp}°C"
                        if rain > 0:
                            response += f", Rain: {rain}mm"
                        response += "\n"
            
            # Add farming advice
            response += self._get_weather_summary(current)
            
            return response
            
        except Exception as e:
            return f"Error formatting weather data: {str(e)}"
    
    def _get_weather_summary(self, current_weather: Dict) -> str:
        """Generate weather summary."""
        try:
            current = current_weather.get("current_weather", {})
            hourly = current_weather.get("hourly", {})
            
            temp = current.get("temperature", 0)
            wind_speed = current.get("windspeed", 0)
            humidity = hourly.get("relative_humidity_2m", [0])[0] if hourly.get("relative_humidity_2m") else 0
            
            summary = "\n📊 **Weather Summary:**\n"
            
            # Temperature summary
            if temp < 0:
                summary += "🧊 Freezing conditions\n"
            elif temp < 15:
                summary += "❄️ Cold weather\n"
            elif temp > 35:
                summary += "🔥 Hot weather\n"
            else:
                summary += "🌡️ Moderate temperature\n"
            
            # Humidity summary
            if humidity > 80:
                summary += "💧 High humidity levels\n"
            elif humidity < 40:
                summary += "🏜️ Low humidity conditions\n"
            
            # Wind summary
            if wind_speed > 20:
                summary += "💨 Strong winds\n"
            elif wind_speed > 10:
                summary += "🌬️ Moderate winds\n"
            
            return summary
            
        except Exception:
            return "\n📊 **Weather Summary:** Weather conditions vary.\n"

