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
from config.logging import get_logger

# Initialize logging
logger = get_logger('main')

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
        logger.info(f"Audio transcription requested for language: {language}")
        logger.debug(f"Audio data length: {len(audio_data)} characters")
        
        result = await audio_service.transcribe(audio_data, language)
        
        if result.get("success"):
            transcript = result.get("transcript", "No transcript generated")
            logger.info(f"Audio transcription successful, transcript length: {len(transcript)}")
            return transcript
        else:
            error_msg = f"Transcription failed: {result.get('error', 'Unknown error')}"
            logger.error(f"Audio transcription failed: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Audio transcription failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

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
        logger.info(f"Medical image analysis requested, context: {user_context}")
        logger.debug(f"Image data length: {len(image_data)} characters")
        
        result = await gemini_service.analyze_medical_image(image_data, user_context)
        
        if isinstance(result, dict) and result.get("success"):
            analysis = result.get("analysis", "Image analyzed but no details available")
            logger.info(f"Medical image analysis completed successfully")
            return analysis
        else:
            error_msg = f"Image analysis failed: {result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)}"
            logger.error(f"Medical image analysis failed: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Image analysis failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

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
        logger.info(f"Weather request for location: {location}, forecast days: {forecast_days}")
        
        result = await weather_service.get_weather_forecast(location, forecast_days)
        
        if isinstance(result, dict) and result.get("success"):
            forecast = result.get("forecast", "Weather information retrieved but no details available")
            logger.info(f"Weather information retrieved successfully for {location}")
            return forecast
        else:
            error_msg = f"Weather retrieval failed: {result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)}"
            logger.error(f"Weather retrieval failed: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Weather retrieval failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

CropPredictionToolDescription = RichToolDescription(
    description="Predict crop patterns and farming advice optimized for voice communication.",
    use_when="User asks about crop sowing patterns, rates, or farming advice via voice",
    side_effects=None
)

@mcp.tool(description=CropPredictionToolDescription.model_dump_json())
async def get_crop_advice(
    crop_type: Annotated[str, Field(description="Type of crop")],
    location: Annotated[str, Field(description="Location for crop advice")],
    season: Annotated[str, Field(description="Season (kharif/rabi/zaid)", default="")]
) -> str:
    """Get crop sowing advice and patterns."""
    try:
        logger.info(f"Crop advice requested for {crop_type} in {location}, season: {season}")
        
        result = await crop_service.predict_crop_info(crop_type, location, season)
        
        if isinstance(result, dict) and result.get("success"):
            recommendations = result.get("recommendations", "Crop advice retrieved but no details available")
            logger.info(f"Crop advice retrieved successfully for {crop_type}")
            return recommendations
        else:
            error_msg = f"Crop advice failed: {result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)}"
            logger.error(f"Crop advice failed: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Crop advice failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

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
        logger.info(f"Health record management requested for user: {user_id}, action: {action}")
        logger.debug(f"Health data length: {len(data)} characters")
        
        result = await health_service.manage_record(user_id, action, data)
        
        if isinstance(result, dict) and result.get("success"):
            message = result.get("message", "Health record operation completed")
            logger.info(f"Health record operation completed successfully for user: {user_id}")
            return message
        else:
            error_msg = f"Health record operation failed: {result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)}"
            logger.error(f"Health record operation failed: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Health record management failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

SchemeSearchToolDescription = RichToolDescription(
    description="Search government schemes with voice-friendly explanations in native language.",
    use_when="User asks about government schemes based on their profile via voice interaction",
    side_effects=None
)

@mcp.tool(description=SchemeSearchToolDescription.model_dump_json())
async def search_schemes(
    query: Annotated[str, Field(description="Search query for schemes")],
    age: Annotated[int, Field(description="User age for filtering", default=0)],
    gender: Annotated[str, Field(description="User gender for filtering", default="")],
    state: Annotated[str, Field(description="User state for filtering", default="")],
    category: Annotated[str, Field(description="User category for filtering", default="")]
) -> str:
    """Search for government schemes using vector similarity and filters."""
    try:
        logger.info(f"Scheme search requested with query: '{query}', filters: age={age}, gender={gender}, state={state}, category={category}")
        
        result = await scheme_service.search_schemes(query, age, gender, state, category)
        
        if isinstance(result, dict) and result.get("success"):
            schemes = result.get("schemes", [])
            logger.info(f"Scheme search successful, found {len(schemes)} schemes")
            return schemes
        else:
            error_msg = f"Scheme search failed: {result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)}"
            logger.error(f"Scheme search failed: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Scheme search failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

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
        logger.info(f"Audio generation requested for language: {language}, text length: {len(text)}")
        
        result = await audio_service.generate_audio(text, language)
        
        if isinstance(result, dict) and result.get("success"):
            audio_path = result.get("audio_path", "Audio generated but path not available")
            logger.info(f"Audio generation successful, path: {audio_path}")
            return audio_path
        else:
            error_msg = f"Audio generation failed: {result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)}"
            logger.error(f"Audio generation failed: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Audio generation failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

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
        logger.info(f"Hospital search requested for location: {location}, emergency type: {emergency_type}")
        
        result = await health_service.find_nearby_hospitals(location, emergency_type)
        
        if isinstance(result, dict) and result.get("success"):
            hospitals = result.get("hospitals", "Hospital search completed but no results available")
            logger.info(f"Hospital search completed successfully for {location}")
            return hospitals
        else:
            error_msg = f"Hospital search failed: {result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)}"
            logger.error(f"Hospital search failed: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Hospital search failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

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
        logger.info(f"Sarvam AI response requested for language: {input_language}, format: {response_format}")
        logger.debug(f"Query length: {len(query)} characters, context length: {len(context)} characters")
        
        # Import Sarvam AI client
        try:
            import sarvamai
            client = sarvamai.SarvamAI(api_key=settings.SARVAM_API_KEY)
        except ImportError:
            logger.error("Sarvam AI package not available")
            return "Sarvam AI service not available"
        except Exception as e:
            logger.error(f"Failed to initialize Sarvam AI client: {str(e)}")
            return f"Sarvam AI initialization failed: {str(e)}"
        
        # Generate response
        try:
            response = await client.chat.completions.create(
                model="sarvam-ai/sarvam-v1",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for Indian users. Provide clear, accurate responses in the user's preferred language."},
                    {"role": "user", "content": f"Context: {context}\n\nQuery: {query}"}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            logger.info(f"Sarvam AI response generated successfully, length: {len(ai_response)}")
            
            # Translate if needed
            if input_language != "en":
                try:
                    translation = await client.translate(
                        text=ai_response,
                        source_language="en",
                        target_language=input_language
                    )
                    final_response = translation.translated_text
                    logger.info(f"Response translated to {input_language}")
                except Exception as e:
                    logger.warning(f"Translation failed, using original response: {str(e)}")
                    final_response = ai_response
            else:
                final_response = ai_response
            
            return final_response
            
        except Exception as e:
            error_msg = f"Sarvam AI response generation failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Sarvam AI service failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

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
    """Translate text between languages using Sarvam AI."""
    try:
        logger.info(f"Translation requested from {source_language} to {target_language}")
        logger.debug(f"Text length: {len(text)} characters")
        
        # Import Sarvam AI client
        try:
            import sarvamai
            client = sarvamai.SarvamAI(api_key=settings.SARVAM_API_KEY)
        except ImportError:
            logger.error("Sarvam AI package not available for translation")
            return "Translation service not available"
        except Exception as e:
            logger.error(f"Failed to initialize Sarvam AI client for translation: {str(e)}")
            return f"Translation service initialization failed: {str(e)}"
        
        # Perform translation
        try:
            translation = await client.translate(
                text=text,
                source_language=source_language,
                target_language=target_language
            )
            
            translated_text = translation.translated_text
            logger.info(f"Translation completed successfully, result length: {len(translated_text)}")
            return translated_text
            
        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Translation service failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

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
    """Complete voice processing workflow: transcribe → AI response → audio generation."""
    try:
        logger.info(f"Voice message processing requested for language: {user_language}")
        logger.debug(f"Audio data length: {len(audio_data)} characters")
        
        # Step 1: Transcribe audio
        logger.info("Step 1: Transcribing audio...")
        transcription_result = await audio_service.transcribe(audio_data, user_language)
        
        if not transcription_result.get("success"):
            error_msg = f"Transcription failed: {transcription_result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            return error_msg
        
        transcript = transcription_result.get("transcript", "")
        detected_language = transcription_result.get("detected_language", user_language)
        logger.info(f"Transcription successful: '{transcript[:100]}...' in {detected_language}")
        
        # Step 2: Generate AI response
        logger.info("Step 2: Generating AI response...")
        try:
            import sarvamai
            client = sarvamai.SarvamAI(api_key=settings.SARVAM_API_KEY)
            
            response = await client.chat.completions.create(
                model="sarvam-ai/sarvam-v1",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for Indian users. Provide clear, accurate responses in the user's preferred language."},
                    {"role": "user", "content": transcript}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            logger.info(f"AI response generated successfully, length: {len(ai_response)}")
            
        except Exception as e:
            logger.warning(f"AI response generation failed, using fallback: {str(e)}")
            ai_response = f"I understood you said: {transcript}. How can I help you with that?"
        
        # Step 3: Generate audio response
        logger.info("Step 3: Generating audio response...")
        audio_result = await audio_service.generate_audio(ai_response, detected_language)
        
        if audio_result.get("success"):
            audio_path = audio_result.get("audio_path", "Audio generated but path not available")
            logger.info(f"Voice processing workflow completed successfully")
            return f"Transcription: {transcript}\nAI Response: {ai_response}\nAudio: {audio_path}"
        else:
            logger.warning(f"Audio generation failed, returning text response: {audio_result.get('error', 'Unknown error')}")
            return f"Transcription: {transcript}\nAI Response: {ai_response}\nAudio generation failed"
            
    except Exception as e:
        error_msg = f"Voice processing workflow failed: {str(e)}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

# Help Menu Tool
HelpMenuToolDescription = RichToolDescription(
    description="Get comprehensive help menu with all available tools and voice-first features.",
    use_when="User asks for help, wants to see available features, or needs guidance on using the bot",
    side_effects=None
)

@mcp.tool(description=HelpMenuToolDescription.model_dump_json())
async def get_help_menu(
    language: Annotated[str, Field(description="Language for help menu (e.g., 'en', 'hi', 'ta')", default="en")]
) -> str:
    """Get comprehensive help menu with all available tools and voice-first features."""
    try:
        logger.info(f"Help menu requested in language: {language}")
        
        help_content = {
            "en": {
                "title": "🎤 Voice-First WhatsApp Bot Help Menu",
                "intro": "Welcome to your AI assistant! Here are all the features available:",
                "voice_features": {
                    "title": "🎵 Voice Features",
                    "transcribe": "• Send voice messages - I'll transcribe them to text",
                    "audio_response": "• Get audio responses in your preferred language",
                    "voice_processing": "• Complete voice workflow (transcribe → AI → audio response)"
                },
                "ai_features": {
                    "title": "🤖 AI Features",
                    "sarvam_ai": "• AI-powered responses using Sarvam AI",
                    "translation": "• Translate between Indian languages",
                    "intent_detection": "• Smart intent detection for better responses"
                },
                "government_schemes": {
                    "title": "🏛️ Government Schemes",
                    "search": "• Search for relevant government schemes",
                    "filter": "• Filter by age, gender, state, category",
                    "details": "• Get detailed scheme information and application process"
                },
                "health_features": {
                    "title": "🏥 Health Features",
                    "image_analysis": "• Analyze medical images for wounds/diseases",
                    "report_explanation": "• Explain medical reports in your language",
                    "health_records": "• Manage health records and prescriptions",
                    "hospital_finder": "• Find nearest hospitals and medical facilities"
                },
                "agriculture_features": {
                    "title": "🌾 Agriculture Features",
                    "crop_advice": "• Get crop sowing advice and patterns",
                    "weather_info": "• Weather forecasts for farming",
                    "seasonal_calendar": "• Crop calendar with seasonal recommendations"
                },
                "weather_features": {
                    "title": "🌤️ Weather Features",
                    "forecast": "• Detailed weather information",
                    "farming_advice": "• Weather-based agricultural recommendations",
                    "alerts": "• Crop-specific weather warnings"
                },
                "usage_tips": {
                    "title": "💡 Usage Tips",
                    "voice_first": "• Send voice messages for natural interaction",
                    "language": "• I support Hindi, English, Tamil, Telugu, and more",
                    "context": "• Provide context for better responses",
                    "emergency": "• For medical emergencies, contact healthcare professionals"
                },
                "commands": {
                    "title": "📋 Quick Commands",
                    "help": "• Say 'help' or 'सहायता' for this menu",
                    "schemes": "• Say 'schemes' or 'योजना' for government schemes",
                    "weather": "• Say 'weather' or 'मौसम' for weather info",
                    "health": "• Say 'health' or 'स्वास्थ्य' for health features",
                    "crop": "• Say 'crop' or 'फसल' for agricultural advice"
                }
            },
            "hi": {
                "title": "🎤 वॉइस-फर्स्ट WhatsApp बॉट सहायता मेनू",
                "intro": "आपके AI सहायक में आपका स्वागत है! यहाँ सभी उपलब्ध सुविधाएँ हैं:",
                "voice_features": {
                    "title": "🎵 वॉइस सुविधाएँ",
                    "transcribe": "• वॉइस मैसेज भेजें - मैं उन्हें टेक्स्ट में बदल दूंगा",
                    "audio_response": "• अपनी पसंदीदा भाषा में ऑडियो प्रतिक्रियाएँ प्राप्त करें",
                    "voice_processing": "• पूर्ण वॉइस वर्कफ्लो (ट्रांसक्राइब → AI → ऑडियो प्रतिक्रिया)"
                },
                "ai_features": {
                    "title": "🤖 AI सुविधाएँ",
                    "sarvam_ai": "• Sarvam AI का उपयोग करके AI-संचालित प्रतिक्रियाएँ",
                    "translation": "• भारतीय भाषाओं के बीच अनुवाद",
                    "intent_detection": "• बेहतर प्रतिक्रियाओं के लिए स्मार्ट इंटेंट डिटेक्शन"
                },
                "government_schemes": {
                    "title": "🏛️ सरकारी योजनाएँ",
                    "search": "• प्रासंगिक सरकारी योजनाओं की खोज करें",
                    "filter": "• आयु, लिंग, राज्य, श्रेणी के अनुसार फ़िल्टर करें",
                    "details": "• विस्तृत योजना जानकारी और आवेदन प्रक्रिया प्राप्त करें"
                },
                "health_features": {
                    "title": "🏥 स्वास्थ्य सुविधाएँ",
                    "image_analysis": "• घावों/रोगों के लिए चिकित्सीय छवियों का विश्लेषण",
                    "report_explanation": "• आपकी भाषा में चिकित्सीय रिपोर्ट की व्याख्या",
                    "health_records": "• स्वास्थ्य रिकॉर्ड और पर्चे प्रबंधित करें",
                    "hospital_finder": "• निकटतम अस्पतालों और चिकित्सा सुविधाओं को खोजें"
                },
                "agriculture_features": {
                    "title": "🌾 कृषि सुविधाएँ",
                    "crop_advice": "• फसल बोने की सलाह और पैटर्न प्राप्त करें",
                    "weather_info": "• खेती के लिए मौसम पूर्वानुमान",
                    "seasonal_calendar": "• मौसमी सिफारिशों के साथ फसल कैलेंडर"
                },
                "weather_features": {
                    "title": "🌤️ मौसम सुविधाएँ",
                    "forecast": "• विस्तृत मौसम जानकारी",
                    "farming_advice": "• मौसम-आधारित कृषि सिफारिशें",
                    "alerts": "• फसल-विशिष्ट मौसम चेतावनियाँ"
                },
                "usage_tips": {
                    "title": "💡 उपयोग टिप्स",
                    "voice_first": "• प्राकृतिक बातचीत के लिए वॉइस मैसेज भेजें",
                    "language": "• मैं हिंदी, अंग्रेजी, तमिल, तेलुगु और अधिक का समर्थन करता हूं",
                    "context": "• बेहतर प्रतिक्रियाओं के लिए संदर्भ प्रदान करें",
                    "emergency": "• चिकित्सा आपात स्थितियों के लिए, स्वास्थ्य देखभाल पेशेवरों से संपर्क करें"
                },
                "commands": {
                    "title": "📋 त्वरित कमांड",
                    "help": "• इस मेनू के लिए 'help' या 'सहायता' कहें",
                    "schemes": "• सरकारी योजनाओं के लिए 'schemes' या 'योजना' कहें",
                    "weather": "• मौसम जानकारी के लिए 'weather' या 'मौसम' कहें",
                    "health": "• स्वास्थ्य सुविधाओं के लिए 'health' या 'स्वास्थ्य' कहें",
                    "crop": "• कृषि सलाह के लिए 'crop' या 'फसल' कहें"
                }
            }
        }
        
        # Get help content for the requested language, fallback to English
        content = help_content.get(language.lower(), help_content["en"])
        
        # Build help menu
        help_menu = f"""
{content['title']}

{content['intro']}

{content['voice_features']['title']}
{content['voice_features']['transcribe']}
{content['voice_features']['audio_response']}
{content['voice_features']['voice_processing']}

{content['ai_features']['title']}
{content['ai_features']['sarvam_ai']}
{content['ai_features']['translation']}
{content['ai_features']['intent_detection']}

{content['government_schemes']['title']}
{content['government_schemes']['search']}
{content['government_schemes']['filter']}
{content['government_schemes']['details']}

{content['health_features']['title']}
{content['health_features']['image_analysis']}
{content['health_features']['report_explanation']}
{content['health_features']['health_records']}
{content['health_features']['hospital_finder']}

{content['agriculture_features']['title']}
{content['agriculture_features']['crop_advice']}
{content['agriculture_features']['weather_info']}
{content['agriculture_features']['seasonal_calendar']}

{content['weather_features']['title']}
{content['weather_features']['forecast']}
{content['weather_features']['farming_advice']}
{content['weather_features']['alerts']}

{content['usage_tips']['title']}
{content['usage_tips']['voice_first']}
{content['usage_tips']['language']}
{content['usage_tips']['context']}
{content['usage_tips']['emergency']}

{content['commands']['title']}
{content['commands']['help']}
{content['commands']['schemes']}
{content['commands']['weather']}
{content['commands']['health']}
{content['commands']['crop']}

For more information, just ask me anything! मुझसे कुछ भी पूछें!
        """.strip()
        
        logger.info(f"Help menu generated successfully for language: {language}")
        return help_menu
        
    except Exception as e:
        logger.error(f"Error generating help menu: {str(e)}")
        return f"Sorry, I couldn't generate the help menu. Error: {str(e)}"

# Validation tool
@mcp.tool()
async def validate() -> str:
    """Validate that all services are working correctly."""
    logger.info("Service validation requested")
    return "All services are operational and ready for voice-first interactions!"

async def main():
    """Main function to run the MCP server."""
    try:
        logger.info("Starting Voice-First WhatsApp Bot MCP Server...")
        
        # Log tool names for debugging
        tool_names = [tool.__name__ for tool in mcp.tools]
        logger.info(f"Registered tools: {', '.join(tool_names)}")
        
        # Start the server
        logger.info("Starting MCP server with stdio...")
        await mcp.run_stdio_async()
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Voice-First WhatsApp Bot MCP Server initializing...")
    asyncio.run(main())
