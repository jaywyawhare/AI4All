-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    wp_user_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    age INTEGER,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female')),
    income DECIMAL,
    state VARCHAR(100),
    phone_number VARCHAR(20),
    preferred_language VARCHAR(10) DEFAULT 'en',
    response_format VARCHAR(10) DEFAULT 'text' CHECK (response_format IN ('text', 'audio', 'both')),
    voice_enabled BOOLEAN DEFAULT true,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    message_type VARCHAR(10) CHECK (message_type IN ('text', 'image', 'video', 'voice')),
    content TEXT,
    media_url TEXT,
    language VARCHAR(10),
    is_processed BOOLEAN DEFAULT false,
    processing_time INTEGER,
    sarvam_response_id VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audio files table
CREATE TABLE audio_files (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    file_type VARCHAR(10) CHECK (file_type IN ('voice', 'audio_response')),
    file_path TEXT NOT NULL,
    language VARCHAR(10),
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table
CREATE TABLE user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    session_id VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schemes table (minimal)
CREATE TABLE schemes (
    id BIGSERIAL PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    url TEXT,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(100),
    category VARCHAR(255),
    description TEXT,
    caste TEXT, -- Comma-separated castes
    is_minority BOOLEAN DEFAULT false,
    is_differently_abled BOOLEAN DEFAULT false,
    is_bpl BOOLEAN DEFAULT false,
    is_student BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheme embeddings table
CREATE TABLE scheme_embeddings (
    scheme_id BIGINT REFERENCES schemes(id) PRIMARY KEY,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Scheme matches table
CREATE TABLE user_scheme_matches (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    scheme_id BIGINT REFERENCES schemes(id),
    score FLOAT,
    matched_by VARCHAR(50),
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_wp_user_id ON users(wp_user_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_language ON messages(language);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_audio_files_user_id ON audio_files(user_id);
CREATE INDEX idx_audio_files_created_at ON audio_files(created_at);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_schemes_slug ON schemes(slug);
CREATE INDEX idx_schemes_state ON schemes(state);
CREATE INDEX idx_schemes_category ON schemes(category);
CREATE INDEX idx_scheme_embeddings_scheme_id ON scheme_embeddings(scheme_id);
CREATE INDEX idx_user_scheme_matches_user_id ON user_scheme_matches(user_id);
CREATE INDEX idx_user_scheme_matches_scheme_id ON user_scheme_matches(scheme_id);