from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, LargeBinary, JSON, Float, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            if isinstance(value, str):
                return PG_UUID(as_uuid=True).process_bind_param(value, dialect)
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value

from app.core.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    github_username = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    avatar_url = Column(Text, nullable=True)
    display_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Auth tokens
    github_access_token = Column(String(255), nullable=False)
    github_refresh_token = Column(String(255), nullable=True)
    github_token_expires_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    email_verified = Column(Boolean, default=False)
    subscription_tier = Column(String(50), default="free")  # free, pro, enterprise
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Settings
    preferred_language = Column(String(10), default="en")
    theme = Column(String(20), default="auto")  # light, dark, auto
    notifications_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    repositories = relationship("Repository", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Repository(Base):
    """Repository model."""
    __tablename__ = "repositories"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Repository Info
    github_repo_id = Column(Integer, unique=True, nullable=True)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Repository Metadata
    language_primary = Column(String(50), nullable=True)
    languages_detected = Column(JSON, nullable=True)
    file_count = Column(Integer, default=0)
    total_lines_of_code = Column(Integer, default=0)
    repository_size_kb = Column(Integer, default=0)
    
    # GitHub Data
    github_stars = Column(Integer, default=0)
    github_forks = Column(Integer, default=0)
    github_last_updated = Column(DateTime, nullable=True)
    is_fork = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    
    # Indexing Status
    indexing_status = Column(String(50), default="pending", index=True)  # pending, in_progress, completed, failed
    indexing_started_at = Column(DateTime, nullable=True)
    indexing_completed_at = Column(DateTime, nullable=True)
    indexing_error_message = Column(Text, nullable=True)
    
    # Embeddings
    embedding_status = Column(String(50), default="pending")
    embedding_count = Column(Integer, default=0)
    
    # Analysis
    last_analyzed_at = Column(DateTime, nullable=True)
    analysis_version = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="repositories")
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")
    chunks = relationship("CodeChunk", back_populates="repository", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="repository", cascade="all, delete-orphan")
    repo_metadata = relationship("RepositoryMetadata", back_populates="repository", uselist=False, cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="repository")
    conversations = relationship("Conversation", back_populates="repository")


