import os
import asyncio
import json
import base64
from typing import Annotated, Optional, List
from pathlib import Path
from datetime import datetime

from fastmcp import FastMCP
from mcp import ErrorData, McpError
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

# System prompt for voice-first WhatsApp Bot with Sarvam AI
SYSTEM_PROMPT = """
You are a Voice-First WhatsApp Bot MCP Server designed for users in India who prefer voice interactions, powered by Sarvam AI.

CORE APPROACH - VOICE FIRST WITH SARVAM AI:
1. You are an intelligent AI assistant optimized for voice-based conversations using Sarvam AI
2. Prioritize audio transcription and generation for seamless voice interactions
3. Use Sarvam AI for natural language processing and responses
4. Provide comprehensive voice-friendly answers that work well when spoken

VOICE-FOCUSED TOOLS (PRIORITY):
- transcribe_audio: PRIMARY - Convert user voice messages to text (supports Indian languages)
- generate_audio_response: PRIMARY - Convert your responses to audio in user's native language
- process_voice_message: PRIMARY - Complete voice workflow (transcribe → Sarvam AI → audio response)
- get_sarvam_response: PRIMARY - AI responses using Sarvam AI for voice and text
- translate_text: Translate between Indian languages using Sarvam AI
- analyze_medical_image: For medical image analysis with voice explanations
- explain_medical_report: Explain medical reports in native language (voice-friendly)
- get_weather: Weather info for voice delivery
- predict_crop_info: Crop advice optimized for voice communication
- manage_health_record: Voice-accessible health record management
- search_government_schemes: Government schemes with voice explanations
- find_nearest_hospital: Hospital locations for voice delivery

VOICE INTERACTION STRATEGY WITH SARVAM AI:
1. ALWAYS transcribe incoming voice messages first
2. Process the transcribed text with Sarvam AI for natural responses
3. Use appropriate tools to gather information when needed
4. Generate comprehensive voice-friendly responses using Sarvam AI
5. Convert responses to audio in user's native language
6. Provide both text and audio responses when possible

LANGUAGE SUPPORT (VOICE OPTIMIZED WITH SARVAM AI):
- Primary: Hindi, English
- Secondary: Tamil, Telugu, Bengali, Gujarati, Malayalam, Kannada, Punjabi, Marathi
- Always detect user's language from voice and respond in the same language
- Use Sarvam AI for natural language processing and translation
- Use language-appropriate audio generation tools

VOICE-FRIENDLY RESPONSES:
- Keep responses conversational and natural for speech
- Use simple, clear language that sounds good when spoken
- Break complex information into digestible voice segments
- Include pauses and natural speech patterns
- Avoid complex formatting that doesn't work in voice

SAFETY AND DISCLAIMERS (VOICE):
- For medical concerns: Clear voice disclaimers about consulting professionals
- For agricultural advice: Voice recommendations to consult local experts
- For emergencies: Provide emergency numbers in clear, spoken format
- Always include voice-appropriate disclaimers

VOICE INTERACTION EXAMPLES WITH SARVAM AI:
- User sends voice: "मौसम कैसा है?" → Transcribe → Sarvam AI processing → Generate Hindi audio response
- User sends voice: "मेरी फसल के लिए सलाह दो" → Transcribe → Sarvam AI processing → Generate Hindi audio response
- User sends text: "What is diabetes?" → Sarvam AI processing → Text response
- User sends medical image + voice: Transcribe voice → Analyze image → Sarvam AI processing → Generate comprehensive voice response

Remember: You are a voice-first assistant powered by Sarvam AI. Every interaction should be optimized for voice communication, making information accessible through speech with natural AI responses.
"""

class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None

# Initialize MCP server with system prompt (no auth)
mcp = FastMCP(
    "WhatsApp Bot MCP Server",
    system_prompt=SYSTEM_PROMPT,
)

# Initialize services
audio_service = AudioService()
gemini_service = GeminiService()
weather_service = WeatherService()
crop_service = CropService()
health_service = HealthService()
scheme_service = SchemeService()

