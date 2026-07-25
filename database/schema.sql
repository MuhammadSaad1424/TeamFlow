-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "fuzzystrmatch";

-- Create Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id INTEGER UNIQUE NOT NULL,
    github_username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    avatar_url TEXT,
    display_name VARCHAR(255),
    bio TEXT,
    github_access_token VARCHAR(255) NOT NULL,
    github_refresh_token VARCHAR(255),
    github_token_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_expires_at TIMESTAMP,
    preferred_language VARCHAR(10) DEFAULT 'en',
    theme VARCHAR(20) DEFAULT 'auto',
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    deleted_at TIMESTAMP,
    CONSTRAINT subscription_tier_check CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
    CONSTRAINT theme_check CHECK (theme IN ('light', 'dark', 'auto'))
);

CREATE INDEX idx_users_github_id ON users(github_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = true;

-- Create Repositories table
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    github_repo_id INTEGER UNIQUE,
    repo_name VARCHAR(255) NOT NULL,
    repo_url VARCHAR(500) NOT NULL,
    description TEXT,
    language_primary VARCHAR(50),
    languages_detected TEXT[],
    file_count INTEGER DEFAULT 0,
    total_lines_of_code BIGINT DEFAULT 0,
    repository_size_kb INTEGER DEFAULT 0,
    github_stars INTEGER DEFAULT 0,
    github_forks INTEGER DEFAULT 0,
    github_last_updated TIMESTAMP,
    is_fork BOOLEAN DEFAULT false,
    is_private BOOLEAN DEFAULT false,
    indexing_status VARCHAR(50) DEFAULT 'pending',
    indexing_started_at TIMESTAMP,
    indexing_completed_at TIMESTAMP,
    indexing_error_message TEXT,
    embedding_status VARCHAR(50) DEFAULT 'pending',
    embedding_count INTEGER DEFAULT 0,
    last_analyzed_at TIMESTAMP,
    analysis_version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    CONSTRAINT indexing_status_check CHECK (indexing_status IN ('pending', 'in_progress', 'completed', 'failed')),
    CONSTRAINT embedding_status_check CHECK (embedding_status IN ('pending', 'in_progress', 'completed', 'failed'))
);

CREATE INDEX idx_repositories_user_id ON repositories(user_id);
CREATE INDEX idx_repositories_indexing_status ON repositories(indexing_status) WHERE indexing_status != 'completed';
CREATE INDEX idx_repositories_github_repo_id ON repositories(github_repo_id);

-- Create Repository Files table
CREATE TABLE repository_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(20),
    file_size_bytes INTEGER DEFAULT 0,
    language VARCHAR(50),
    is_binary BOOLEAN DEFAULT false,
    is_test_file BOOLEAN DEFAULT false,
    is_documentation BOOLEAN DEFAULT false,
    line_count INTEGER DEFAULT 0,
    function_count INTEGER DEFAULT 0,
    class_count INTEGER DEFAULT 0,
    import_count INTEGER DEFAULT 0,
    last_modified_date TIMESTAMP,
    git_last_commit_sha VARCHAR(40),
    git_last_commit_message TEXT,
    parsed_at TIMESTAMP,
    parser_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, file_path)
);

CREATE INDEX idx_repository_files_repo_id ON repository_files(repository_id);
CREATE INDEX idx_repository_files_extension ON repository_files(file_extension);
CREATE INDEX idx_repository_files_language ON repository_files(language);

-- Create Code Chunks table
CREATE TABLE code_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES repository_files(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_type VARCHAR(50),
    raw_content TEXT NOT NULL,
    cleaned_content TEXT,
    content_hash VARCHAR(64),
    language VARCHAR(50),
    start_line_number INTEGER,
    end_line_number INTEGER,
    start_char_offset INTEGER,
    end_char_offset INTEGER,
    entity_name VARCHAR(255),
    entity_type VARCHAR(50),
    is_public BOOLEAN,
    documentation_text TEXT,
    depends_on_chunks UUID[],
    referenced_by_chunks UUID[],
    is_embedded BOOLEAN DEFAULT false,
    embedding_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, file_id, chunk_index)
);

CREATE INDEX idx_code_chunks_repo_id ON code_chunks(repository_id);
CREATE INDEX idx_code_chunks_file_id ON code_chunks(file_id);
CREATE INDEX idx_code_chunks_entity_name ON code_chunks(entity_name);
CREATE INDEX idx_code_chunks_chunk_type ON code_chunks(chunk_type);

