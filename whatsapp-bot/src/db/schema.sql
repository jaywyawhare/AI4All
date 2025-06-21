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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    message_type VARCHAR(10) CHECK (message_type IN ('text', 'image', 'video', 'voice')),
    content TEXT,
    media_url TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schemes table
CREATE TABLE schemes (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    min_age INTEGER,
    max_age INTEGER,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'any')),
    income_limit DECIMAL,
    state VARCHAR(100),
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
CREATE INDEX idx_scheme_embeddings_scheme_id ON scheme_embeddings(scheme_id);
CREATE INDEX idx_user_scheme_matches_user_id ON user_scheme_matches(user_id);
CREATE INDEX idx_user_scheme_matches_scheme_id ON user_scheme_matches(scheme_id);