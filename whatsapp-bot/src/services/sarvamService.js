const axios = require('axios');
const logger = require('../utils/logger');
const fs = require('fs-extra');
const path = require('path');

class SarvamService {
    constructor() {
        this.apiKey = process.env.SARVAM_API_KEY;
        this.baseUrl = process.env.SARVAM_API_URL || 'https://api.sarvam.ai';
        this.axios = axios.create({
            baseURL: this.baseUrl,
            timeout: 60000,
            headers: {
                'api-subscription-key': this.apiKey,
                'Content-Type': 'application/json'
            }
        });
        
        // Language mapping for Sarvam API
        this.languageMapping = {
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
        };
    }

    async transcribeAudio(audioPath, language = 'en') {
        try {
            logger.info(`Transcribing audio: ${audioPath}`);
            
            const FormData = require('form-data');
            const form = new FormData();
            form.append('file', fs.createReadStream(audioPath), 'input.wav');
            form.append('model', 'saarika:v2');
            form.append('language_code', 'unknown'); // Sarvam auto-detects language
            
            const response = await this.axios.post('/speech-to-text', form, {
                headers: {
                    ...form.getHeaders(),
                    'api-subscription-key': this.apiKey
                }
            });
            
            if (!response.data.transcript) {
                return {
                    success: false,
                    error: "No transcript generated",
                    message: "Sorry, I couldn't understand the audio."
                };
            }
            
            return {
                success: true,
                transcript: response.data.transcript,
                detected_language: this.detectLanguage(response.data.transcript),
                model_used: "saarika:v2"
            };
        } catch (error) {
            logger.error('Error transcribing audio:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    detectLanguage(text) {
        if (!text || !text.trim()) {
            return "english";
        }
        
        try {
            // Character range detection fallback
            const devanagariRange = [0x0900, 0x097F];  // Hindi, Marathi
            const tamilRange = [0x0B80, 0x0BFF];  // Tamil
            const teluguRange = [0x0C00, 0x0C7F];  // Telugu
            const kannadaRange = [0x0C80, 0x0CFF];  // Kannada
            const malayalamRange = [0x0D00, 0x0D7F];  // Malayalam
            const gujaratiRange = [0x0A80, 0x0AFF];  // Gujarati
            const punjabiRange = [0x0A00, 0x0A7F];  // Punjabi
            const bengaliRange = [0x0980, 0x09FF];  // Bengali
            const odiaRange = [0x0B00, 0x0B7F];  // Odia

            const scriptCounts = {
                'devanagari': 0, 'tamil': 0, 'telugu': 0, 'kannada': 0,
                'malayalam': 0, 'gujarati': 0, 'punjabi': 0, 'bengali': 0, 'odia': 0
            };

            for (const char of text) {
                const code = char.charCodeAt(0);
                if (code >= devanagariRange[0] && code <= devanagariRange[1]) {
                    scriptCounts['devanagari']++;
                } else if (code >= tamilRange[0] && code <= tamilRange[1]) {
                    scriptCounts['tamil']++;
                } else if (code >= teluguRange[0] && code <= teluguRange[1]) {
                    scriptCounts['telugu']++;
                } else if (code >= kannadaRange[0] && code <= kannadaRange[1]) {
                    scriptCounts['kannada']++;
                } else if (code >= malayalamRange[0] && code <= malayalamRange[1]) {
                    scriptCounts['malayalam']++;
                } else if (code >= gujaratiRange[0] && code <= gujaratiRange[1]) {
                    scriptCounts['gujarati']++;
                } else if (code >= punjabiRange[0] && code <= punjabiRange[1]) {
                    scriptCounts['punjabi']++;
                } else if (code >= bengaliRange[0] && code <= bengaliRange[1]) {
                    scriptCounts['bengali']++;
                } else if (code >= odiaRange[0] && code <= odiaRange[1]) {
                    scriptCounts['odia']++;
                }
            }

            const maxScript = Object.entries(scriptCounts).reduce((a, b) => a[1] > b[1] ? a : b)[0];
            const maxCount = scriptCounts[maxScript];

            if (maxCount > 0) {
                if (maxScript === 'devanagari') {
                    // Distinguish between Hindi and Marathi
                    const hindiIndicators = ['है', 'का', 'की', 'के', 'में', 'और', 'या', 'को', 'से', 'पर'];
                    const marathiIndicators = ['आहे', 'च्या', 'ची', 'चे', 'मध्ये', 'आणि', 'किंवा', 'ला', 'पासून', 'वर'];
                    
                    const hindiScore = hindiIndicators.filter(indicator => text.includes(indicator)).length;
                    const marathiScore = marathiIndicators.filter(indicator => text.includes(indicator)).length;
                    
                    return marathiScore > hindiScore ? "marathi" : "hindi";
                } else {
                    const scriptToLanguage = {
                        'tamil': 'tamil', 'telugu': 'telugu', 'kannada': 'kannada',
                        'malayalam': 'malayalam', 'gujarati': 'gujarati', 'punjabi': 'punjabi',
                        'bengali': 'bengali', 'odia': 'odia'
                    };
                    return scriptToLanguage[maxScript] || 'english';
                }
            }

            return "english";
        } catch (error) {
            logger.error('Error detecting language:', error);
            return "english";
        }
    }

    async detectIntent(text, language = 'en') {
        try {
            logger.info(`Detecting intent for: ${text}`);
            
            // For now, use a simple keyword-based intent detection
            // In production, this would use Sarvam AI's intent detection API
            const lowerText = text.toLowerCase();
            
            if (lowerText.includes('scheme') || lowerText.includes('सरकारी') || lowerText.includes('योजना')) {
                return {
                    type: 'scheme_search',
                    confidence: 0.8,
                    entities: {}
                };
            } else if (lowerText.includes('crop') || lowerText.includes('फसल') || lowerText.includes('खेती')) {
                return {
                    type: 'crop_advice',
                    confidence: 0.8,
                    entities: {}
                };
            } else if (lowerText.includes('weather') || lowerText.includes('मौसम') || lowerText.includes('हवा')) {
                return {
                    type: 'weather_info',
                    confidence: 0.8,
                    entities: {}
                };
            } else if (lowerText.includes('health') || lowerText.includes('स्वास्थ्य') || lowerText.includes('डॉक्टर')) {
                return {
                    type: 'health_query',
                    confidence: 0.8,
                    entities: {}
                };
            } else {
                return {
                    type: 'general',
                    confidence: 0.5,
                    entities: {}
                };
            }
        } catch (error) {
            logger.error('Error detecting intent:', error);
            return {
                type: 'general',
                confidence: 0.5,
                entities: {}
            };
        }
    }

    async generateSchemeResponse(schemesData, language = 'en') {
        try {
            if (!schemesData.success || !schemesData.schemes || schemesData.schemes.length === 0) {
                return this._getNoResultsResponse('schemes', language);
            }

            const schemes = schemesData.schemes;
            const schemeNames = schemes.slice(0, 5).map(scheme => scheme.name || 'Unknown').join(', ');
            
            return `Found ${schemes.length} government schemes that match your criteria: ${schemeNames}. Please ask for more details about any specific scheme.`;
        } catch (error) {
            logger.error('Error generating scheme response:', error);
            return this._getFallbackResponse('schemes', language);
        }
    }

    async generateCropResponse(cropData, language = 'en') {
        try {
            if (!cropData.success) {
                return this._getNoResultsResponse('crop advice', language);
            }

            return `Here's your crop advice: ${JSON.stringify(cropData)}. This information should help you with your farming decisions.`;
        } catch (error) {
            logger.error('Error generating crop response:', error);
            return this._getFallbackResponse('crop advice', language);
        }
    }

    async generateWeatherResponse(weatherData, language = 'en') {
        try {
            if (!weatherData.success) {
                return this._getNoResultsResponse('weather information', language);
            }

            return `Here's the weather information: ${JSON.stringify(weatherData)}. This should help you plan your activities.`;
        } catch (error) {
            logger.error('Error generating weather response:', error);
            return this._getFallbackResponse('weather information', language);
        }
    }

    async generateHealthResponse(healthData, language = 'en') {
        try {
            if (!healthData.success) {
                return this._getNoResultsResponse('health information', language);
            }

            return `Here's the health information: ${JSON.stringify(healthData)}. Please consult a healthcare professional for medical advice.`;
        } catch (error) {
            logger.error('Error generating health response:', error);
            return this._getFallbackResponse('health information', language);
        }
    }

    async generateGeneralResponse(text, language = 'en') {
        try {
            return `I understand you're asking about: ${text}. I'm here to help with government schemes, crop advice, weather information, and health queries. Please let me know how I can assist you further.`;
        } catch (error) {
            logger.error('Error generating general response:', error);
            return this._getFallbackResponse('general', language);
        }
    }

    async generateVoiceResponse(text, language = 'en') {
        try {
            logger.info(`Generating voice response for: ${text.substring(0, 50)}...`);
            
            // Clean text for TTS
            const cleanedText = this._cleanTextForTTS(text);
            
            if (!cleanedText) {
                return {
                    success: false,
                    error: "No text provided for audio generation"
                };
            }
            
            // Map language to Sarvam format
            const sarvamLanguage = this.languageMapping[language.toLowerCase()] || "en-IN";
            
            const response = await this.axios.post('/text-to-speech', {
                text: cleanedText,
                model: 'saarika:v2',
                language_code: sarvamLanguage,
                voice: 'female'
            }, {
                responseType: 'arraybuffer',
                headers: {
                    'api-subscription-key': this.apiKey,
                    'Content-Type': 'application/json'
                }
            });
            
            // Save audio file
            const audioDir = path.join(process.cwd(), 'temp_audio');
            await fs.ensureDir(audioDir);
            
            const filename = `response_${Date.now()}.wav`;
            const audioPath = path.join(audioDir, filename);
            
            await fs.writeFile(audioPath, response.data);
            
            return {
                success: true,
                audioPath: audioPath,
                duration: this._estimateDuration(text),
                text: cleanedText,
                language: language,
                sarvam_language: sarvamLanguage,
                audio_size: response.data.length,
                model_used: "saarika:v2",
                voice: "female"
            };
        } catch (error) {
            logger.error('Error generating voice response:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async translateText(text, fromLanguage, toLanguage) {
        try {
            // For now, return the original text
            // In production, this would use Sarvam AI's translation API
            return {
                success: true,
                translated_text: text,
                confidence: 1.0
            };
        } catch (error) {
            logger.error('Error translating text:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    _cleanTextForTTS(text) {
        if (!text) return "";
        
        // Remove markdown formatting
        let cleanedText = text
            .replace(/\*\*\*(.*?)\*\*\*/g, '$1')
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\*(.*?)\*/g, '$1')
            .replace(/^#+\s*/gm, '');
        
        // Remove emojis
        cleanedText = cleanedText.replace(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{FE0F}]|[\u{1F900}-\u{1F9FF}]/gu, '');
        
        // Replace multiple spaces with single space
        cleanedText = cleanedText.replace(/\s+/g, ' ').trim();
        
        return cleanedText;
    }

    _getVoiceForLanguage(language) {
        const voices = {
            'en': 'en-IN-NeerjaNeural',
            'hi': 'hi-IN-SwaraNeural',
            'ta': 'ta-IN-PallaviNeural',
            'te': 'te-IN-ShrutiNeural',
            'bn': 'bn-IN-TanishaaNeural',
            'mr': 'mr-IN-AarohiNeural',
            'gu': 'gu-IN-DhwaniNeural',
            'kn': 'kn-IN-SapnaNeural',
            'ml': 'ml-IN-SobhanaNeural',
            'pa': 'pa-IN-Apnaneural'
        };
        
        return voices[language] || voices['en'];
    }

    _estimateDuration(text) {
        // Rough estimate: 150 words per minute
        const words = text.split(' ').length;
        return Math.ceil(words / 2.5); // seconds
    }

    _getNoResultsResponse(type, language) {
        const responses = {
            'en': `Sorry, I couldn't find any ${type} matching your request. Please try rephrasing your question.`,
            'hi': `माफ़ करें, मुझे आपके अनुरोध से मेल खाता कोई ${type} नहीं मिला। कृपया अपना प्रश्न दोबारा लिखें।`,
            'ta': `மன்னிக்கவும், உங்கள் கோரிக்கைக்கு பொருந்தும் ${type} எதுவும் கிடைக்கவில்லை. தயவுசெய்து உங்கள் கேள்வியை மாற்றி எழுதுங்கள்.`,
            'te': `క్షమించండి, మీ అభ్యర్థనకు సరిపోలే ${type} ఏదీ కనుగొనబడలేదు. దయచేసి మీ ప్రశ్నను తిరిగి రాయండి.`
        };
        
        return responses[language] || responses['en'];
    }

    _getFallbackResponse(type, language) {
        const responses = {
            'en': `I'm having trouble processing your ${type} request right now. Please try again in a moment.`,
            'hi': `मुझे अभी आपका ${type} अनुरोध संसाधित करने में समस्या हो रही है। कृपया कुछ देर बाद फिर से कोशिश करें।`,
            'ta': `உங்கள் ${type} கோரிக்கையை இப்போது செயலாக்குவதில் எனக்கு சிக்கல் உள்ளது. தயவுசெய்து சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கவும்.`,
            'te': `మీ ${type} అభ్యర్థనను ప్రస్తుతం ప్రాసెస్ చేయడంలో నాకు సమస్య ఉంది. దయచేసి కొంత సమయం తర్వాత మళ్లీ ప్రయత్నించండి.`
        };
        
        return responses[language] || responses['en'];
    }
}

module.exports = SarvamService; 