-- Create Embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_chunk_id UUID NOT NULL UNIQUE REFERENCES code_chunks(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    vector_id VARCHAR(255) NOT NULL UNIQUE,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-large',
    vector_dimension INTEGER DEFAULT 3072,
    content_summary TEXT,
    semantic_tags TEXT[],
    relevance_keywords TEXT[],
    vector_db_provider VARCHAR(50),
    stored_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_embeddings_chunk_id ON embeddings(code_chunk_id);
CREATE INDEX idx_embeddings_repo_id ON embeddings(repository_id);
CREATE INDEX idx_embeddings_model ON embeddings(embedding_model);

-- Create Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    title VARCHAR(500),
    description TEXT,
    message_count INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    llm_model VARCHAR(100),
    embedding_model VARCHAR(100),
    vector_db_provider VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_repo_id ON conversations(repository_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- Create Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(50) DEFAULT 'user',
    query_text TEXT NOT NULL,
    response_text TEXT,
    query_tokens INTEGER,
    response_tokens INTEGER,
    processing_time_ms INTEGER,
    confidence_score FLOAT,
    is_hallucinated BOOLEAN DEFAULT false,
    user_feedback VARCHAR(50),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (message_type IN ('user', 'assistant')),
    CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Create Citations table
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    code_chunk_id UUID NOT NULL REFERENCES code_chunks(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES repository_files(id) ON DELETE CASCADE,
    citation_index INTEGER,
    citation_type VARCHAR(50),
    relevance_score FLOAT,
    snippet_text TEXT,
    start_line INTEGER,
    end_line INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_citations_message_id ON citations(message_id);
CREATE INDEX idx_citations_chunk_id ON citations(code_chunk_id);
CREATE INDEX idx_citations_file_id ON citations(file_id);

-- Create Repository Metadata table
CREATE TABLE repository_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL UNIQUE REFERENCES repositories(id) ON DELETE CASCADE,
    architecture_summary TEXT,
    main_modules TEXT[],
    key_services TEXT[],
    external_dependencies TEXT[],
    internal_dependencies TEXT[],
    design_patterns TEXT[],
    architecture_patterns TEXT[],
    code_statistics JSONB,
    complexity_metrics JSONB,
    auto_generated_readme TEXT,
    auto_generated_api_doc TEXT,
    last_analyzed_at TIMESTAMP,
    analysis_version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_repo_metadata_repo_id ON repository_metadata(repository_id);

-- Create Analytics Events table
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_created_at ON analytics_events(created_at);

-- Create API Keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,
    ip_whitelist INET[],
    rate_limit_per_hour INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expired_at TIMESTAMP
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- Create Activity Logs table
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    description TEXT,
    details JSONB,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_action_type ON activity_logs(action_type);

-- Create Message Feedback table
CREATE TABLE message_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL UNIQUE REFERENCES messages(id) ON DELETE CASCADE,
    rating INTEGER,
    feedback_type VARCHAR(50),
    feedback_text TEXT,
    accuracy BOOLEAN,
    completeness BOOLEAN,
    clarity BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (rating >= 1 AND rating <= 5)
);

CREATE INDEX idx_feedback_message_id ON message_feedback(message_id);

-- Create Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) NOT NULL UNIQUE,
    refresh_token VARCHAR(500),
    user_agent TEXT,
    ip_address INET,
    device_type VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    is_revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW user_statistics AS
SELECT 
    u.id,
    u.github_username,
    COUNT(DISTINCT r.id) as repository_count,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT m.id) as message_count,
    MAX(u.last_login_at) as last_active
FROM users u
LEFT JOIN repositories r ON u.id = r.user_id AND r.deleted_at IS NULL
LEFT JOIN conversations c ON u.id = c.user_id AND c.deleted_at IS NULL
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.github_username;

CREATE MATERIALIZED VIEW repository_statistics AS
SELECT 
    r.id,
    r.repo_name,
    COUNT(DISTINCT rf.id) as file_count,
    COUNT(DISTINCT rc.id) as chunk_count,
    COUNT(DISTINCT e.id) as embedding_count,
    AVG(rf.line_count) as avg_file_lines,
    SUM(rf.line_count) as total_lines
FROM repositories r
LEFT JOIN repository_files rf ON r.id = rf.repository_id
LEFT JOIN code_chunks rc ON r.id = rc.repository_id
LEFT JOIN embeddings e ON r.id = e.repository_id
WHERE r.deleted_at IS NULL
GROUP BY r.id, r.repo_name;

-- Create update triggers
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER repositories_updated_at BEFORE UPDATE ON repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
