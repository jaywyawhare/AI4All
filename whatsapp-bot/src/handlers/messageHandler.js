const { MessageTypes } = require('whatsapp-web.js');
const logger = require('../utils/logger');

class MessageHandler {
    constructor() {
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

    async handleMessage(message) {
        try {
            const wpUserId = message.from;
            const messageType = message.type;
            
            logger.info(`Received message of type: ${messageType} from ${wpUserId}`);

            // Handle message based on type
            const handler = this.messageTypes[messageType];
            if (!handler) {
                logger.warn(`Unsupported message type: ${messageType}`);
                return {
                    success: false,
                    error: 'Unsupported message type',
                    messageType
                };
            }

            const result = await handler.call(this, message);
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

    async handleTextMessage(message) {
        return {
            type: 'text',
            content: message.body
        };
    }

    async handleImageMessage(message) {
        const media = await message.downloadMedia();
        return {
            type: 'image',
            data: media.data,
            mimetype: media.mimetype
        };
    }

    async handleVideoMessage(message) {
        const media = await message.downloadMedia();
        return {
            type: 'video',
            data: media.data,
            mimetype: media.mimetype
        };
    }

    async handleVoiceMessage(message) {
        const media = await message.downloadMedia();
        return {
            type: 'voice',
            data: media.data,
            mimetype: media.mimetype
        };
    }

    async handleDocumentMessage(message) {
        const media = await message.downloadMedia();
        return {
            type: 'document',
            data: media.data,
            filename: media.filename,
            mimetype: media.mimetype
        };
    }

    async handleStickerMessage(message) {
        try {
            const media = await message.downloadMedia();
            const isAnimated = message.isGif || false;
            const hasQuotedMsg = message.hasQuotedMsg;
            
            logger.info(`Processing ${isAnimated ? 'animated' : 'static'} sticker`);

            // Get quoted message if exists
            let quotedMessage = null;
            if (hasQuotedMsg) {
                quotedMessage = await message.getQuotedMessage();
            }

            return {
                type: 'sticker',
                data: media.data,
                mimetype: media.mimetype,
                isAnimated: isAnimated,
                hasQuotedMessage: hasQuotedMsg,
                quotedMessageType: hasQuotedMsg ? quotedMessage.type : null,
                stickerAuthor: message.author || message.from,
                timestamp: message.timestamp
            };
        } catch (error) {
            logger.error('Error handling sticker:', error);
            throw new Error(`Failed to process sticker: ${error.message}`);
        }
    }
}

module.exports = new MessageHandler();