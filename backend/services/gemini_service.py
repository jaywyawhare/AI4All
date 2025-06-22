import base64
import tempfile
from typing import Optional, Dict, Any
import json

from google.genai import types
import google.genai as genai
from PIL import Image
import io

from config.settings import Settings
from config.logging import get_logger

# Initialize logger for gemini service
logger = get_logger('gemini_service')

class GeminiService:
    """Service for Gemini AI image analysis and text processing."""
    
    def __init__(self):
        self.settings = Settings()
        if self.settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        else:
            self.client = None
    
    async def analyze_medical_image(self, image_data: str, user_context: str = "") -> Dict[str, Any]:
        """
        Analyze medical images for wounds or diseases with first aid suggestions.
        
        Args:
            image_data: Base64 encoded image data
            user_context: Additional context about the image
            
        Returns:
            Raw analysis data
        """
        if not self.client:
            logger.warning("Gemini API key not configured for medical image analysis")
            return {
                "success": False,
                "error": "Gemini API key not configured"
            }
        
        try:
            logger.info(f"Starting medical image analysis, context: {user_context}")
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            logger.debug(f"Decoded image data, size: {len(image_bytes)} bytes")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            logger.debug(f"Image opened successfully, format: {image.format}, size: {image.size}")
            
            # Generate response using AI model
            prompt = self._get_medical_prompt(user_context)
            logger.debug(f"Generated medical analysis prompt: {prompt[:100]}...")
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/jpeg',
                    ),
                    prompt
                ]
            )
            logger.info(f"Medical image analysis completed successfully, response length: {len(response.text)}")
            
            return {
                "success": True,
                "analysis": response.text,
                "user_context": user_context,
                "image_size": len(image_bytes),
                "model_used": "gemini-2.0-flash-lite",
                "disclaimer": "This AI analysis is for informational purposes only and should NEVER replace professional medical diagnosis or treatment."
            }
            
        except Exception as e:
            logger.error(f"Medical image analysis failed: {str(e)}")
            return {
                "success": False,
                "error": f"Image analysis failed: {str(e)}",
                "recommendation": "Please consult a healthcare professional immediately for any medical concerns."
            }
    
    def _get_medical_prompt(self, user_context: str) -> str:
        """Get medical analysis prompt."""
        # Placeholder implementation - should be loaded from external source
        return f"Analyze this medical image. Context: {user_context}"
    
    async def explain_medical_report(self, report_text: str, target_language: str = "en") -> Dict[str, Any]:
        """
        Explain medical reports in user's native language.
        
        Args:
            report_text: Medical report text to explain
            target_language: Target language for explanation
            
        Returns:
            Raw explanation data
        """
        if not self.client:
            return {
                "success": False,
                "error": "Gemini API key not configured"
            }
        
        try:
            target_lang_name = self._get_language_name(target_language)
            prompt = self._get_report_explanation_prompt(report_text, target_lang_name)
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[prompt]
            )
            
            return {
                "success": True,
                "original_report": report_text,
                "explanation": response.text,
                "target_language": target_language,
                "language_name": target_lang_name,
                "model_used": "gemini-2.0-flash-lite"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Report explanation failed: {str(e)}",
                "recommendation": "Please consult your doctor for clarification."
            }
    
    def _get_language_name(self, language_code: str) -> str:
        """Get language name from code."""
        # Placeholder implementation - should be loaded from external source
        language_names = {
            "en": "English",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu",
            "bn": "Bengali",
            "gu": "Gujarati",
            "ml": "Malayalam",
            "kn": "Kannada",
            "pa": "Punjabi",
            "mr": "Marathi"
        }
        return language_names.get(language_code, "English")
    
    def _get_report_explanation_prompt(self, report_text: str, target_language: str) -> str:
        """Get medical report explanation prompt."""
        # Placeholder implementation - should be loaded from external source
        return f"Explain this medical report in {target_language}: {report_text}"
    
    async def analyze_general_image(self, image_data: str, question: str) -> Dict[str, Any]:
        """
        General image analysis with custom questions.
        
        Args:
            image_data: Base64 encoded image data
            question: Question about the image
            
        Returns:
            Raw analysis data
        """
        if not self.client:
            return {
                "success": False,
                "error": "Gemini API key not configured"
            }
        
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Generate response using AI model
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/jpeg',
                    ),
                    question
                ]
            )
            
            return {
                "success": True,
                "question": question,
                "analysis": response.text,
                "image_size": len(image_bytes),
                "model_used": "gemini-2.0-flash-lite"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Image analysis failed: {str(e)}"
            }
    
    async def generate_health_advice(self, symptoms: str, age: int, gender: str) -> Dict[str, Any]:
        """
        Generate health advice based on symptoms and user profile.
        
        Args:
            symptoms: Described symptoms
            age: User age
            gender: User gender
            
        Returns:
            Raw health advice data
        """
        if not self.client:
            return {
                "success": False,
                "error": "Gemini API key not configured"
            }
        
        try:
            prompt = self._get_health_advice_prompt(symptoms, age, gender)
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[prompt]
            )
            
            return {
                "success": True,
                "symptoms": symptoms,
                "user_profile": {"age": age, "gender": gender},
                "advice": response.text,
                "model_used": "gemini-2.0-flash-lite",
                "disclaimer": "This is general health information only. Please consult a healthcare professional for proper medical advice."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Health advice generation failed: {str(e)}",
                "recommendation": "Please consult a healthcare professional."
            }
    
    def _get_health_advice_prompt(self, symptoms: str, age: int, gender: str) -> str:
        """Get health advice prompt."""
        # Placeholder implementation - should be loaded from external source
        return f"Provide health advice for: Age {age}, Gender {gender}, Symptoms: {symptoms}"
