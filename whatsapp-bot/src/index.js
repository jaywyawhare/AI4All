require('dotenv').config();
const { Client, LocalAuth, MessageTypes } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const messageHandler = require('./handlers/messageHandler');
const logger = require('./utils/logger');
const User = require('./models/User');

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
    logger.info('Voice-first WhatsApp bot is ready!');
    logger.info('Bot supports: Voice messages, Text messages, Images, and Documents');
});

// Handle incoming messages
client.on('message', async (message) => {
    try {
        const wpUserId = message.from;
        logger.info(`Processing ${message.type} message from ${wpUserId}`);

        // Get or create user
        let user = await User.findByWpUserId(wpUserId);
        if (!user) {
            user = await User.createOrUpdate(wpUserId, {
                phoneNumber: wpUserId.replace('@c.us', ''),
                name: message._data.notifyName || 'Unknown'
            });
        }

        // Process message through handler
        const response = await messageHandler.handleMessage(message, user);
        
        if (!response.success) {
            logger.error(`Message processing failed: ${response.error}`);
            await message.reply('Sorry, I encountered an error while processing your message. Please try again.');
            return;
        }

        // Send response based on user preferences
        await messageHandler.sendResponse(message, response.data, user);

    } catch (error) {
        logger.error('Error in message handling:', error);
        await message.reply('Sorry, something went wrong while processing your message. Please try again.');
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