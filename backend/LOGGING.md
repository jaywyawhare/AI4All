# Backend Logging System

This document describes the comprehensive logging system implemented for the Voice-First WhatsApp Bot backend.

## Overview

The backend uses a centralized logging system that provides:
- **Service-specific logging** for each component
- **Rotating log files** to manage disk space
- **Multiple log levels** (DEBUG, INFO, WARNING, ERROR)
- **Structured logging** with timestamps and service names
- **Console and file output** for development and production

## Log Files Structure

```
logs/
├── all_services_YYYYMMDD.log    # All services combined
├── errors_YYYYMMDD.log          # Error-level logs only
├── main_YYYYMMDD.log            # Main server logs
├── audio_service_YYYYMMDD.log   # Audio service logs
├── gemini_service_YYYYMMDD.log  # Gemini service logs
├── weather_service_YYYYMMDD.log # Weather service logs
├── crop_service_YYYYMMDD.log    # Crop service logs
├── health_service_YYYYMMDD.log  # Health service logs
├── scheme_service_YYYYMMDD.log  # Scheme service logs
└── sarvam_service_YYYYMMDD.log  # Sarvam AI service logs
```

## Log Levels

### DEBUG
- Detailed information for debugging
- Function entry/exit points
- Variable values and state changes
- API request/response details

### INFO
- General operational information
- Service initialization
- Successful operations
- Performance metrics

### WARNING
- Non-critical issues
- Deprecated feature usage
- Performance degradation
- External service warnings

### ERROR
- Critical errors
- Service failures
- API errors
- System exceptions

## Service-Specific Logging

### Audio Service (`audio_service`)
- Audio transcription requests and results
- Audio generation requests and results
- File management operations
- API call details and responses
- Language detection results

### Gemini Service (`gemini_service`)
- Medical image analysis requests
- API authentication and initialization
- Image processing steps
- Response generation details
- Error handling for medical analysis

### Weather Service (`weather_service`)
- Weather forecast requests
- Location geocoding
- API responses and data processing
- Cache hits/misses
- External API errors

### Crop Service (`crop_service`)
- Crop advice requests
- Weather data integration
- Recommendation generation
- Seasonal calculations
- Market price predictions

### Health Service (`health_service`)
- Health record operations
- Medical report explanations
- Hospital search requests
- Mem0 database operations
- Privacy and security events

### Scheme Service (`scheme_service`)
- Government scheme searches
- Vector similarity calculations
- Database query performance
- Filter applications
- Result ranking and scoring

### Main Server (`main`)
- MCP tool registrations
- Server startup/shutdown
- Tool execution requests
- Error handling and recovery
- Performance monitoring

## Usage Examples

### Basic Logging
```python
from config.logging import get_logger

logger = get_logger('my_service')

logger.info("Service started successfully")
logger.debug("Processing request with parameters: %s", params)
logger.warning("API rate limit approaching")
logger.error("Failed to connect to database: %s", error)
```

### Tool-Specific Logging
```python
@mcp.tool()
async def my_tool(param: str) -> str:
    logger = get_logger('my_service')
    
    try:
        logger.info(f"Tool execution started with param: {param}")
        
        # Tool logic here
        result = await process_request(param)
        
        logger.info(f"Tool execution completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Tool execution failed: {str(e)}")
        raise
```

## Configuration

### Log File Rotation
- **Max file size**: 10MB for general logs, 5MB for service-specific logs
- **Backup count**: 5 for general logs, 3 for service-specific logs
- **Daily rotation**: New log files created daily

### External Library Logging
The following external libraries have their log levels set to WARNING to reduce noise:
- `httpx` - HTTP client library
- `requests` - HTTP requests library
- `urllib3` - HTTP client library
- `asyncio` - Async I/O library

## Testing Logging

Run the logging test script to verify all services are logging correctly:

```bash
cd backend
python test_logging.py
```

This will:
1. Test logging for all services
2. Create sample log entries
3. Verify log file creation
4. Display created log files

## Help Menu Tool

The backend includes a comprehensive help menu tool that provides:

### Features
- **Multi-language support** (English, Hindi)
- **Voice-first feature descriptions**
- **Tool usage instructions**
- **Quick commands reference**
- **Emergency information**

### Usage
```python
# Get help menu in English
help_menu = await get_help_menu("en")

# Get help menu in Hindi
help_menu = await get_help_menu("hi")
```

### Help Menu Sections
1. **Voice Features** - Audio transcription and generation
2. **AI Features** - Sarvam AI integration and translation
3. **Government Schemes** - Scheme search and filtering
4. **Health Features** - Medical analysis and records
5. **Agriculture Features** - Crop advice and weather
6. **Weather Features** - Forecasts and farming advice
7. **Usage Tips** - Best practices and guidelines
8. **Quick Commands** - Voice commands reference

## Monitoring and Debugging

### Real-time Monitoring
```bash
# Monitor all logs in real-time
tail -f logs/all_services_$(date +%Y%m%d).log

# Monitor errors only
tail -f logs/errors_$(date +%Y%m%d).log

# Monitor specific service
tail -f logs/audio_service_$(date +%Y%m%d).log
```

### Log Analysis
```bash
# Count errors by service
grep "ERROR" logs/all_services_*.log | cut -d' ' -f3 | sort | uniq -c

# Find slow operations
grep "processing_time" logs/all_services_*.log

# Search for specific errors
grep "API.*failed" logs/all_services_*.log
```

## Best Practices

1. **Use appropriate log levels**
   - DEBUG for detailed debugging
   - INFO for general operations
   - WARNING for potential issues
   - ERROR for actual problems

2. **Include context in log messages**
   - User IDs for user-specific operations
   - Request parameters for API calls
   - Performance metrics for slow operations

3. **Handle sensitive data**
   - Never log passwords or API keys
   - Mask personal information in logs
   - Use placeholders for sensitive data

4. **Monitor log file sizes**
   - Check disk space regularly
   - Archive old log files
   - Clean up temporary files

## Troubleshooting

### Common Issues

1. **Log files not created**
   - Check directory permissions
   - Verify logs directory exists
   - Ensure proper import of logging module

2. **High log volume**
   - Adjust log levels for external libraries
   - Use DEBUG level sparingly in production
   - Implement log filtering

3. **Performance impact**
   - Use async logging where possible
   - Avoid expensive operations in log messages
   - Consider log buffering for high-frequency operations

### Debug Commands
```bash
# Check log file permissions
ls -la logs/

# Verify log rotation
ls -la logs/ | grep -E "\.log$"

# Check disk usage
du -sh logs/

# Monitor log file growth
watch -n 5 'ls -lh logs/'
``` 