const axios = require('axios');
const { logger } = require('../utils/logger');

const searchSchemes = async (query) => {
    try {
        // Call your scheme API here
        const response = await axios.get(`${process.env.SCHEME_API_URL}/search`, {
            params: { q: query }
        });

        if (!response.data || response.data.length === 0) {
            return 'No schemes found matching your query. Please try with different keywords.';
        }

        // Format the schemes into a readable message
        return formatSchemeResponse(response.data);

    } catch (error) {
        logger.error('Error searching schemes:', error);
        throw new Error('Failed to search schemes');
    }
};

const formatSchemeResponse = (schemes) => {
    let response = '🏛️ *Found Government Schemes:*\n\n';
    
    schemes.slice(0, 3).forEach((scheme, index) => {
        response += `*${index + 1}. ${scheme.name}*\n`;
        response += `📝 Description: ${scheme.briefDescription}\n`;
        response += `💰 Benefits: ${scheme.benefits}\n`;
        response += `📱 How to apply: ${scheme.applicationProcess}\n\n`;
    });

    response += '\nTo know more, please reply with the scheme number.';
    return response;
};

module.exports = { searchSchemes };