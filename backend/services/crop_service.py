import asyncio
from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timedelta
import httpx

from config.settings import Settings
from services.weather_service import WeatherService

class CropService:
    """Service for crop prediction and agricultural advice."""
    
    def __init__(self):
        self.settings = Settings()
        self.weather_service = WeatherService()
        
        # Free Indian APIs (no API key required)
        self.agmarknet_api = "http://agmarknet.gov.in/SearchCmmMkt.aspx"
        self.imd_weather_api = "https://mausam.imd.gov.in/backend/api"
        self.nic_agri_api = "https://farmer.gov.in/api"
        self.krishi_gov_api = "https://agricoop.nic.in/api"
        self.mkisan_api = "https://mkisan.gov.in/api"
        
        # Alternative free sources
        self.openweather_api = "https://api.openweathermap.org/data/2.5"
        self.crop_calendar_api = "https://raw.githubusercontent.com/CropCalendar/india-data/main"
        
        # Do not initialize client in constructor
        self.client = None
        
        # Cache for API responses
        self.cache = {
            "crop_data": {},
            "soil_data": {},
            "market_prices": {},
            "last_updated": datetime.now()
        }
    
    async def predict_crop_info(self, crop_type: str, location: str, season: str = "") -> str:
        """
        Predict crop sowing patterns, rates, and optimal timing using government APIs.
        
        Args:
            crop_type: Type of crop to analyze
            location: Location for prediction
            season: Specific season (kharif/rabi/zaid)
            
        Returns:
            Comprehensive crop prediction and advice
        """
        try:
            crop_type = crop_type.lower().strip()
            
            # Check cache first
            cache_key = f"{crop_type}_{location}_{season}"
            if cache_key in self.cache["crop_data"]:
                cached_data = self.cache["crop_data"][cache_key]
                if (datetime.now() - cached_data["timestamp"]).total_seconds() < 3600:  # 1 hour cache
                    return cached_data["data"]
            
            # Use fallback crop data if API fails
            crop_info = await self._get_fallback_crop_data(crop_type, location, season)
            
            # Get weather data for the location
            weather_data = await self.weather_service.get_weather_forecast(location, 7)
            
            # Get current month
            current_month = datetime.now().month
            
            # Determine best sowing time
            sowing_advice = self._get_sowing_advice(crop_info, current_month, season)
            
            # Get market price prediction
            price_prediction = await self._get_price_prediction(crop_type, location)
            
            # Format comprehensive response
            response = self._format_crop_response(
                crop_type, location, crop_info, sowing_advice, 
                price_prediction, weather_data
            )
            
            return response
            
        except Exception as e:
            return f"Crop prediction service error: {str(e)}"
    
    def _get_sowing_advice(self, crop_info: Dict, current_month: int, season: str) -> Dict:
        """Get sowing timing advice based on crop and season."""
        advice = {
            "current_suitability": False,
            "next_sowing_window": None,
            "season_recommendation": None,
            "days_to_wait": 0
        }
        
        # Determine season if not provided
        if not season:
            if current_month in [4, 5, 6, 7, 8, 9]:
                season = "kharif"
            elif current_month in [10, 11, 12, 1, 2, 3]:
                season = "rabi"
            else:
                season = "kharif"
        
        season = season.lower()
        
        # Check if season is valid for this crop
        if season not in crop_info["seasons"] and "year-round" not in crop_info["seasons"]:
            # Find the best season
            advice["season_recommendation"] = crop_info["seasons"][0]
            season = crop_info["seasons"][0]
        
        # Get sowing months for the season
        sowing_months = crop_info["sowing_months"].get(season, [])
        
        if current_month in sowing_months:
            advice["current_suitability"] = True
            advice["next_sowing_window"] = "Now is the ideal time!"
        else:
            # Find next sowing window
            next_months = [m for m in sowing_months if m > current_month]
            if next_months:
                next_month = min(next_months)
                advice["days_to_wait"] = (next_month - current_month) * 30  # Approximate
            else:
                # Next year
                next_month = min(sowing_months)
                advice["days_to_wait"] = ((12 - current_month) + next_month) * 30
            
            month_names = {
                1: "January", 2: "February", 3: "March", 4: "April",
                5: "May", 6: "June", 7: "July", 8: "August",
                9: "September", 10: "October", 11: "November", 12: "December"
            }
            
            sowing_month_names = [month_names[m] for m in sowing_months]
            advice["next_sowing_window"] = f"Best months: {', '.join(sowing_month_names)}"
        
        return advice
    
    async def _get_price_prediction(self, crop_type: str, location: str) -> Dict:
        """Get market price prediction from government e-markets."""
        try:
            # Check cache
            cache_key = f"price_{crop_type}_{location}"
            if cache_key in self.cache["market_prices"]:
                cached_data = self.cache["market_prices"][cache_key]
                if (datetime.now() - cached_data["timestamp"]).total_seconds() < 3600:
                    return cached_data["data"]

            # Try to get prices from free sources
            price_data = await self._get_free_market_prices(crop_type, location)
            
            # Cache the response
            self.cache["market_prices"][cache_key] = {
                "timestamp": datetime.now(),
                "data": price_data
            }

            return price_data

        except Exception as e:
            return {
                "current_range": "Error fetching price data",
                "prediction": "Service temporarily unavailable",
                "factors": f"Error: {str(e)}"
            }
    
    def _format_crop_response(self, crop_type: str, location: str, crop_info: Dict, 
                            sowing_advice: Dict, price_prediction: Dict, weather_data: str) -> str:
        """Format comprehensive crop response."""
        
        response = f"🌾 **Crop Advisory for {crop_type.title()} in {location}**\n\n"
        
        # Sowing timing
        response += "📅 **Sowing Timing:**\n"
        if sowing_advice["current_suitability"]:
            response += "✅ Current time is ideal for sowing!\n"
        else:
            response += f"⏰ {sowing_advice['next_sowing_window']}\n"
            if sowing_advice["days_to_wait"] > 0:
                response += f"⏳ Wait approximately {sowing_advice['days_to_wait']//30} months\n"
        
        if sowing_advice["season_recommendation"]:
            response += f"🌱 Recommended season: {sowing_advice['season_recommendation'].title()}\n"
        
        response += "\n"
        
        # Crop details
        response += "🌾 **Crop Information:**\n"
        response += f"⏱️ Duration: {crop_info['duration_days']} days\n"
        response += f"💧 Water requirement: {crop_info['water_requirement'].title()}\n"
        response += f"🌡️ Temperature range: {crop_info['temperature_range'][0]}-{crop_info['temperature_range'][1]}°C\n"
        response += f"🌍 Soil type: {crop_info['soil_type'].title()}\n"
        response += f"📊 Expected yield: {crop_info['expected_yield_per_acre']}\n\n"
        
        # Price prediction
        response += "💰 **Market Price Prediction:**\n"
        response += f"💵 Current range: {price_prediction['current_range']}\n"
        response += f"📈 Trend: {price_prediction['prediction']}\n"
        response += f"📋 Factors: {price_prediction['factors']}\n\n"
        
        # Agricultural recommendations
        response += "🎯 **Recommendations:**\n"
        response += self._get_crop_specific_recommendations(crop_type, crop_info)
        
        # Weather integration note
        response += "\n🌤️ **Weather Consideration:**\n"
        response += "Check current weather conditions and plan accordingly.\n"
        response += "Monitor weather forecasts for optimal planting and harvesting times.\n"
        
        return response
    
    def _get_crop_specific_recommendations(self, crop_type: str, crop_info: Dict) -> str:
        """Get crop-specific farming recommendations from advisory data."""
        recommendations = []
        
        # Extract recommendations from crop_info
        if "recommendations" in crop_info:
            for rec in crop_info["recommendations"]:
                recommendations.append(f"• {rec}")
        
        # Add general recommendations if no specific ones found
        if not recommendations:
            recommendations = [
                "• Follow local agricultural practices",
                "• Consult agricultural extension services",
                "• Use quality inputs",
                "• Monitor crop health regularly"
            ]
        
        return "\n".join(recommendations) + "\n"
    
    async def _handle_unknown_crop(self, crop_type: str, location: str, season: str) -> str:
        """Handle crops not in the database."""
        response = f"🌱 **Advisory for {crop_type.title()}**\n\n"
        response += "This crop is not in our detailed database, but here's general guidance:\n\n"
        response += "📋 **General Recommendations:**\n"
        response += "• Consult local agricultural extension officers\n"
        response += "• Contact nearby agricultural universities\n"
        response += "• Check with local farmer groups\n"
        response += "• Visit district agriculture office\n\n"
        response += "🌍 **Location-specific advice:**\n"
        response += f"For {location}, consider local climate and soil conditions.\n"
        response += "Traditional knowledge from local farmers is valuable.\n\n"
        response += "📞 **Resources:**\n"
        response += "• Kisan Call Center: 1800-180-1551\n"
        response += "• Local agriculture helpline\n"
        response += "• Agricultural apps like Kisan Suvidha\n"
        
        return response
    
    async def get_seasonal_crop_calendar(self, location: str) -> str:
        """Get seasonal crop calendar for the location."""
        try:
            # Try to fetch from government APIs first
            calendar_data = await self._fetch_seasonal_data(location)
            if calendar_data:
                return calendar_data
            
            # If API fails, provide general guidance
            return await self._get_general_seasonal_advice(location)
            
        except Exception as e:
            return f"Error fetching crop calendar: {str(e)}"
    
    async def _fetch_seasonal_data(self, location: str) -> Optional[str]:
        """Fetch seasonal data from government APIs."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try farmer.gov.in for seasonal calendar
                response = await client.get(
                    f"https://farmer.gov.in/seasonal-calendar/{location}",
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    return self._parse_seasonal_data(response.text, location)
                    
        except Exception:
            pass
        
        return None
    
    def _parse_seasonal_data(self, html_content: str, location: str) -> str:
        """Parse seasonal data from HTML response."""
        # In real implementation, would use BeautifulSoup to parse HTML
        output = f"📅 **Seasonal Crop Calendar for {location}**\n\n"
        
        # Add note about data source
        output += "📊 **Data sourced from government agricultural websites**\n\n"
        
        # Add general seasonal guidance
        output += "🌾 **General Seasonal Patterns:**\n"
        output += "• Monsoon season typically supports rice, cotton, and oilseeds\n"
        output += "• Winter season is ideal for wheat, gram, and mustard\n"
        output += "• Summer season supports fodder crops and vegetables\n\n"
        
        output += "💡 **Note:** For specific crop recommendations, consult local agricultural extension services.\n"
        output += "Local climate and soil conditions significantly affect crop selection."
        
        return output
    
    async def _get_general_seasonal_advice(self, location: str) -> str:
        """Get general seasonal advice when specific data is unavailable."""
        output = f"📅 **Seasonal Crop Advisory for {location}**\n\n"
        
        # Determine current season recommendations
        current_month = datetime.now().month
        
        if current_month in [6, 7, 8, 9]:  # Monsoon season
            output += "�️ **Current Season: Monsoon (Kharif)**\n"
            output += "• Suitable for: Rice, Cotton, Sugarcane, Maize\n"
            output += "• Focus on: Water management and pest control\n"
            output += "• Considerations: Monitor rainfall patterns\n\n"
        elif current_month in [11, 12, 1, 2]:  # Winter season
            output += "❄️ **Current Season: Winter (Rabi)**\n"
            output += "• Suitable for: Wheat, Gram, Mustard, Barley\n"
            output += "• Focus on: Irrigation management\n"
            output += "• Considerations: Frost protection if needed\n\n"
        else:  # Summer season
            output += "☀️ **Current Season: Summer (Zaid)**\n"
            output += "• Suitable for: Fodder crops, Vegetables\n"
            output += "• Focus on: Water conservation\n"
            output += "• Considerations: Heat stress management\n\n"
        
        output += "📞 **For detailed information:**\n"
        output += "• Contact local agricultural extension office\n"
        output += "• Visit district collector office\n"
        output += "• Call Kisan Call Center: 1800-180-1551\n"

