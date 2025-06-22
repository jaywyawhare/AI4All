import os
import base64
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import re
import io
import wave
import shutil
from datetime import datetime, timedelta
import glob

from config.settings import Settings
from config.logging import get_logger

# Initialize logger for audio service
logger = get_logger('audio_service')

class AudioService:
    """Service for handling audio transcription and generation using Sarvam APIs."""
    
    def __init__(self):
        self.settings = Settings()
        # Get Sarvam API key from settings or environment
        self.api_key = getattr(self.settings, 'SARVAM_API_KEY', None) or os.getenv('SARVAM_API_KEY')
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY not found in settings or environment variables")
        
        # Create temp audio directory
        self.temp_audio_dir = Path.cwd() / "temp_audio"
        self.temp_audio_dir.mkdir(exist_ok=True)
        
        # Audio file rotation settings
        self.max_temp_files = 100  # Maximum number of temp files to keep
        self.max_file_age_hours = 24  # Maximum age of temp files in hours
        
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
    
    def _cleanup_temp_files(self):
        """Clean up old temporary audio files based on age and count."""
        try:
            logger.debug("Starting temp file cleanup...")
            
            # Get all temp audio files
            temp_files = list(self.temp_audio_dir.glob("*.wav")) + list(self.temp_audio_dir.glob("*.mp3"))
            initial_count = len(temp_files)
            logger.debug(f"Found {initial_count} temp files")
            
            # Remove files older than max_file_age_hours
            cutoff_time = datetime.now() - timedelta(hours=self.max_file_age_hours)
            removed_by_age = 0
            for file_path in temp_files:
                if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_time:
                    file_path.unlink()
                    removed_by_age += 1
            
            if removed_by_age > 0:
                logger.info(f"Removed {removed_by_age} files older than {self.max_file_age_hours} hours")
            
            # If still too many files, remove oldest ones
            temp_files = list(self.temp_audio_dir.glob("*.wav")) + list(self.temp_audio_dir.glob("*.mp3"))
            if len(temp_files) > self.max_temp_files:
                # Sort by modification time (oldest first)
                temp_files.sort(key=lambda x: x.stat().st_mtime)
                # Remove oldest files
                files_to_remove = temp_files[:-self.max_temp_files]
                for file_path in files_to_remove:
                    file_path.unlink()
                logger.info(f"Removed {len(files_to_remove)} oldest files to maintain limit")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
    
    def _save_temp_audio(self, audio_bytes: bytes, prefix: str = "audio") -> str:
        """Save audio bytes to temporary file and return file path."""
        try:
            # Cleanup old files first
            self._cleanup_temp_files()
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{prefix}_{timestamp}.wav"
            file_path = self.temp_audio_dir / filename
            
            # Save audio file
            with open(file_path, 'wb') as f:
                f.write(audio_bytes)
            
            return str(file_path)
            
        except Exception as e:
            print(f"Error saving temp audio: {e}")
            return ""
    
    def _load_temp_audio(self, file_path: str) -> Optional[bytes]:
        """Load audio bytes from temporary file."""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading temp audio: {e}")
            return None
    
    def _delete_temp_audio(self, file_path: str) -> bool:
        """Delete temporary audio file."""
        try:
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception as e:
            print(f"Error deleting temp audio: {e}")
            return False
    
    async def transcribe(self, audio_data: str, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio to text using Sarvam ASR API.
        
        Args:
            audio_data: Base64 encoded audio data
            language: Language code for transcription (not used as Sarvam auto-detects)
            
        Returns:
            Raw transcription data
        """
        try:
            logger.info(f"Starting audio transcription for language: {language}")
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            logger.debug(f"Decoded audio data, size: {len(audio_bytes)} bytes")
            
            # Save to temp file
            temp_file_path = self._save_temp_audio(audio_bytes, "input")
            logger.debug(f"Saved audio to temp file: {temp_file_path}")
            
            # Use Sarvam ASR API
            files = {'file': ('input.wav', audio_bytes, 'audio/wav')}
            data = {
                'model': 'saarika:v2',
                'language_code': 'unknown'  # Sarvam auto-detects language
            }
            headers = {'api-subscription-key': self.api_key}

            logger.info("Making request to Sarvam ASR API...")
            response = requests.post('https://api.sarvam.ai/speech-to-text', files=files, data=data, headers=headers)

            if not response.ok:
                logger.error(f"ASR API request failed with status {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"ASR API request failed with status {response.status_code}",
                    "response_text": response.text
                }

            transcript = response.json().get("transcript", "")
            logger.info(f"Transcription successful, transcript length: {len(transcript)}")
            
            if not transcript:
                logger.warning("No transcript generated from audio")
                return {
                    "success": False,
                    "error": "No transcript generated",
                    "message": "Sorry, I couldn't understand the audio."
                }
            
            # Detect language from transcript
            detected_language = self.detect_language(transcript)
            logger.info(f"Detected language: {detected_language}")
            
            return {
                "success": True,
                "transcript": transcript,
                "detected_language": detected_language,
                "audio_size": len(audio_bytes),
                "temp_file_path": temp_file_path,
                "model_used": "saarika:v2"
            }
                
        except Exception as e:
            logger.error(f"Audio transcription failed: {str(e)}")
            return {
                "success": False,
                "error": f"Audio transcription failed: {str(e)}"
            }
    
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

        max_script = max(script_counts.items(), key=lambda x: x[1])[0]
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
        
        return cleaned_text

    async def generate_audio(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Generate audio from text using Sarvam TTS API.
        
        Args:
            text: Text to convert to speech
            language: Language code for TTS
            
        Returns:
            Raw audio generation data
        """
        try:
            logger.info(f"Starting audio generation for language: {language}, text length: {len(text)}")
            
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            logger.debug(f"Cleaned text length: {len(cleaned_text)}")
            
            if not cleaned_text:
                logger.warning("No text provided for audio generation")
                return {
                    "success": False,
                    "error": "No text provided for audio generation"
                }
            
            # Map language to Sarvam format
            sarvam_language = self.language_mapping.get(language.lower(), "en-IN")
            logger.debug(f"Mapped language {language} to Sarvam format: {sarvam_language}")
            
            # Use Sarvam TTS API
            headers = {
                'api-subscription-key': self.api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                'text': cleaned_text,
                'model': 'saarika:v2',
                'language_code': sarvam_language,
                'voice': 'female'  # Default to female voice
            }

            logger.info("Making request to Sarvam TTS API...")
            response = requests.post('https://api.sarvam.ai/text-to-speech', json=payload, headers=headers)

            if not response.ok:
                logger.error(f"TTS API request failed with status {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"TTS API request failed with status {response.status_code}",
                    "response_text": response.text
                }

            # Get audio data from response
            audio_data = response.content
            logger.info(f"Audio generation successful, audio size: {len(audio_data)} bytes")
            
            # Save to temp file
            temp_file_path = self._save_temp_audio(audio_data, "output")
            logger.debug(f"Saved generated audio to temp file: {temp_file_path}")
            
            # Convert to base64 for storage/transmission
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "success": True,
                "audio_data": audio_base64,
                "temp_file_path": temp_file_path,
                "text": cleaned_text,
                "language": language,
                "sarvam_language": sarvam_language,
                "audio_size": len(audio_data),
                "model_used": "saarika:v2",
                "voice": "female"
            }
                    
        except Exception as e:
            logger.error(f"Audio generation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Audio generation failed: {str(e)}"
            }
    
    async def play_audio(self, audio_data: str) -> Dict[str, Any]:
        """
        Play audio (placeholder for future implementation).
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Play status
        """
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Save to temp file for playback
            temp_file_path = self._save_temp_audio(audio_bytes, "playback")
            
            # Placeholder implementation
            return {
                "success": True,
                "message": "Audio play feature not implemented",
                "temp_file_path": temp_file_path,
                "audio_size": len(audio_bytes)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Audio play failed: {str(e)}"
            }
    
    async def cleanup_temp_files(self) -> Dict[str, Any]:
        """Manually trigger cleanup of temporary audio files."""
        try:
            logger.info("Manual temp file cleanup requested")
            initial_count = len(list(self.temp_audio_dir.glob("*")))
            self._cleanup_temp_files()
            final_count = len(list(self.temp_audio_dir.glob("*")))
            
            files_removed = initial_count - final_count
            logger.info(f"Cleanup completed: {files_removed} files removed, {final_count} remaining")
            
            return {
                "success": True,
                "files_removed": files_removed,
                "remaining_files": final_count,
                "temp_directory": str(self.temp_audio_dir)
            }
                
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return {
                "success": False,
                "error": f"Cleanup failed: {str(e)}"
            }
    
    def get_temp_file_info(self) -> Dict[str, Any]:
        """Get information about temporary audio files."""
        try:
            temp_files = list(self.temp_audio_dir.glob("*"))
            file_info = []
            
            for file_path in temp_files:
                stat = file_path.stat()
                file_info.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_hours": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
                })
            
            return {
                "success": True,
                "temp_directory": str(self.temp_audio_dir),
                "total_files": len(file_info),
                "files": file_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get temp file info: {str(e)}"
            }
