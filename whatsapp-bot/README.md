# Voice-First WhatsApp Bot

A voice-first WhatsApp bot designed for Indian users, providing assistance with government schemes, crop advice, weather information, and health queries.

## Features

- **Voice-First Interaction**: Primary interface through voice messages with automatic transcription
- **Multi-Language Support**: Supports 10 Indian languages (English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi)
- **Government Scheme Search**: Find relevant government schemes based on user eligibility
- **Crop Sowing Advice**: Get personalized crop recommendations based on location and season
- **Weather Information**: Real-time weather updates for farming and daily activities
- **Health Query Support**: Basic health information and medical image analysis
- **Session Management**: Track user interactions and preferences
- **Audio File Management**: Automatic cleanup of temporary audio files

## Architecture

The bot follows a voice-first architecture with the following components:

1. **WhatsApp Client**: Handles WhatsApp Web.js integration
2. **Sarvam AI Integration**: Handles transcription, intent detection, and voice synthesis
3. **Backend MCP Tools**: Connects to Python backend for data processing
4. **PostgreSQL Database**: Stores user data, messages, and scheme information
5. **Audio Processing**: Manages temporary audio files and cleanup

## Setup Instructions

### Prerequisites

- Node.js 16+ and npm
- PostgreSQL 12+ with vector extension
- Sarvam AI API key
- Python backend running (see backend/README.md)

### Installation

1. **Install Dependencies**:
   ```bash
   cd whatsapp-bot
   npm install
   ```

2. **Database Setup**:
   ```bash
   # Create database and run schema
   psql -U postgres -d whatsapp_bot -f src/db/schema.sql
   ```

3. **Environment Configuration**:
   Create a `.env` file with the following variables:
   ```env
   # Database Configuration
   DB_USER=postgres
   DB_HOST=localhost
   DB_NAME=whatsapp_bot
   DB_PASSWORD=your_password_here
   DB_PORT=5432
   DB_SSL=false

   # Backend API Configuration
   BACKEND_API_URL=http://localhost:8000

   # Sarvam AI Configuration
   SARVAM_API_KEY=your_sarvam_api_key_here
   SARVAM_API_URL=https://api.sarvam.ai

   # Logging Configuration
   LOG_LEVEL=info
   LOG_FILE=whatsapp-bot.log
   ```

4. **Start the Bot**:
   ```bash
   npm start
   ```

5. **Authentication**:
   - Scan the QR code with WhatsApp
   - The bot will be ready to receive messages

## Usage

### Voice Messages (Primary Interface)
- Send voice messages asking about government schemes, crop advice, weather, or health
- The bot will transcribe, process, and respond with voice

### Text Messages
- Type questions directly
- Use commands like `/help`, `/profile`, `/language <code>`

### Images
- Send medical images for health analysis
- The bot will analyze and provide health information

### Commands
- `/help` - Show available commands
- `/profile` - View your profile
- `/language <code>` - Change language (en, hi, ta, te, bn, mr, gu, kn, ml, pa)
- `/voice <on/off>` - Toggle voice responses

## Database Schema

The bot uses the following main tables:

- **users**: User profiles and preferences
- **messages**: Message history and processing status
- **audio_files**: Audio file storage and metadata
- **user_sessions**: Session management
- **schemes**: Government scheme data
- **scheme_embeddings**: Vector embeddings for similarity search
- **user_scheme_matches**: User-scheme matching history

## File Structure

```
whatsapp-bot/
├── src/
│   ├── config/
│   │   └── database.js          # Database connection
│   │   └── config.js            # Configuration
│   ├── handlers/
│   │   └── messageHandler.js    # Message processing logic
│   ├── models/
│   │   └── User.js             # User data model
│   ├── services/
│   │   ├── backendService.js   # Backend API integration
│   │   └── sarvamService.js    # Sarvam AI integration
│   ├── utils/
│   │   ├── audioProcessor.js   # Audio file management
│   │   └── logger.js           # Logging utility
│   ├── db/
│   │   └── schema.sql          # Database schema
│   ├── app.js                  # Express app (if needed)
│   └── index.js                # Main entry point
├── temp_audio/                 # Temporary audio files
├── package.json
└── README.md
```

## API Integration

### Backend MCP Tools
The bot connects to the Python backend running MCP tools:
- `/tools/scheme_service/search_schemes` - Government scheme search
- `/tools/crop_service/get_crop_advice` - Crop recommendations
- `/tools/weather_service/get_weather_info` - Weather data
- `/tools/health_service/get_health_info` - Health queries
- `/tools/audio_service/process_audio` - Audio processing

### Sarvam AI Services
- Transcription: Convert voice to text
- Intent Detection: Understand user intent
- Response Generation: Generate contextual responses
- Voice Synthesis: Convert text to voice
- Translation: Multi-language support

## Error Handling

The bot includes comprehensive error handling:
- Graceful fallbacks for API failures
- Automatic retry mechanisms
- User-friendly error messages
- Detailed logging for debugging

## Performance Optimization

- Automatic cleanup of temporary files
- Database connection pooling
- Efficient audio file management
- Session-based user tracking

## Security Considerations

- Environment variable configuration
- Database connection security
- API key management
- Temporary file cleanup
- User data privacy

## Troubleshooting

### Common Issues

1. **QR Code Not Appearing**: Check internet connection and WhatsApp Web.js version
2. **Database Connection Failed**: Verify PostgreSQL is running and credentials are correct
3. **Audio Processing Errors**: Check Sarvam AI API key and network connectivity
4. **Backend Connection Failed**: Ensure Python backend is running on correct port

### Logs

Check the log file for detailed error information:
```bash
tail -f whatsapp-bot.log
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive error handling
3. Update documentation for new features
4. Test with multiple languages and scenarios

## License

This project is part of the Warpspeed voice-first WhatsApp bot system. 