require('dotenv').config();
const { Client, LocalAuth, MessageTypes } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const messageHandler = require('./handlers/messageHandler');
const logger = require('./utils/logger');

// Initialize WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox']
    }
});

// Generate QR code for authentication
client.on('qr', (qr) => {
    logger.info('QR code received');
    qrcode.generate(qr, {small: true});
});

client.on('ready', () => {
    logger.info('WhatsApp bot is ready!');
});

// Handle incoming messages
client.on('message', async (message) => {
    try {
        logger.info(`Processing message from ${message.from}`);
        const response = await messageHandler.handleMessage(message);
        
        if (!response.success) {
            if (response.messageType) {
                await message.reply(`Sorry, I don't handle ${response.messageType} messages yet.`);
            } else {
                await message.reply('Sorry, I encountered an error while processing your message.');
            }
            return;
        }

        // Handle successful response based on type
        switch (response.data.type) {
            case 'text':
                await message.reply(`Received your message: ${response.data.content}`);
                break;
            case 'sticker':
                const stickerInfo = response.data.isAnimated ? 'animated' : 'static';
                const quotedInfo = response.data.hasQuotedMessage ? 
                    ` (in reply to a ${response.data.quotedMessageType} message)` : '';
                await message.reply(`Received your ${stickerInfo} sticker${quotedInfo}!`);
                break;
            default:
                await message.reply(`Received and processed your ${response.data.type} successfully.`);
        }
        
    } catch (error) {
        logger.error('Error in message handling:', error);
        await message.reply('Sorry, something went wrong while processing your message.');
    }
});

// Handle authentication failures
client.on('auth_failure', () => {
    logger.error('Authentication failed');
});

// Handle client disconnection
client.on('disconnected', (reason) => {
    logger.warn('Client disconnected:', reason);
});

// Handle errors
client.on('error', (error) => {
    logger.error('WhatsApp client error:', error);
});

// Initialize the client
client.initialize();