class RepositoryFile(Base):
    """Repository file model."""
    __tablename__ = "repository_files"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    repository_id = Column(GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File Info
    file_path = Column(String(1000), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_extension = Column(String(20), index=True)
    file_size_bytes = Column(Integer, default=0)
    
    # Content
    language = Column(String(50), index=True)
    is_binary = Column(Boolean, default=False)
    is_test_file = Column(Boolean, default=False)
    is_documentation = Column(Boolean, default=False)
    
    # Code Metrics
    line_count = Column(Integer, default=0)
    function_count = Column(Integer, default=0)
    class_count = Column(Integer, default=0)
    import_count = Column(Integer, default=0)
    
    # Git Info
    last_modified_date = Column(DateTime, nullable=True)
    git_last_commit_sha = Column(String(40), nullable=True)
    git_last_commit_message = Column(Text, nullable=True)
    
    # Processing
    parsed_at = Column(DateTime, nullable=True)
    parser_version = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="files")
    chunks = relationship("CodeChunk", back_populates="file", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="file")


class CodeChunk(Base):
    """Code chunk model."""
    __tablename__ = "code_chunks"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    repository_id = Column(GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(GUID(), ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Chunk Info
    chunk_index = Column(Integer, nullable=False)
    chunk_type = Column(String(50))  # function, class, comment, import, etc.
    
    # Content
    raw_content = Column(Text, nullable=False)
    cleaned_content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)  # SHA256
    
    # Metadata
    language = Column(String(50))
    start_line_number = Column(Integer)
    end_line_number = Column(Integer)
    start_char_offset = Column(Integer)
    end_char_offset = Column(Integer)
    
    # Semantic Info
    entity_name = Column(String(255), index=True)
    entity_type = Column(String(50))  # function, class, method, etc.
    is_public = Column(Boolean)
    documentation_text = Column(Text, nullable=True)
    
    # Related Code
    depends_on_chunks = Column(JSON, nullable=True)
    referenced_by_chunks = Column(JSON, nullable=True)
    
    # Embedding Info
    is_embedded = Column(Boolean, default=False)
    embedding_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="chunks")
    file = relationship("RepositoryFile", back_populates="chunks")
    embedding = relationship("Embedding", back_populates="chunk", uselist=False)
    citations = relationship("Citation", back_populates="chunk")


class Embedding(Base):
    """Embedding model."""
    __tablename__ = "embeddings"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    code_chunk_id = Column(GUID(), ForeignKey("code_chunks.id", ondelete="CASCADE"), nullable=False, unique=True)
    repository_id = Column(GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Embedding Info
    vector_id = Column(String(255), nullable=False, unique=True)
    embedding_model = Column(String(100), default="models/gemini-embedding-2")
    vector_dimension = Column(Integer, default=3072)
    
    # Metadata
    content_summary = Column(Text, nullable=True)
    semantic_tags = Column(JSON, nullable=True)
    relevance_keywords = Column(JSON, nullable=True)
    
    # Storage
    vector_db_provider = Column(String(50))  # chromadb, pinecone, weaviate
    stored_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chunk = relationship("CodeChunk", back_populates="embedding")
    repository = relationship("Repository", back_populates="embeddings")


class Conversation(Base):
    """Conversation model."""
    __tablename__ = "conversations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(GUID(), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # Content
    message_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Models Used
    llm_model = Column(String(100), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    vector_db_provider = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    repository = relationship("Repository", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model."""
    __tablename__ = "messages"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(GUID(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Message Type
    message_type = Column(String(50), default="user")  # user, assistant
    
    # Content
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    
    # Processing Info
    query_tokens = Column(Integer, nullable=True)
    response_tokens = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Quality
    confidence_score = Column(Float, nullable=True)
    is_hallucinated = Column(Boolean, default=False)
    
    # Feedback
    user_feedback = Column(String(50), nullable=True)  # helpful, not_helpful, none
    feedback_text = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan")
    feedback = relationship("MessageFeedback", back_populates="message", uselist=False, cascade="all, delete-orphan")


class Citation(Base):
    """Citation model."""
    __tablename__ = "citations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    message_id = Column(GUID(), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    code_chunk_id = Column(GUID(), ForeignKey("code_chunks.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(GUID(), ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    
    # Citation Info
    citation_index = Column(Integer, nullable=True)
    citation_type = Column(String(50))  # direct, related, reference
    relevance_score = Column(Float, nullable=True)
    
    # Display Info
    snippet_text = Column(Text, nullable=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="citations")
    chunk = relationship("CodeChunk", back_populates="citations")
    file = relationship("RepositoryFile", back_populates="citations")


class RepositoryMetadata(Base):
    """Repository metadata model."""
    __tablename__ = "repository_metadata"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    repository_id = Column(GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Architecture Info
    architecture_summary = Column(Text, nullable=True)
    main_modules = Column(JSON, nullable=True)
    key_services = Column(JSON, nullable=True)
    
    # Dependencies
    external_dependencies = Column(JSON, nullable=True)
    internal_dependencies = Column(JSON, nullable=True)
    
    # Patterns
    design_patterns = Column(JSON, nullable=True)
    architecture_patterns = Column(JSON, nullable=True)
    
    # Statistics
    code_statistics = Column(JSON, nullable=True)
    complexity_metrics = Column(JSON, nullable=True)
    
    # Generated Content
    auto_generated_readme = Column(Text, nullable=True)
    auto_generated_api_doc = Column(Text, nullable=True)
    
    # Analysis
    last_analyzed_at = Column(DateTime, nullable=True)
    analysis_version = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="repo_metadata")


class AnalyticsEvent(Base):
    """Analytics event model."""
    __tablename__ = "analytics_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event Info
    event_type = Column(String(100), nullable=False, index=True)
    event_name = Column(String(255), nullable=False)
    
    # Context
    repository_id = Column(GUID(), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True)
    conversation_id = Column(GUID(), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    
    # Data
    event_data = Column(JSON, nullable=True)
    
    # Properties
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")
    repository = relationship("Repository", back_populates="analytics_events")


class APIKey(Base):
    """API Key model."""
    __tablename__ = "api_keys"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Key Info
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(20), nullable=True)
    
    # Metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Security
    ip_whitelist = Column(JSON, nullable=True)
    rate_limit_per_hour = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expired_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class ActivityLog(Base):
    """Activity log model."""
    __tablename__ = "activity_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Activity Info
    action_type = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    # Details
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")


class MessageFeedback(Base):
    """Message feedback model."""
    __tablename__ = "message_feedback"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    message_id = Column(GUID(), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Feedback
    rating = Column(Integer, nullable=True)
    feedback_type = Column(String(50), nullable=True)
    feedback_text = Column(Text, nullable=True)
    
    # Categories
    accuracy = Column(Boolean, nullable=True)
    completeness = Column(Boolean, nullable=True)
    clarity = Column(Boolean, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="feedback")


class Session(Base):
    """User session model."""
    __tablename__ = "sessions"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session Info
    session_token = Column(String(500), nullable=False, unique=True)
    refresh_token = Column(String(500), nullable=True)
    
    # Device/Browser
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_type = Column(String(50), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
