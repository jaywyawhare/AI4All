const axios = require('axios');
const logger = require('../utils/logger');

class BackendService {
    constructor() {
        this.baseUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
        this.axios = axios.create({
            baseURL: this.baseUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async searchSchemes(query, user) {
        try {
            logger.info(`Searching schemes for user ${user.id}: ${query}`);
            
            const response = await this.axios.post('/tools/scheme_service/search_schemes', {
                query: query,
                user_age: user.age,
                user_gender: user.gender,
                user_state: user.state,
                user_caste: user.caste,
                is_minority: user.is_minority,
                is_differently_abled: user.is_differently_abled,
                is_bpl: user.is_bpl,
                is_student: user.is_student
            });
            
            return response.data;
        } catch (error) {
            logger.error('Error searching schemes:', error);
            throw error;
        }
    }

    async getCropAdvice(query, user) {
        try {
            logger.info(`Getting crop advice for user ${user.id}: ${query}`);
            
            const response = await this.axios.post('/tools/crop_service/get_crop_advice', {
                query: query,
                user_state: user.state,
                user_location: user.location
            });
            
            return response.data;
        } catch (error) {
            logger.error('Error getting crop advice:', error);
            throw error;
        }
    }

    async getWeatherInfo(query, user) {
        try {
            logger.info(`Getting weather info for user ${user.id}: ${query}`);
            
            const response = await this.axios.post('/tools/weather_service/get_weather_info', {
                query: query,
                user_state: user.state,
                user_location: user.location
            });
            
            return response.data;
        } catch (error) {
            logger.error('Error getting weather info:', error);
            throw error;
        }
    }

    async getHealthInfo(query, user) {
        try {
            logger.info(`Getting health info for user ${user.id}: ${query}`);
            
            const response = await this.axios.post('/tools/health_service/get_health_info', {
                query: query,
                user_id: user.id
            });
            
            return response.data;
        } catch (error) {
            logger.error('Error getting health info:', error);
            throw error;
        }
    }

    async analyzeHealthImage(imagePath, user) {
        try {
            logger.info(`Analyzing health image for user ${user.id}`);
            
            const FormData = require('form-data');
            const fs = require('fs');
            
            const form = new FormData();
            form.append('image', fs.createReadStream(imagePath));
            form.append('user_id', user.id);
            
            const response = await this.axios.post('/tools/health_service/analyze_health_image', form, {
                headers: {
                    ...form.getHeaders()
                }
            });
            
            return response.data;
        } catch (error) {
            logger.error('Error analyzing health image:', error);
            throw error;
        }
    }

    async analyzeHealthDocument(documentPath, user) {
        try {
            logger.info(`Analyzing health document for user ${user.id}`);
            
            const FormData = require('form-data');
            const fs = require('fs');
            
            const form = new FormData();
            form.append('document', fs.createReadStream(documentPath));
            form.append('user_id', user.id);
            
            const response = await this.axios.post('/tools/health_service/analyze_health_document', form, {
                headers: {
                    ...form.getHeaders()
                }
            });
            
            return response.data;
        } catch (error) {
            logger.error('Error analyzing health document:', error);
            throw error;
        }
    }

    async processAudio(audioPath, user) {
        try {
            logger.info(`Processing audio for user ${user.id}`);
            
            const FormData = require('form-data');
            const fs = require('fs');
            
            const form = new FormData();
            form.append('audio', fs.createReadStream(audioPath));
            form.append('user_id', user.id);
            form.append('language', user.preferred_language);
            
            const response = await this.axios.post('/tools/audio_service/process_audio', form, {
                headers: {
                    ...form.getHeaders()
                }
            });
            
            return response.data;
        } catch (error) {
            logger.error('Error processing audio:', error);
            throw error;
        }
    }
}

module.exports = BackendService;