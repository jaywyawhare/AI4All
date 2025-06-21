const speech = require('@google-cloud/speech');
const fs = require('fs');
const ffmpeg = require('fluent-ffmpeg');
const { logger } = require('./logger');

const client = new speech.SpeechClient();

const processVoiceMessage = async (message) => {
    try {
        const media = await message.downloadMedia();
        const audioBuffer = Buffer.from(media.data, 'base64');
        
        // Convert audio to proper format using ffmpeg
        const convertedAudio = await convertAudio(audioBuffer);
        
        // Perform speech-to-text
        const [response] = await client.recognize({
            audio: {
                content: convertedAudio.toString('base64'),
            },
            config: {
                encoding: 'LINEAR16',
                sampleRateHertz: 16000,
                languageCode: 'en-IN', // Can be dynamic based on user preference
            },
        });

        const transcription = response.results
            .map(result => result.alternatives[0].transcript)
            .join('\n');

        return transcription;

    } catch (error) {
        logger.error('Error processing voice message:', error);
        throw new Error('Failed to process voice message');
    }
};

const convertAudio = (buffer) => {
    return new Promise((resolve, reject) => {
        const outputPath = `/tmp/${Date.now()}.wav`;
        
        ffmpeg()
            .input(buffer)
            .toFormat('wav')
            .audioFrequency(16000)
            .audioChannels(1)
            .on('end', () => {
                const convertedBuffer = fs.readFileSync(outputPath);
                fs.unlinkSync(outputPath);
                resolve(convertedBuffer);
            })
            .on('error', reject)
            .save(outputPath);
    });
};

module.exports = { processVoiceMessage };