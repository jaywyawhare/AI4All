# WhatsApp Bot MCP Backend

This is the Model Context Protocol (MCP) backend server for the WhatsApp bot that provides comprehensive tools for government schemes, agricultural advice, health records management, and more.

## Features

The MCP server provides the following tools:

### 🎤 Audio Processing
- **Audio Transcription**: Convert voice messages to text in multiple Indian languages
- **Audio Generation**: Generate audio responses in user's native language

### 🖼️ Image Analysis
- **Medical Image Analysis**: Analyze wounds, diseases, and medical conditions using Gemini Vision
- **First Aid Suggestions**: Provide immediate first aid recommendations
- **General Image Analysis**: Answer questions about any image

### 🏥 Health Management
- **Health Records**: Comprehensive health record management using mem0
- **Prescription Management**: Store and track medical prescriptions
- **Hospital Finder**: Find nearest hospitals and medical facilities
- **Medical Report Explanation**: Explain doctor reports in native languages

### 🌾 Agricultural Support
- **Crop Prediction**: Predict crop patterns, rates, and optimal sowing times
- **Weather Integration**: Weather-based farming advice
- **Seasonal Calendar**: Crop calendar with seasonal recommendations
- **Agricultural Alerts**: Weather alerts specific to crops

### 🏛️ Government Schemes
- **Semantic Search**: AI-powered search for relevant government schemes
- **Parameter Filtering**: Filter schemes by age, gender, state, category
- **Detailed Information**: Complete scheme details and application process

### 🌤️ Weather Services
- **Weather Forecasts**: Detailed weather information for any location
- **Farming Advice**: Weather-based agricultural recommendations
- **Agricultural Alerts**: Crop-specific weather warnings

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Required API Keys:**
- `GEMINI_API_KEY`: Google Gemini API key for image/text analysis
- `WEATHER_API_KEY`: OpenWeatherMap API key
- `MEM0_API_KEY`: Mem0 API key for health records (optional)

## Usage

### Start the MCP Server

```bash
python start_server.py
```

The server will start on port 8085 by default.

### Configuration

Edit the `.env` file with your configuration:

```env
# MCP Server Configuration
MCP_PORT=8085
MCP_TOKEN=your-secure-mcp-token-here
PHONE_NUMBER=919876543210

# API Keys
GEMINI_API_KEY=your-gemini-api-key-here
WEATHER_API_KEY=your-openweather-api-key-here

# Other configurations...
```

### Connect WhatsApp Bot

Configure your WhatsApp bot to use this MCP server:

```javascript
// In your WhatsApp bot code
const mcpClient = new McpClient({
    baseUrl: 'http://localhost:8085',
    authToken: 'your-secure-mcp-token-here'
});
```

## API Tools

### Audio Transcription
```json
{
    "tool": "transcribe_audio",
    "parameters": {
        "audio_data": "base64_encoded_audio",
        "language": "hi"
    }
}
```

### Medical Image Analysis
```json
{
    "tool": "analyze_medical_image", 
    "parameters": {
        "image_data": "base64_encoded_image",
        "user_context": "wound on hand"
    }
}
```

### Scheme Search
```json
{
    "tool": "search_government_schemes",
    "parameters": {
        "query": "farmer scheme",
        "age": 35,
        "gender": "male", 
        "state": "maharashtra",
        "category": "general"
    }
}
```

### Health Records
```json
{
    "tool": "manage_health_record",
    "parameters": {
        "user_id": "user123",
        "action": "store",
        "data": "{\"personal_info\": {\"age\": 30, \"blood_group\": \"O+\"}}"
    }
}
```

## Supported Languages

The system supports multiple Indian languages:
- English (en)
- Hindi (hi) 
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Gujarati (gu)
- Malayalam (ml)
- Kannada (kn)
- Punjabi (pa)
- Marathi (mr)

## Database Structure

The system uses SQLite databases for:
- **Government Schemes**: Full-text search enabled scheme database
- **Health Records**: User health data and prescriptions
- **Vector Database**: For semantic search capabilities

## Error Handling

The server includes comprehensive error handling:
- API key validation
- Graceful degradation when services are unavailable
- Detailed error messages for debugging
- Fallback options for critical features

## Security

- Bearer token authentication for MCP server
- API key validation
- Input sanitization
- Secure file handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Troubleshooting

### Common Issues

1. **Import Errors**: Install requirements: `pip install -r requirements.txt`
2. **API Errors**: Check API keys in `.env` file
3. **Database Errors**: Check file permissions and disk space
4. **Port Conflicts**: Change `MCP_PORT` in `.env`

### Logs

Check server logs for detailed error information:
- Server startup logs printed to console
- Error details in stack traces
- API response errors logged

## Support

For support and questions:
- Check the troubleshooting section
- Review error logs
- Contact the development team

## License

This project is part of the WhatsApp Bot ecosystem for government services and agricultural support.
