const db = require('../config/database');
const logger = require('../utils/logger');

class User {
    static async createOrUpdate(wpUserId, data = {}) {
        try {
            const { phoneNumber } = data;
            if (!phoneNumber) {
                throw new Error('Phone number is required');
            }
            
            const query = `
                INSERT INTO users (wp_user_id, phone_number)
                VALUES ($1, $2)
                ON CONFLICT (wp_user_id) 
                DO UPDATE SET
                    phone_number = EXCLUDED.phone_number
                RETURNING *;
            `;
            
            const values = [wpUserId, phoneNumber];
            const result = await db.query(query, values);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in createOrUpdate:', error);
            throw error;
        }
    }

    static async findByWpUserId(wpUserId) {
        try {
            const query = 'SELECT * FROM users WHERE wp_user_id = $1';
            const result = await db.query(query, [wpUserId]);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in findByWpUserId:', error);
            throw error;
        }
    }

    static async saveMessage(userId, messageType, content = null, mediaUrl = null) {
        try {
            const query = `
                INSERT INTO messages (user_id, message_type, content, media_url)
                VALUES ($1, $2, $3, $4)
                RETURNING *;
            `;
            const values = [userId, messageType, content, mediaUrl];
            const result = await db.query(query, values);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in saveMessage:', error);
            throw error;
        }
    }
}

module.exports = User;