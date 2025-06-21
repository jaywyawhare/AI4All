import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Configuration settings for the MCP server."""
    
    # Server configuration
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8085"))
    MCP_TOKEN: str = os.getenv("MCP_TOKEN", "")
    PHONE_NUMBER: str = os.getenv("PHONE_NUMBER", "")
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///whatsapp_bot.db")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    
    # Health service configuration
    MEM0_API_KEY: str = os.getenv("MEM0_API_KEY", "")
    
    # File storage
    AUDIO_STORAGE_PATH: str = os.getenv("AUDIO_STORAGE_PATH", "./data/audio")
    IMAGE_STORAGE_PATH: str = os.getenv("IMAGE_STORAGE_PATH", "./data/images")
    
    # External APIs
    CROP_API_URL: str = os.getenv("CROP_API_URL", "")
    HOSPITAL_API_URL: str = os.getenv("HOSPITAL_API_URL", "")
    
    # Language settings
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES: list = ["en", "hi", "ta", "te", "bn", "gu", "ml", "kn", "pa", "mr"]
    
    def __init__(self):
        """Initialize settings and create necessary directories."""
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        Path(self.VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.AUDIO_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.IMAGE_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(parents=True, exist_ok=True)
