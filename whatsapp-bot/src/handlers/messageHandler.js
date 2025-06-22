const { MessageTypes, MessageMedia } = require('whatsapp-web.js');
const logger = require('../utils/logger');
const BackendService = require('../services/backendService');
const SarvamService = require('../services/sarvamService');
const AudioProcessor = require('../utils/audioProcessor');
const User = require('../models/User');

class MessageHandler {
    constructor() {
        this.backendService = new BackendService();
        this.sarvamService = new SarvamService();
        this.audioProcessor = new AudioProcessor();
        
        this.messageTypes = {
            [MessageTypes.TEXT]: this.handleTextMessage,
            [MessageTypes.IMAGE]: this.handleImageMessage,
            [MessageTypes.VIDEO]: this.handleVideoMessage,
            [MessageTypes.AUDIO]: this.handleVoiceMessage,
            [MessageTypes.VOICE]: this.handleVoiceMessage,
            [MessageTypes.DOCUMENT]: this.handleDocumentMessage,
            [MessageTypes.STICKER]: this.handleStickerMessage
        };
    }

    async handleMessage(message, user) {
        try {
            const messageType = message.type;
            logger.info(`Processing ${messageType} message from user ${user.id}`);

            // Save message to database
            await User.saveMessage(user.id, messageType, message.body || null);

            // Handle message based on type
            const handler = this.messageTypes[messageType];
            if (!handler) {
                logger.warn(`Unsupported message type: ${messageType}`);
                return {
                    success: false,
                    error: 'Unsupported message type'
                };
            }

            const result = await handler.call(this, message, user);
            return {
                success: true,
                data: result
            };

        } catch (error) {
            logger.error('Error handling message:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async handleTextMessage(message, user) {
        try {
            const text = message.body.trim();
            
            // Check for commands
            if (text.startsWith('/')) {
                return await this.handleCommand(text, user);
            }

            // Process text through Sarvam AI for intent detection
            const intent = await this.sarvamService.detectIntent(text, user.preferred_language);
            
            // Call appropriate backend service based on intent
            const response = await this.processIntent(intent, text, user);
            
            return {
                type: 'text_response',
                content: response,
                language: user.preferred_language
            };

        } catch (error) {
            logger.error('Error handling text message:', error);
            throw error;
        }
    }

    async handleVoiceMessage(message, user) {
        try {
            // Download voice message
            const media = await message.downloadMedia();
            
            // Save audio file
            const audioFile = await this.audioProcessor.saveAudioFile(media, user.id);
            
            // Transcribe audio using Sarvam AI
            const transcription = await this.sarvamService.transcribeAudio(audioFile.path, user.preferred_language);
            
            if (!transcription.success) {
                throw new Error('Failed to transcribe audio');
            }

            // Detect intent from transcription
            const intent = await this.sarvamService.detectIntent(transcription.transcript, user.preferred_language);
            
            // Process intent through backend
            const response = await this.processIntent(intent, transcription.transcript, user);
            
            // Generate voice response
            const voiceResponse = await this.sarvamService.generateVoiceResponse(response, user.preferred_language);
            
            return {
                type: 'voice_response',
                text: response,
                audioPath: voiceResponse.audioPath,
                language: user.preferred_language
            };

        } catch (error) {
            logger.error('Error handling voice message:', error);
            throw error;
        }
    }

    async handleImageMessage(message, user) {
        try {
            const media = await message.downloadMedia();
            
            // Save image for health analysis
            const imageFile = await this.audioProcessor.saveImageFile(media, user.id);
            
            // Process image through health service
            const healthAnalysis = await this.backendService.analyzeHealthImage(imageFile.path, user);
            
            // Generate response using Sarvam AI
            const response = await this.sarvamService.generateHealthResponse(healthAnalysis, user.preferred_language);
            
            return {
                type: 'health_analysis',
                content: response,
                analysis: healthAnalysis,
                language: user.preferred_language
            };

        } catch (error) {
            logger.error('Error handling image message:', error);
            throw error;
        }
    }

    async handleVideoMessage(message, user) {
        try {
            const media = await message.downloadMedia();
            
            // For now, treat video as voice message (extract audio)
            const audioFile = await this.audioProcessor.extractAudioFromVideo(media, user.id);
            
            // Process as voice message
            return await this.handleVoiceMessage({
                ...message,
                downloadMedia: async () => ({ data: audioFile.data, mimetype: 'audio/ogg' })
            }, user);

        } catch (error) {
            logger.error('Error handling video message:', error);
            throw error;
        }
    }

    async handleDocumentMessage(message, user) {
        try {
            const media = await message.downloadMedia();
            
            // Check if it's a health document
            if (media.mimetype.includes('pdf') || media.mimetype.includes('image')) {
                const documentFile = await this.audioProcessor.saveDocumentFile(media, user.id);
                
                // Process through health service
                const healthAnalysis = await this.backendService.analyzeHealthDocument(documentFile.path, user);
                
                const response = await this.sarvamService.generateHealthResponse(healthAnalysis, user.preferred_language);
                
                return {
                    type: 'health_document',
                    content: response,
                    analysis: healthAnalysis,
                    language: user.preferred_language
                };
            }
            
            return {
                type: 'document',
                content: 'I can help you analyze health documents. Please send medical reports or images.',
                language: user.preferred_language
            };

        } catch (error) {
            logger.error('Error handling document message:', error);
            throw error;
        }
    }

    async handleStickerMessage(message, user) {
        try {
            const media = await message.downloadMedia();
            
            return {
                type: 'sticker',
                content: 'I received your sticker! I\'m designed to help with voice and text interactions. Please send a voice message or text for assistance.',
                language: user.preferred_language
            };

        } catch (error) {
            logger.error('Error handling sticker:', error);
            throw error;
        }
    }

    async handleCommand(command, user) {
        const cmd = command.toLowerCase();
        
        switch (cmd) {
            case '/help':
                return {
                    type: 'help',
                    content: `Available commands:
• Send voice message: Ask about government schemes, crop advice, weather, or health
• Send text message: Type your questions
• Send image: Upload medical images for analysis
• /language <code>: Change language (en, hi, ta, te, bn, mr, gu, kn, ml, pa)
• /voice <on/off>: Toggle voice responses
• /profile: View your profile`,
                    language: user.preferred_language
                };
                
            case '/profile':
                return {
                    type: 'profile',
                    content: `Your Profile:
• Name: ${user.name || 'Not set'}
• Language: ${user.preferred_language}
• Voice: ${user.voice_enabled ? 'Enabled' : 'Disabled'}
• State: ${user.state || 'Not set'}
• Age: ${user.age || 'Not set'}`,
                    language: user.preferred_language
                };
                
            default:
                if (cmd.startsWith('/language ')) {
                    const lang = cmd.split(' ')[1];
                    await User.updateLanguage(user.id, lang);
                    return {
                        type: 'language_update',
                        content: `Language updated to ${lang}`,
                        language: lang
                    };
                }
                
                if (cmd.startsWith('/voice ')) {
                    const voice = cmd.split(' ')[1];
                    await User.updateVoicePreference(user.id, voice === 'on');
                    return {
                        type: 'voice_update',
                        content: `Voice responses ${voice === 'on' ? 'enabled' : 'disabled'}`,
                        language: user.preferred_language
                    };
                }
                
                return {
                    type: 'unknown_command',
                    content: 'Unknown command. Type /help for available commands.',
                    language: user.preferred_language
                };
        }
    }

    async processIntent(intent, text, user) {
        try {
            switch (intent.type) {
                case 'scheme_search':
                    const schemes = await this.backendService.searchSchemes(text, user);
                    return await this.sarvamService.generateSchemeResponse(schemes, user.preferred_language);
                    
                case 'crop_advice':
                    const cropAdvice = await this.backendService.getCropAdvice(text, user);
                    return await this.sarvamService.generateCropResponse(cropAdvice, user.preferred_language);
                    
                case 'weather_info':
                    const weather = await this.backendService.getWeatherInfo(text, user);
                    return await this.sarvamService.generateWeatherResponse(weather, user.preferred_language);
                    
                case 'health_query':
                    const healthInfo = await this.backendService.getHealthInfo(text, user);
                    return await this.sarvamService.generateHealthResponse(healthInfo, user.preferred_language);
                    
                default:
                    return await this.sarvamService.generateGeneralResponse(text, user.preferred_language);
            }
        } catch (error) {
            logger.error('Error processing intent:', error);
            return 'Sorry, I encountered an error while processing your request. Please try again.';
        }
    }

    async sendResponse(message, responseData, user) {
        try {
            switch (responseData.type) {
                case 'text_response':
                case 'help':
                case 'profile':
                case 'language_update':
                case 'voice_update':
                case 'unknown_command':
                case 'health_analysis':
                case 'health_document':
                case 'sticker':
                    await message.reply(responseData.content);
                    break;
                    
                case 'voice_response':
                    // Send voice message
                    const media = MessageMedia.fromFilePath(responseData.audioPath);
                    await message.reply(media, { sendAudioAsVoice: true });
                    break;
                    
                default:
                    await message.reply(responseData.content || 'Response sent successfully.');
            }
        } catch (error) {
            logger.error('Error sending response:', error);
            await message.reply('Sorry, I encountered an error while sending the response.');
        }
    }
}

module.exports = new MessageHandler();