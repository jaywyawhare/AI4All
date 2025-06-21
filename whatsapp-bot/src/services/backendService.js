const axios = require('axios');
const logger = require('../utils/logger');

class BackendService {
    constructor() {
        this.baseUrl = process.env.BACKEND_API_URL || 'http://localhost:3000/api';
        this.axios = axios.create({
            baseURL: this.baseUrl,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async processMessage(userId, message) {
        try {
            logger.info(`Processing message for user ${userId}`);
            const response = await this.axios.post('/process-message', {
                userId,
                message
            });
            return response.data;
        } catch (error) {
            logger.error('Error processing message:', error);
            throw error;
        }
    }

    async storeMedia(userId, mediaType, mediaUrl) {
        try {
            logger.info(`Storing ${mediaType} for user ${userId}`);
            const response = await this.axios.post('/store-media', {
                userId,
                mediaType,
                mediaUrl
            });
            return response.data;
        } catch (error) {
            logger.error('Error storing media:', error);
            throw error;
        }
    }
}

module.exports = new BackendService();