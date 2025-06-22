const db = require('../config/database');
const logger = require('../utils/logger');

class User {
    static async createOrUpdate(wpUserId, data = {}) {
        try {
            const { phoneNumber, name, age, gender, state, income, caste, 
                    is_minority, is_differently_abled, is_bpl, is_student } = data;
            
            if (!phoneNumber) {
                throw new Error('Phone number is required');
            }
            
            const query = `
                INSERT INTO users (
                    wp_user_id, phone_number, name, age, gender, state, income, 
                    caste, is_minority, is_differently_abled, is_bpl, is_student,
                    preferred_language, voice_enabled, last_interaction
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, CURRENT_TIMESTAMP)
                ON CONFLICT (wp_user_id) 
                DO UPDATE SET
                    phone_number = EXCLUDED.phone_number,
                    name = COALESCE(EXCLUDED.name, users.name),
                    age = COALESCE(EXCLUDED.age, users.age),
                    gender = COALESCE(EXCLUDED.gender, users.gender),
                    state = COALESCE(EXCLUDED.state, users.state),
                    income = COALESCE(EXCLUDED.income, users.income),
                    caste = COALESCE(EXCLUDED.caste, users.caste),
                    is_minority = COALESCE(EXCLUDED.is_minority, users.is_minority),
                    is_differently_abled = COALESCE(EXCLUDED.is_differently_abled, users.is_differently_abled),
                    is_bpl = COALESCE(EXCLUDED.is_bpl, users.is_bpl),
                    is_student = COALESCE(EXCLUDED.is_student, users.is_student),
                    last_interaction = CURRENT_TIMESTAMP
                RETURNING *;
            `;
            
            const values = [
                wpUserId, phoneNumber, name, age, gender, state, income,
                caste, is_minority, is_differently_abled, is_bpl, is_student,
                data.preferred_language || 'en', data.voice_enabled !== false
            ];
            
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

    static async findById(userId) {
        try {
            const query = 'SELECT * FROM users WHERE id = $1';
            const result = await db.query(query, [userId]);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in findById:', error);
            throw error;
        }
    }

    static async updateLanguage(userId, language) {
        try {
            const query = `
                UPDATE users 
                SET preferred_language = $2, last_interaction = CURRENT_TIMESTAMP
                WHERE id = $1
                RETURNING *;
            `;
            const result = await db.query(query, [userId, language]);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in updateLanguage:', error);
            throw error;
        }
    }

    static async updateVoicePreference(userId, voiceEnabled) {
        try {
            const query = `
                UPDATE users 
                SET voice_enabled = $2, last_interaction = CURRENT_TIMESTAMP
                WHERE id = $1
                RETURNING *;
            `;
            const result = await db.query(query, [userId, voiceEnabled]);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in updateVoicePreference:', error);
            throw error;
        }
    }

    static async updateProfile(userId, profileData) {
        try {
            const { name, age, gender, state, income, caste, 
                    is_minority, is_differently_abled, is_bpl, is_student } = profileData;
            
            const query = `
                UPDATE users 
                SET name = COALESCE($2, name),
                    age = COALESCE($3, age),
                    gender = COALESCE($4, gender),
                    state = COALESCE($5, state),
                    income = COALESCE($6, income),
                    caste = COALESCE($7, caste),
                    is_minority = COALESCE($8, is_minority),
                    is_differently_abled = COALESCE($9, is_differently_abled),
                    is_bpl = COALESCE($10, is_bpl),
                    is_student = COALESCE($11, is_student),
                    last_interaction = CURRENT_TIMESTAMP
                WHERE id = $1
                RETURNING *;
            `;
            
            const values = [userId, name, age, gender, state, income, 
                          caste, is_minority, is_differently_abled, is_bpl, is_student];
            
            const result = await db.query(query, values);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in updateProfile:', error);
            throw error;
        }
    }

    static async saveMessage(userId, messageType, content = null, mediaUrl = null, language = null) {
        try {
            const query = `
                INSERT INTO messages (user_id, message_type, content, media_url, language, timestamp)
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                RETURNING *;
            `;
            const values = [userId, messageType, content, mediaUrl, language];
            const result = await db.query(query, values);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in saveMessage:', error);
            throw error;
        }
    }

    static async getMessageHistory(userId, limit = 10) {
        try {
            const query = `
                SELECT * FROM messages 
                WHERE user_id = $1 
                ORDER BY timestamp DESC 
                LIMIT $2;
            `;
            const result = await db.query(query, [userId, limit]);
            return result.rows;
        } catch (error) {
            logger.error('Error in getMessageHistory:', error);
            throw error;
        }
    }

    static async createSession(userId) {
        try {
            const sessionId = require('crypto').randomBytes(32).toString('hex');
            const query = `
                INSERT INTO user_sessions (user_id, session_id, is_active, last_activity)
                VALUES ($1, $2, true, CURRENT_TIMESTAMP)
                RETURNING *;
            `;
            const result = await db.query(query, [userId, sessionId]);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in createSession:', error);
            throw error;
        }
    }

    static async updateSessionActivity(sessionId) {
        try {
            const query = `
                UPDATE user_sessions 
                SET last_activity = CURRENT_TIMESTAMP
                WHERE session_id = $1
                RETURNING *;
            `;
            const result = await db.query(query, [sessionId]);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in updateSessionActivity:', error);
            throw error;
        }
    }

    static async deactivateSession(sessionId) {
        try {
            const query = `
                UPDATE user_sessions 
                SET is_active = false
                WHERE session_id = $1
                RETURNING *;
            `;
            const result = await db.query(query, [sessionId]);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in deactivateSession:', error);
            throw error;
        }
    }

    static async getActiveSession(userId) {
        try {
            const query = `
                SELECT * FROM user_sessions 
                WHERE user_id = $1 AND is_active = true
                ORDER BY last_activity DESC 
                LIMIT 1;
            `;
            const result = await db.query(query, [userId]);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in getActiveSession:', error);
            throw error;
        }
    }

    static async saveSchemeMatch(userId, schemeId, score, matchedBy) {
        try {
            const query = `
                INSERT INTO user_scheme_matches (user_id, scheme_id, score, matched_by, matched_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                RETURNING *;
            `;
            const values = [userId, schemeId, score, matchedBy];
            const result = await db.query(query, values);
            return result.rows[0];
        } catch (error) {
            logger.error('Error in saveSchemeMatch:', error);
            throw error;
        }
    }

    static async getSchemeMatches(userId, limit = 10) {
        try {
            const query = `
                SELECT usm.*, s.name as scheme_name, s.category, s.state
                FROM user_scheme_matches usm
                JOIN schemes s ON usm.scheme_id = s.id
                WHERE usm.user_id = $1
                ORDER BY usm.matched_at DESC
                LIMIT $2;
            `;
            const result = await db.query(query, [userId, limit]);
            return result.rows;
        } catch (error) {
            logger.error('Error in getSchemeMatches:', error);
            throw error;
        }
    }
}

module.exports = User;