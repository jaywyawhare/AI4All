import os
import asyncio
import json
import base64
from typing import Annotated, Optional, List
from pathlib import Path
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, TextContent
from pydantic import BaseModel, Field

# Import our service modules
from services.audio_service import AudioService
from services.gemini_service import GeminiService
from services.weather_service import WeatherService
from services.crop_service import CropService
from services.health_service import HealthService
from services.scheme_service import SchemeService
from config.settings import Settings

# Load settings
settings = Settings()

class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None

class SimpleBearerAuthProvider(BearerAuthProvider):
    """Simple bearer auth provider for MCP server."""
    
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(
            public_key=k.public_key, jwks_uri=None, issuer=None, audience=None
        )
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="whatsapp_bot",
                scopes=[],
                expires_at=None,
            )
        return None

# Initialize MCP server
mcp = FastMCP(
    "WhatsApp Bot MCP Server",
    auth=SimpleBearerAuthProvider(settings.MCP_TOKEN),
)

# Initialize services
audio_service = AudioService()
gemini_service = GeminiService()
weather_service = WeatherService()
crop_service = CropService()
health_service = HealthService()
scheme_service = SchemeService()

# Tool descriptions
AudioTranscriptionToolDescription = RichToolDescription(
    description="Transcribe audio in native language to text using speech recognition.",
    use_when="User sends voice message or audio file that needs to be converted to text",
    side_effects="May store transcription data temporarily for processing"
)

@mcp.tool(description=AudioTranscriptionToolDescription.model_dump_json())
async def transcribe_audio(
    audio_data: Annotated[str, Field(description="Base64 encoded audio data")],
    language: Annotated[str, Field(description="Language code (e.g., 'hi', 'en', 'ta')", default="en")]
) -> str:
    """Transcribe audio in native language to text."""
    try:
        return await audio_service.transcribe(audio_data, language)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Audio transcription failed: {str(e)}"))

ImageAnalysisToolDescription = RichToolDescription(
    description="Analyze wound or disease images using Gemini Vision API with first aid suggestions.",
    use_when="User sends image of wound, disease, or medical condition requiring analysis",
    side_effects="May store analysis results for health records"
)

@mcp.tool(description=ImageAnalysisToolDescription.model_dump_json())
async def analyze_medical_image(
    image_data: Annotated[str, Field(description="Base64 encoded image data")],
    user_context: Annotated[str, Field(description="Additional context about the image", default="")]
) -> str:
    """Analyze medical images for wounds or diseases with first aid suggestions."""
    try:
        return await gemini_service.analyze_medical_image(image_data, user_context)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Image analysis failed: {str(e)}"))

ReportExplanationToolDescription = RichToolDescription(
    description="Explain doctor reports in native language using Gemini text analysis.",
    use_when="User requests explanation of medical reports in their native language",
    side_effects="May store explanation for health records"
)

@mcp.tool(description=ReportExplanationToolDescription.model_dump_json())
async def explain_medical_report(
    report_text: Annotated[str, Field(description="Medical report text to explain")],
    target_language: Annotated[str, Field(description="Target language for explanation", default="en")]
) -> str:
    """Explain medical reports in user's native language."""
    try:
        return await gemini_service.explain_medical_report(report_text, target_language)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Report explanation failed: {str(e)}"))

WeatherToolDescription = RichToolDescription(
    description="Get weather information for crop planning and general queries.",
    use_when="User asks about weather conditions for farming or general weather info",
    side_effects=None
)

@mcp.tool(description=WeatherToolDescription.model_dump_json())
async def get_weather(
    location: Annotated[str, Field(description="Location name or coordinates")],
    forecast_days: Annotated[int, Field(description="Number of forecast days", default=7)]
) -> str:
    """Get weather information for specified location."""
    try:
        return await weather_service.get_weather_forecast(location, forecast_days)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Weather retrieval failed: {str(e)}"))