# Tool descriptions - Voice First Priority
AudioTranscriptionToolDescription = RichToolDescription(
    description="Transcribe voice messages to text in native language for voice-first interaction.",
    use_when="User sends voice message that needs to be converted to text for processing",
    side_effects="May temporarily store audio file for processing"
)

@mcp.tool(description=AudioTranscriptionToolDescription.model_dump_json())
async def transcribe_audio(
    audio_data: Annotated[str, Field(description="Base64 encoded audio data")],
    language: Annotated[str, Field(description="Language code (e.g., 'hi', 'en', 'ta')", default="en")]
) -> str:
    """Transcribe audio in native language to text."""
    try:
        result = await audio_service.transcribe(audio_data, language)
        if result.get("success"):
            return result.get("transcript", "No transcript generated")
        else:
            return f"Transcription failed: {result.get('error', 'Unknown error')}"
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Audio transcription failed: {str(e)}"))

ImageAnalysisToolDescription = RichToolDescription(
    description="Analyze medical images with voice-friendly explanations in native language.",
    use_when="User sends medical image and needs voice-optimized analysis with first aid suggestions",
    side_effects="May store analysis results for health records"
)

@mcp.tool(description=ImageAnalysisToolDescription.model_dump_json())
async def analyze_medical_image(
    image_data: Annotated[str, Field(description="Base64 encoded image data")],
    user_context: Annotated[str, Field(description="Additional context about the image", default="")]
) -> str:
    """Analyze medical images for wounds or diseases with first aid suggestions."""
    try:
        result = await gemini_service.analyze_medical_image(image_data, user_context)
        if isinstance(result, dict):
            return result.get("analysis", "Analysis completed but no details available")
        return str(result)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Image analysis failed: {str(e)}"))

ReportExplanationToolDescription = RichToolDescription(
    description="Explain medical reports in native language optimized for voice delivery.",
    use_when="User requests explanation of medical reports in their native language for voice communication",
    side_effects="May store explanation for health records"
)

@mcp.tool(description=ReportExplanationToolDescription.model_dump_json())
async def explain_medical_report(
    report_text: Annotated[str, Field(description="Medical report text to explain")],
    target_language: Annotated[str, Field(description="Target language for explanation", default="en")]
) -> str:
    """Explain medical reports in user's native language."""
    try:
        result = await gemini_service.explain_medical_report(report_text, target_language)
        if isinstance(result, dict):
            return result.get("explanation", "Explanation completed but no details available")
        return str(result)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Report explanation failed: {str(e)}"))

WeatherToolDescription = RichToolDescription(
    description="Get weather information optimized for voice delivery and crop planning.",
    use_when="User asks about weather conditions for farming or general weather info via voice",
    side_effects=None
)

@mcp.tool(description=WeatherToolDescription.model_dump_json())
async def get_weather(
    location: Annotated[str, Field(description="Location name or coordinates")],
    forecast_days: Annotated[int, Field(description="Number of forecast days", default=7)]
) -> str:
    """Get weather information for specified location."""
    try:
        result = await weather_service.get_weather_forecast(location, forecast_days)
        if isinstance(result, dict):
            return result.get("forecast", "Weather information retrieved but no details available")
        return str(result)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Weather retrieval failed: {str(e)}"))

