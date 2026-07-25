from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# User Schemas
class UserBase(BaseModel):
    github_username: str
    email: EmailStr
    display_name: Optional[str] = None


class UserCreate(UserBase):
    github_id: int
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    github_id: int
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    subscription_tier: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Authentication Schemas
class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "bearer"


# Repository Schemas
class RepositoryBase(BaseModel):
    repo_name: str
    repo_url: HttpUrl
    description: Optional[str] = None


class RepositoryCreate(BaseModel):
    github_url: str
    name: Optional[str] = None
    description: Optional[str] = None


class RepositoryUpdate(BaseModel):
    description: Optional[str] = None


class RepositoryResponse(RepositoryBase):
    id: UUID
    user_id: UUID
    language_primary: Optional[str] = None
    languages_detected: Optional[List[str]] = None
    file_count: int
    total_lines_of_code: int
    indexing_status: str
    embedding_count: int
    github_stars: int
    github_forks: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RepositoryDetailResponse(RepositoryResponse):
    repository_size_kb: int
    is_fork: bool
    is_private: bool
    last_analyzed_at: Optional[datetime] = None


# Code Chunk Schemas
class CodeChunkBase(BaseModel):
    raw_content: str
    language: Optional[str] = None
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None


class CodeChunkResponse(CodeChunkBase):
    id: UUID
    repository_id: UUID
    file_id: UUID
    chunk_index: int
    start_line_number: int
    end_line_number: int
    is_embedded: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Conversation Schemas
class ConversationBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ConversationCreate(ConversationBase):
    repository_id: UUID


class ConversationResponse(ConversationBase):
    id: UUID
    user_id: UUID
    repository_id: Optional[UUID] = None
    message_count: int
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    last_message_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Message/Query Schemas
class ChatQueryRequest(BaseModel):
    repository_id: UUID
    conversation_id: Optional[UUID] = None
    query: str = Field(..., min_length=1, max_length=2000)
    context_limit: Optional[int] = Field(5, ge=1, le=20)
    model_preference: Optional[str] = None


class CitationResponse(BaseModel):
    id: UUID
    file_path: str
    snippet: str
    start_line: int
    end_line: int
    relevance_score: float
    
    class Config:
        from_attributes = True


class ChatResponseMessage(BaseModel):
    message_id: UUID
    conversation_id: UUID
    query: str
    response: str
    citations: List[CitationResponse]
    confidence_score: float
    processing_time_ms: int
    tokens_used: dict
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    message_type: str
    query_text: Optional[str] = None
    response_text: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse]


# Feedback Schemas
class MessageFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback_type: Optional[str] = None
    accuracy: Optional[bool] = None
    completeness: Optional[bool] = None
    clarity: Optional[bool] = None
    feedback_text: Optional[str] = None


# Analytics Schemas
class AnalyticsEventRequest(BaseModel):
    event_type: str
    event_name: str
    event_data: Optional[dict] = None


class DashboardAnalyticsResponse(BaseModel):
    total_queries: int
    avg_query_time_ms: float
    avg_confidence_score: float
    total_repositories: int
    queries_by_day: List[dict]
    top_questions: List[dict]
    model_usage: dict


# Error Response Schema
class ErrorResponse(BaseModel):
    success: bool = False
    statusCode: int
    message: str
    error: Optional[dict] = None
    timestamp: datetime


# Generic Response Schema
class GenericResponse(BaseModel):
    success: bool
    statusCode: int
    message: Optional[str] = None
    data: Optional[dict] = None
    timestamp: datetime


# Pagination Schema
class PaginationResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Architecture Analysis Schema
class ArchitectureResponse(BaseModel):
    modules: List[dict]
    services: List[dict]
    patterns_detected: List[str]
    data_flow_diagram: Optional[str] = None


# Repository Index Status Schema
class RepositoryIndexStatusResponse(BaseModel):
    repository_id: UUID
    status: str
    progress: dict
    started_at: datetime
    estimated_completion_at: Optional[datetime] = None
