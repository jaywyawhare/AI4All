const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');
const logger = require('./logger');

class AudioProcessor {
    constructor() {
        this.tempDir = path.join(process.cwd(), 'temp_audio');
        this.maxFiles = 100; // Maximum number of temp files to keep
        this.maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        this.init();
    }

    async init() {
        try {
            await fs.ensureDir(this.tempDir);
            await this.cleanupOldFiles();
        } catch (error) {
            logger.error('Error initializing AudioProcessor:', error);
        }
    }

    async saveAudioFile(media, userId) {
        try {
            const buffer = Buffer.from(media.data, 'base64');
            const filename = `audio_${userId}_${Date.now()}_${crypto.randomBytes(8).toString('hex')}.ogg`;
            const filePath = path.join(this.tempDir, filename);
            
            await fs.writeFile(filePath, buffer);
            
            logger.info(`Audio file saved: ${filePath}`);
            
            // Save to database
            await this.saveAudioRecord(userId, 'voice', filePath);
            
            return {
                path: filePath,
                filename: filename,
                size: buffer.length,
                mimetype: media.mimetype
            };
        } catch (error) {
            logger.error('Error saving audio file:', error);
            throw error;
        }
    }

    async saveImageFile(media, userId) {
        try {
            const buffer = Buffer.from(media.data, 'base64');
            const extension = this.getExtensionFromMimeType(media.mimetype);
            const filename = `image_${userId}_${Date.now()}_${crypto.randomBytes(8).toString('hex')}.${extension}`;
            const filePath = path.join(this.tempDir, filename);
            
            await fs.writeFile(filePath, buffer);
            
            logger.info(`Image file saved: ${filePath}`);
            
            return {
                path: filePath,
                filename: filename,
                size: buffer.length,
                mimetype: media.mimetype
            };
        } catch (error) {
            logger.error('Error saving image file:', error);
            throw error;
        }
    }

    async saveDocumentFile(media, userId) {
        try {
            const buffer = Buffer.from(media.data, 'base64');
            const extension = this.getExtensionFromMimeType(media.mimetype) || 'pdf';
            const filename = `doc_${userId}_${Date.now()}_${crypto.randomBytes(8).toString('hex')}.${extension}`;
            const filePath = path.join(this.tempDir, filename);
            
            await fs.writeFile(filePath, buffer);
            
            logger.info(`Document file saved: ${filePath}`);
            
            return {
                path: filePath,
                filename: filename,
                size: buffer.length,
                mimetype: media.mimetype
            };
        } catch (error) {
            logger.error('Error saving document file:', error);
            throw error;
        }
    }

    async extractAudioFromVideo(media, userId) {
        try {
            // For now, we'll save the video and return a placeholder
            // In a real implementation, you'd use ffmpeg to extract audio
            const buffer = Buffer.from(media.data, 'base64');
            const filename = `video_${userId}_${Date.now()}_${crypto.randomBytes(8).toString('hex')}.mp4`;
            const filePath = path.join(this.tempDir, filename);
            
            await fs.writeFile(filePath, buffer);
            
            logger.info(`Video file saved (audio extraction placeholder): ${filePath}`);
            
            // Return the video file as audio for now
            return {
                path: filePath,
                filename: filename,
                size: buffer.length,
                mimetype: 'audio/ogg', // Placeholder
                data: media.data
            };
        } catch (error) {
            logger.error('Error extracting audio from video:', error);
            throw error;
        }
    }

    async saveAudioRecord(userId, fileType, filePath) {
        try {
            const db = require('../config/database');
            const query = `
                INSERT INTO audio_files (user_id, file_type, file_path, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                RETURNING *;
            `;
            
            await db.query(query, [userId, fileType, filePath]);
            logger.info(`Audio record saved for user ${userId}`);
        } catch (error) {
            logger.error('Error saving audio record:', error);
            // Don't throw error as this is not critical
        }
    }

    async cleanupOldFiles() {
        try {
            const files = await fs.readdir(this.tempDir);
            
            if (files.length <= this.maxFiles) {
                return;
            }
            
            // Get file stats and sort by creation time
            const fileStats = await Promise.all(
                files.map(async (filename) => {
                    const filePath = path.join(this.tempDir, filename);
                    const stats = await fs.stat(filePath);
                    return { filename, filePath, stats };
                })
            );
            
            // Sort by creation time (oldest first)
            fileStats.sort((a, b) => a.stats.birthtime.getTime() - b.stats.birthtime.getTime());
            
            // Remove oldest files
            const filesToRemove = fileStats.slice(0, fileStats.length - this.maxFiles);
            
            for (const file of filesToRemove) {
                try {
                    await fs.unlink(file.filePath);
                    logger.info(`Cleaned up old file: ${file.filename}`);
                } catch (error) {
                    logger.error(`Error removing file ${file.filename}:`, error);
                }
            }
            
            logger.info(`Cleaned up ${filesToRemove.length} old files`);
        } catch (error) {
            logger.error('Error during cleanup:', error);
        }
    }

    async removeFile(filePath) {
        try {
            await fs.unlink(filePath);
            logger.info(`File removed: ${filePath}`);
        } catch (error) {
            logger.error(`Error removing file ${filePath}:`, error);
        }
    }

    getExtensionFromMimeType(mimetype) {
        const extensions = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'audio/ogg': 'ogg',
            'audio/mp3': 'mp3',
            'audio/wav': 'wav',
            'video/mp4': 'mp4',
            'video/avi': 'avi',
            'video/mov': 'mov',
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx'
        };
        
        return extensions[mimetype] || 'bin';
    }

    async getFileInfo(filePath) {
        try {
            const stats = await fs.stat(filePath);
            return {
                size: stats.size,
                created: stats.birthtime,
                modified: stats.mtime,
                exists: true
            };
        } catch (error) {
            return {
                exists: false,
                error: error.message
            };
        }
    }

    async ensureTempDirectory() {
        try {
            await fs.ensureDir(this.tempDir);
            return true;
        } catch (error) {
            logger.error('Error ensuring temp directory:', error);
            return false;
        }
    }
}

module.exports = AudioProcessor; 