CropPredictionToolDescription = RichToolDescription(
    description="Predict crop patterns and farming advice optimized for voice communication.",
    use_when="User asks about crop sowing patterns, rates, or farming advice via voice",
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
        result = await crop_service.predict_crop_info(crop_type, location, season)
        if isinstance(result, dict):
            return result.get("advice", "Crop advice retrieved but no details available")
        return str(result)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Crop prediction failed: {str(e)}"))

HealthRecordToolDescription = RichToolDescription(
    description="Voice-accessible health record management for prescriptions and medical data.",
    use_when="User wants to store, retrieve, or manage health records through voice interaction",
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
        result = await health_service.manage_record(user_id, action, data)
        if isinstance(result, dict):
            return result.get("message", "Health record operation completed")
        return str(result)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Health record management failed: {str(e)}"))

SchemeSearchToolDescription = RichToolDescription(
    description="Search government schemes with voice-friendly explanations in native language.",
    use_when="User asks about government schemes based on their profile via voice interaction",
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
        result = await scheme_service.search_schemes(query, age, gender, state, category)
        if isinstance(result, dict):
            schemes = result.get("schemes", [])
            if schemes:
                scheme_names = [scheme.get("name", "Unknown") for scheme in schemes[:5]]
                return f"Found {len(schemes)} schemes: {', '.join(scheme_names)}"
            else:
                return "No schemes found matching your criteria"
        return str(result)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Scheme search failed: {str(e)}"))

AudioGenerationToolDescription = RichToolDescription(
    description="PRIMARY TOOL - Generate audio response in user's native language for voice-first experience.",
    use_when="User prefers voice responses or needs audio output in their native language",
    side_effects="May temporarily store generated audio"
)

@mcp.tool(description=AudioGenerationToolDescription.model_dump_json())
async def generate_audio_response(
    text: Annotated[str, Field(description="Text to convert to audio")],
    language: Annotated[str, Field(description="Language code for audio generation", default="en")]
) -> str:
    """Generate audio response in native language."""
    try:
        result = await audio_service.generate_audio(text, language)
        if isinstance(result, dict):
            return result.get("audio_path", "Audio generated but path not available")
        return str(result)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Audio generation failed: {str(e)}"))

HospitalFinderToolDescription = RichToolDescription(
    description="Find nearest hospitals with voice-optimized location information.",
    use_when="User needs to find nearby medical facilities through voice interaction",
    side_effects=None
)

@mcp.tool(description=HospitalFinderToolDescription.model_dump_json())
async def find_nearest_hospital(
    location: Annotated[str, Field(description="User location")],
    emergency_type: Annotated[str, Field(description="Type of emergency/medical need", default="general")]
) -> str:
    """Find nearest hospitals or medical facilities."""
    try:
        result = await health_service.find_nearby_hospitals(location, emergency_type)
        if isinstance(result, dict):
            return result.get("hospitals", "Hospital search completed but no results available")
        return str(result)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Hospital search failed: {str(e)}"))

# LLM Support Tool - Sarvam AI
LLMSupportToolDescription = RichToolDescription(
    description="AI-powered responses for voice and text queries using Sarvam AI with translation.",
    use_when="User asks questions via voice or text that need AI reasoning",
    side_effects="May use AI model for response generation and translation"
)

@mcp.tool(description=LLMSupportToolDescription.model_dump_json())
async def get_sarvam_response(
    query: Annotated[str, Field(description="User query for AI response")],
    input_language: Annotated[str, Field(description="Language of user input (e.g., 'hi', 'en', 'ta')", default="en")],
    response_format: Annotated[str, Field(description="Response format: 'text' or 'audio'", default="text")],
    context: Annotated[str, Field(description="Additional context for the query", default="")]
) -> str:
    """Get AI-powered response using Sarvam AI with translation support."""
    try:
        # Import Sarvam AI client
        try:
            from sarvamai import SarvamAI
        except ImportError:
            return "Sarvam AI client not available. Please install sarvamai package."
        
        # Configure Sarvam AI client
        if settings.SARVAM_API_KEY:
            client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
            
            # Prepare system message for voice-first WhatsApp bot
            system_message = f"""
            You are a helpful AI assistant for a voice-first WhatsApp bot serving users in India.
            
            User's Language: {input_language}
            Response Format: {response_format}
            Additional Context: {context}
            
            Please provide a comprehensive response that:
            1. Is conversational and natural for {response_format} delivery
            2. Uses simple, clear language that works well for {response_format}
            3. Is culturally appropriate for Indian users
            4. Includes relevant information and helpful guidance
            5. Is optimized for {response_format} delivery
            6. Can be easily understood by users in India
            
            If the user query is in Hindi or another Indian language, respond in the same language.
            If it's in English, respond in English.
            
            Keep the response informative, helpful, and {response_format}-optimized.
            """
            
            # Prepare messages for Sarvam AI
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": query},
            ]
            
            # Get response from Sarvam AI
            response = client.chat.completions.create(
                model="sarvam-ai/OpenHathi-7B-Instruct-v0.1",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # If audio format requested, generate audio
            if response_format == "audio":
                audio_result = await audio_service.generate_audio(ai_response, input_language)
                if isinstance(audio_result, dict) and audio_result.get("success"):
                    return f"AI Response: {ai_response}\nAudio generated at: {audio_result.get('audio_path', 'Unknown path')}"
                else:
                    return f"AI Response: {ai_response}\nAudio generation failed"
            
            return ai_response
            
        else:
            return "Sarvam AI API key not configured. Please set SARVAM_API_KEY in environment variables."
            
    except Exception as e:
        return f"AI response generation failed: {str(e)}"

# Translation Tool
TranslationToolDescription = RichToolDescription(
    description="Translate text between Indian languages for voice-first communication.",
    use_when="User needs text translated between different Indian languages for voice interaction",
    side_effects=None
)

@mcp.tool(description=TranslationToolDescription.model_dump_json())
async def translate_text(
    text: Annotated[str, Field(description="Text to translate")],
    source_language: Annotated[str, Field(description="Source language code (e.g., 'en', 'hi', 'ta')")],
    target_language: Annotated[str, Field(description="Target language code (e.g., 'en', 'hi', 'ta')")]
) -> str:
    """Translate text between languages."""
    try:
        # Import Sarvam AI client for translation
        try:
            from sarvamai import SarvamAI
        except ImportError:
            return "Translation service not available. Please install sarvamai package."
        
        if settings.SARVAM_API_KEY:
            client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
            
            # Use Sarvam AI for translation
            response = client.chat.completions.create(
                model="sarvam-ai/OpenHathi-7B-Instruct-v0.1",
                messages=[
                    {"role": "system", "content": f"You are a translator. Translate the following text from {source_language} to {target_language}. Provide only the translated text without any explanations."},
                    {"role": "user", "content": text}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content
        else:
            return "Translation service not configured. Please set SARVAM_API_KEY."
            
    except Exception as e:
        return f"Translation failed: {str(e)}"

# Voice Processing Tool (Combined)
VoiceProcessingToolDescription = RichToolDescription(
    description="Complete voice message processing: transcription, intent detection, and response generation.",
    use_when="User sends voice message that needs full processing pipeline",
    side_effects="May store audio files and generate responses"
)

@mcp.tool(description=VoiceProcessingToolDescription.model_dump_json())
async def process_voice_message(
    audio_data: Annotated[str, Field(description="Base64 encoded audio data")],
    user_language: Annotated[str, Field(description="User's preferred language", default="en")]
) -> str:
    """Process complete voice message pipeline."""
    try:
        # Step 1: Transcribe audio
        transcription_result = await audio_service.transcribe(audio_data, user_language)
        
        if not transcription_result.get("success"):
            return f"Voice processing failed: {transcription_result.get('error', 'Unknown error')}"
        
        transcript = transcription_result.get("transcript", "")
        
        # Step 2: Get AI response
        ai_response = await get_sarvam_response(transcript, user_language, "text", "")
        
        # Step 3: Generate audio response
        audio_result = await audio_service.generate_audio(ai_response, user_language)
        
        if isinstance(audio_result, dict) and audio_result.get("success"):
            return f"Transcription: {transcript}\nAI Response: {ai_response}\nAudio generated at: {audio_result.get('audio_path', 'Unknown path')}"
        else:
            return f"Transcription: {transcript}\nAI Response: {ai_response}\nAudio generation failed"
            
    except Exception as e:
        return f"Voice processing failed: {str(e)}"

# Validation tool
@mcp.tool
async def validate() -> str:
    """Validate that all services are working correctly."""
    return "All services are operational and ready for voice-first interactions!"

async def main():
    """Main function to run the MCP server."""
    # Create temp directories
    Path("temp_audio").mkdir(exist_ok=True)
    
    # Start the MCP server
    await mcp.run(
        "streamable-http",
        host="0.0.0.0",
        port=settings.MCP_PORT,
    )

if __name__ == "__main__":
    asyncio.run(main())
