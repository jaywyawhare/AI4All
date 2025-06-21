import os
import base64
import tempfile
import asyncio
from pathlib import Path
from typing import Optional
import requests
import re
import io
import wave

from config.settings import Settings

class AudioService:
    """Service for handling audio transcription and generation using Sarvam APIs."""
    
    def __init__(self):
        self.settings = Settings()
        # Get Sarvam API key from settings or environment
        self.api_key = getattr(self.settings, 'SARVAM_API_KEY', None) or os.getenv('SARVAM_API_KEY')
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY not found in settings or environment variables")
        
        # Language mapping for Sarvam API
        self.language_mapping = {
            "hindi": "hi-IN",
            "english": "en-IN", 
            "tamil": "ta-IN",
            "telugu": "te-IN",
            "kannada": "kn-IN",
            "malayalam": "ml-IN",
            "gujarati": "gu-IN",
            "punjabi": "pa-IN",
            "marathi": "mr-IN",
            "bengali": "bn-IN",
            "odia": "or-IN"
        }
    
    async def transcribe(self, audio_data: str, language: str = "en") -> str:
        """
        Transcribe audio to text using Sarvam ASR API.
        
        Args:
            audio_data: Base64 encoded audio data
            language: Language code for transcription (not used as Sarvam auto-detects)
            
        Returns:
            Transcribed text
        """
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Use Sarvam ASR API
            files = {'file': ('input.wav', audio_bytes, 'audio/wav')}
            data = {
                'model': 'saarika:v2',
                'language_code': 'unknown'  # Sarvam auto-detects language
            }
            headers = {'api-subscription-key': self.api_key}

            response = requests.post('https://api.sarvam.ai/speech-to-text', files=files, data=data, headers=headers)

            if not response.ok:
                return f"ASR API request failed with status {response.status_code}: {response.text}"

            transcript = response.json().get("transcript", "")
            return transcript if transcript else "Sorry, I couldn't understand the audio."
                
        except Exception as e:
            return f"Audio transcription failed: {str(e)}"
    
    def detect_language(self, text: str) -> str:
        """Detect language using Sarvam LID API or fallback to character ranges"""
        if not text.strip():
            return "english"
            
        try:
            # Try Sarvam LID API first
            headers = {
                'api-subscription-key': self.api_key,
                'Content-Type': 'application/json'
            }
            payload = {'input': text}

            response = requests.post('https://api.sarvam.ai/text-lid', json=payload, headers=headers)

            if response.ok:
                result = response.json()
                # Extract language from LID response
                lang_code = result.get('language_code', 'en-IN')
                
                # Map Sarvam language codes to our internal format
                lang_mapping = {
                    'hi-IN': 'hindi',
                    'en-IN': 'english',
                    'ta-IN': 'tamil',
                    'te-IN': 'telugu',
                    'kn-IN': 'kannada',
                    'ml-IN': 'malayalam',
                    'gu-IN': 'gujarati',
                    'pa-IN': 'punjabi',
                    'mr-IN': 'marathi',
                    'bn-IN': 'bengali',
                    'or-IN': 'odia'
                }
                
                detected_lang = lang_mapping.get(lang_code, 'english')
                return detected_lang
                
        except Exception as e:
            # Fallback to character range detection
            pass
        
        # Character range detection fallback
        devanagari_range = range(0x0900, 0x097F)  # Hindi, Marathi
        tamil_range = range(0x0B80, 0x0BFF)  # Tamil
        telugu_range = range(0x0C00, 0x0C7F)  # Telugu
        kannada_range = range(0x0C80, 0x0CFF)  # Kannada
        malayalam_range = range(0x0D00, 0x0D7F)  # Malayalam
        gujarati_range = range(0x0A80, 0x0AFF)  # Gujarati
        punjabi_range = range(0x0A00, 0x0A7F)  # Punjabi
        bengali_range = range(0x0980, 0x09FF)  # Bengali
        odia_range = range(0x0B00, 0x0B7F)  # Odia

        script_counts = {
            'devanagari': 0, 'tamil': 0, 'telugu': 0, 'kannada': 0,
            'malayalam': 0, 'gujarati': 0, 'punjabi': 0, 'bengali': 0, 'odia': 0
        }

        for char in text:
            code = ord(char)
            if code in devanagari_range:
                script_counts['devanagari'] += 1
            elif code in tamil_range:
                script_counts['tamil'] += 1
            elif code in telugu_range:
                script_counts['telugu'] += 1
            elif code in kannada_range:
                script_counts['kannada'] += 1
            elif code in malayalam_range:
                script_counts['malayalam'] += 1
            elif code in gujarati_range:
                script_counts['gujarati'] += 1
            elif code in punjabi_range:
                script_counts['punjabi'] += 1
            elif code in bengali_range:
                script_counts['bengali'] += 1
            elif code in odia_range:
                script_counts['odia'] += 1

        max_script = max(script_counts, key=script_counts.get)
        max_count = script_counts[max_script]

        if max_count > 0:
            if max_script == 'devanagari':
                # Distinguish between Hindi and Marathi
                hindi_indicators = ['है', 'का', 'की', 'के', 'में', 'और', 'या', 'को', 'से', 'पर']
                marathi_indicators = ['आहे', 'च्या', 'ची', 'चे', 'मध्ये', 'आणि', 'किंवा', 'ला', 'पासून', 'वर']
                
                hindi_score = sum(1 for indicator in hindi_indicators if indicator in text)
                marathi_score = sum(1 for indicator in marathi_indicators if indicator in text)
                
                return "marathi" if marathi_score > hindi_score else "hindi"
            else:
                script_to_language = {
                    'tamil': 'tamil', 'telugu': 'telugu', 'kannada': 'kannada',
                    'malayalam': 'malayalam', 'gujarati': 'gujarati', 'punjabi': 'punjabi',
                    'bengali': 'bengali', 'odia': 'odia'
                }
                return script_to_language.get(max_script, 'english')

        return "english"

    def _clean_text_for_tts(self, text_input):
        """Clean text by removing markdown, emojis, and special characters"""
        if not text_input:
            return ""

        # Remove markdown formatting
        cleaned_text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', text_input)
        cleaned_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_text)
        cleaned_text = re.sub(r'\*(.*?)\*', r'\1', cleaned_text)
        cleaned_text = re.sub(r'^#+\s*', '', cleaned_text, flags=re.MULTILINE)

        # Remove emojis
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags
                                   u"\u2600-\u26FF"          # miscellaneous symbols
                                   u"\u2700-\u27BF"          # dingbats
                                   u"\uFE0F"                # variation selector
                                   u"\U0001F900-\U0001F9FF"  # supplemental symbols
                                   "]+", flags=re.UNICODE)
        cleaned_text = emoji_pattern.sub(r'', cleaned_text)

        # Replace multiple spaces with single space
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        cleaned_text = cleaned_text.replace('```', '')

        return cleaned_text

    async def generate_audio(self, text: str, language: str = "en") -> str:
        """
        Generate audio from text using Sarvam TTS API.
        
        Args:
            text: Text to convert to audio
            language: Language code for audio generation
            
        Returns:
            Base64 encoded audio data
        """
        try:
            # Clean the text
            cleaned_text = self._clean_text_for_tts(text)
            
            if not cleaned_text or not cleaned_text.strip():
                # Return silent WAV placeholder
                return "UklGRkoAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQYAAAAAAQ=="

            # Map language to Sarvam language code
            lang_code = self.language_mapping.get(language, "en-IN")
            
            # Use Sarvam TTS API
            headers = {
                'api-subscription-key': self.api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                'text': cleaned_text,
                'target_language_code': lang_code,
                'speaker': 'anushka',
                'model': 'bulbul:v2'
            }

            response = requests.post('https://api.sarvam.ai/text-to-speech', json=payload, headers=headers)

            if not response.ok:
                raise Exception(f"Sarvam TTS API request failed with status {response.status_code}: {response.text}")
            
            json_response = response.json()
            if not json_response.get('audios') or not json_response['audios'][0]:
                raise Exception("Sarvam TTS API response OK, but no audio data found.")

            base64_audio = json_response['audios'][0]
            
            if not base64_audio or len(base64_audio) < 100:
                raise Exception("Invalid or too short audio data received from Sarvam TTS.")
                
            return base64_audio
                    
        except Exception as e:
            raise Exception(f"Audio generation failed: {str(e)}")
    
    async def play_audio(self, audio_data: str) -> bool:
        """
        Play audio data (for testing purposes).
        Note: This is a placeholder - actual playback would depend on the client implementation.
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Success status
        """
        try:
            # Validate that we have valid base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # In a real implementation, this would:
            # 1. Send audio to client for playback
            # 2. Or use a server-side audio library
            # 3. Or save to a file for download
            
            # For now, just validate the data and return success
            if len(audio_bytes) > 100:  # Basic validation
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Audio playback validation failed: {str(e)}")
            return False
