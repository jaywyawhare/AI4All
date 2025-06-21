const { Pool } = require('pg');
const logger = require('../utils/logger');

class Database {
    constructor() {
        this.pool = null;
        this.retries = 3;
        this.retryDelay = 5000; 
        this.init();
    }

    init() {
        try {
            this.pool = new Pool({
                user: process.env.DB_USER || 'postgres',
                host: process.env.DB_HOST || 'localhost',
                database: process.env.DB_NAME || 'whatsapp_bot',
                password: process.env.DB_PASSWORD,
                port: process.env.DB_PORT || 5432,
                ssl: process.env.DB_SSL === 'true' ? {
                    rejectUnauthorized: false
                } : false,
                max: 20,
                idleTimeoutMillis: 30000,
                connectionTimeoutMillis: 2000,
            });

            this.pool.on('error', (err) => {
                logger.error('Unexpected database error:', err);
            });
        } catch (error) {
            logger.error('Database initialization error:', error);
            throw error;
        }
    }

    async query(text, params, retryCount = 0) {
        try {
            if (!this.pool) {
                this.init();
            }
            return await this.pool.query(text, params);
        } catch (error) {
            if (retryCount < this.retries && (error.code === 'ECONNREFUSED' || error.code === 'PROTOCOL_CONNECTION_LOST')) {
                logger.warn(`Database connection failed, retrying (${retryCount + 1}/${this.retries})...`);
                await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                return this.query(text, params, retryCount + 1);
            }
            throw error;
        }
    }
}

module.exports = new Database();