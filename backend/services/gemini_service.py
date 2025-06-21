import base64
import tempfile
from typing import Optional, Dict, Any
import json

from google.genai import types
import google.genai as genai
from PIL import Image
import io

from config.settings import Settings

class GeminiService:
    """Service for Gemini AI image analysis and text processing."""
    
    def __init__(self):
        self.settings = Settings()
        if self.settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        else:
            self.client = None
    
    async def analyze_medical_image(self, image_data: str, user_context: str = "") -> str:
        """
        Analyze medical images for wounds or diseases with first aid suggestions.
        
        Args:
            image_data: Base64 encoded image data
            user_context: Additional context about the image
            
        Returns:
            Analysis result with first aid suggestions
        """
        if not self.client:
            return "Gemini API key not configured. Cannot analyze image."
        
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Prepare prompt for comprehensive medical image analysis
            prompt = f"""
            As a medical assistant AI, provide a detailed analysis of this medical image.

            Context provided by user: {user_context}

            Step 1 - General Assessment:
            - Image type (clinical photo/X-ray/MRI/CT/ultrasound)
            - Image quality and clarity
            - Anatomical region shown

            Step 2 - Detailed Analysis Based on Image Type:

            For Clinical Photos (wounds/skin/external):
            - Size and appearance of affected area
            - Color changes or abnormalities 
            - Signs of infection/inflammation
            - Wound characteristics if present
            - Surrounding tissue condition

            For Medical Imaging (X-ray/MRI/CT):
            - Bone/tissue structure and alignment
            - Density variations
            - Presence of fractures/lesions
            - Soft tissue abnormalities
            - Comparison with normal anatomy

            Step 3 - Clinical Assessment:
            1. Primary observations
            2. Possible conditions/diagnoses
            3. Severity indicators
            4. Concerning features
            5. Immediate risks

            Step 4 - Recommendations:
            1. Urgency level (routine/urgent/emergency)
            2. First aid/immediate care steps
            3. Required medical attention
            4. Follow-up timeline
            5. Preventive measures

            WARNING SIGNS - List specific symptoms requiring emergency care.

            Remember to:
            - Be comprehensive but conservative in assessment
            - Highlight any limitations in image analysis
            - Emphasize the importance of professional medical evaluation
            """
            
            # Generate response using new SDK
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
            
            # Add important medical disclaimer
            disclaimer = "\n\n🚨 CRITICAL MEDICAL DISCLAIMER:\nThis AI analysis is for informational purposes only and should NEVER replace professional medical diagnosis or treatment. For any medical concern, especially wounds, injuries, or skin conditions, please consult a healthcare professional immediately. In case of emergency, call your local emergency services."
            
            return response.text + disclaimer
            
        except Exception as e:
            return f"Image analysis failed: {str(e)}. Please consult a healthcare professional immediately for any medical concerns."
    
    async def explain_medical_report(self, report_text: str, target_language: str = "en") -> str:
        """
        Explain medical reports in user's native language.
        
        Args:
            report_text: Medical report text to explain
            target_language: Target language for explanation
            
        Returns:
            Simplified explanation of the medical report
        """
        if not self.client:
            return "Gemini API key not configured. Cannot explain report."
        
        try:
            # Language mapping
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
            
            target_lang_name = language_names.get(target_language, "English")
            
            prompt = f"""
            You are a medical expert who explains complex medical reports in simple terms.
            
            Please explain the following medical report in {target_lang_name} language:
            
            {report_text}
            
            Your explanation should:
            1. Use simple, non-technical language
            2. Explain medical terms clearly
            3. Highlight important findings
            4. Suggest next steps if applicable
            5. Be culturally sensitive and appropriate
            
            Structure your response with:
            - Summary in simple terms
            - Key findings explained
            - What this means for the patient
            - Recommended actions
            
            Keep the tone reassuring but honest.
            """
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[prompt]
            )
            
            return response.text
            
        except Exception as e:
            return f"Report explanation failed: {str(e)}. Please consult your doctor for clarification."
    
    async def analyze_general_image(self, image_data: str, question: str) -> str:
        """
        General image analysis with custom questions.
        
        Args:
            image_data: Base64 encoded image data
            question: Question about the image
            
        Returns:
            Analysis response
        """
        if not self.client:
            return "Gemini API key not configured. Cannot analyze image."
        
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Generate response using new SDK
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
            
            return response.text
            
        except Exception as e:
            return f"Image analysis failed: {str(e)}"
    
    async def generate_health_advice(self, symptoms: str, age: int, gender: str) -> str:
        """
        Generate health advice based on symptoms and user profile.
        
        Args:
            symptoms: Described symptoms
            age: User age
            gender: User gender
            
        Returns:
            Health advice and recommendations
        """
        if not self.client:
            return "Gemini API key not configured. Cannot provide health advice."
        
        try:
            prompt = f"""
            As a health advisor AI, provide guidance for the following:
            
            Patient Profile:
            - Age: {age}
            - Gender: {gender}
            - Symptoms: {symptoms}
            
            Please provide:
            1. Possible causes (general, not diagnostic)
            2. Home care suggestions
            3. When to seek medical attention
            4. Prevention tips
            5. Important warnings
            
            Always emphasize:
            - This is not a medical diagnosis
            - Professional consultation is recommended
            - Emergency signs to watch for
            
            Be helpful but conservative in recommendations.
            """
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[prompt]
            )
            
            disclaimer = "\n\n⚠️ This is general health information only. Please consult a healthcare professional for proper medical advice."
            
            return response.text + disclaimer
            
        except Exception as e:
            return f"Health advice generation failed: {str(e)}. Please consult a healthcare professional."
