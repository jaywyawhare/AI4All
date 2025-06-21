require('dotenv').config();
const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const { handleMessage } = require('./handlers/messageHandler');
const { setupLogging } = require('./utils/logger');

const app = express();
const logger = setupLogging();

// Initialize WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox']
    }
});

// WhatsApp client events
client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
    logger.info('QR Code generated');
});

client.on('ready', () => {
    logger.info('WhatsApp client is ready');
});

client.on('message', async (message) => {
    try {
        await handleMessage(message, client);
    } catch (error) {
        logger.error('Error handling message:', error);
    }
});

client.on('disconnected', (reason) => {
    logger.warn('WhatsApp client disconnected:', reason);
    process.exit(1); // Let process manager restart
});

// Basic health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok' });
});

// Start server
const PORT = process.env.PORT || 3000;

const startServer = async () => {
    try {
        await client.initialize();
        
        app.listen(PORT, () => {
            logger.info(`Server running on port ${PORT}`);
        });
    } catch (error) {
        logger.error('Failed to start server:', error);
        process.exit(1);
    }
};

startServer();