CropPredictionToolDescription = RichToolDescription(
    description="Predict crop patterns, rates, and optimal sowing times based on location and weather.",
    use_when="User asks about crop sowing patterns, predicted rates, or best sowing times",
    side_effects=None
)

@mcp.tool(description=CropPredictionToolDescription.model_dump_json())
async def predict_crop_info(
    crop_type: Annotated[str, Field(description="Type of crop")],
    location: Annotated[str, Field(description="Location for prediction")],
    season: Annotated[str, Field(description="Season (kharif/rabi/zaid)", default="")]
) -> str:
    """Predict crop sowing patterns, rates, and optimal timing."""
    try:
        return await crop_service.predict_crop_info(crop_type, location, season)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Crop prediction failed: {str(e)}"))

HealthRecordToolDescription = RichToolDescription(
    description="Manage comprehensive health records and prescriptions using mem0.",
    use_when="User wants to store, retrieve, or manage health records and prescriptions",
    side_effects="Stores or modifies health records in memory system"
)

@mcp.tool(description=HealthRecordToolDescription.model_dump_json())
async def manage_health_record(
    user_id: Annotated[str, Field(description="User identifier")],
    action: Annotated[str, Field(description="Action: 'store', 'retrieve', 'add_prescription'")],
    data: Annotated[str, Field(description="Health data in JSON format", default="")]
) -> str:
    """Manage user health records and prescriptions."""
    try:
        return await health_service.manage_record(user_id, action, data)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Health record management failed: {str(e)}"))

SchemeSearchToolDescription = RichToolDescription(
    description="Search government schemes using semantic and parameter-based search.",
    use_when="User asks about government schemes based on their profile or specific criteria",
    side_effects=None
)

@mcp.tool(description=SchemeSearchToolDescription.model_dump_json())
async def search_government_schemes(
    query: Annotated[str, Field(description="Search query for schemes")],
    age: Annotated[int, Field(description="User age", default=0)],
    gender: Annotated[str, Field(description="User gender", default="")],
    state: Annotated[str, Field(description="User state", default="")],
    category: Annotated[str, Field(description="Category (SC/ST/OBC/General)", default="")]
) -> str:
    """Search for relevant government schemes."""
    try:
        return await scheme_service.search_schemes(query, age, gender, state, category)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Scheme search failed: {str(e)}"))

AudioGenerationToolDescription = RichToolDescription(
    description="Generate audio response in user's native language.",
    use_when="User needs audio response in their native language",
    side_effects="May temporarily store generated audio"
)

@mcp.tool(description=AudioGenerationToolDescription.model_dump_json())
async def generate_audio_response(
    text: Annotated[str, Field(description="Text to convert to audio")],
    language: Annotated[str, Field(description="Language code for audio generation", default="en")]
) -> str:
    """Generate audio response in native language."""
    try:
        return await audio_service.generate_audio(text, language)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Audio generation failed: {str(e)}"))

HospitalFinderToolDescription = RichToolDescription(
    description="Find nearest hospitals or clinics based on location.",
    use_when="User needs to find nearby medical facilities",
    side_effects=None
)

@mcp.tool(description=HospitalFinderToolDescription.model_dump_json())
async def find_nearest_hospital(
    location: Annotated[str, Field(description="User location")],
    emergency_type: Annotated[str, Field(description="Type of emergency/medical need", default="general")]
) -> str:
    """Find nearest hospitals or medical facilities."""
    try:
        return await health_service.find_nearby_hospitals(location, emergency_type)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Hospital search failed: {str(e)}"))

@mcp.tool
async def validate() -> str:
    """Validation tool for MCP server."""
    return settings.PHONE_NUMBER

async def main():
    """Start the MCP server."""
    await mcp.run_async(
        "streamable-http",
        host="0.0.0.0",
        port=settings.MCP_PORT,
    )

if __name__ == "__main__":
    asyncio.run(main())
