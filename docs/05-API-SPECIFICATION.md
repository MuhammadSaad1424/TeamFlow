# API Reference & Specification

## Base URL

```
Production: https://api.teamflow.ai/v1
Development: http://localhost:8000/v1
```

## Authentication

All endpoints (except public endpoints) require JWT Bearer Token:

```
Authorization: Bearer <JWT_TOKEN>
```

## Response Format

### Success Response (2xx)

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Operation successful",
  "data": {
    "key": "value"
  },
  "timestamp": "2024-06-16T10:30:00Z"
}
```

### Error Response (4xx, 5xx)

```json
{
  "success": false,
  "statusCode": 400,
  "message": "Error description",
  "error": {
    "code": "INVALID_REQUEST",
    "details": "Additional error information"
  },
  "timestamp": "2024-06-16T10:30:00Z"
}
```

## Authentication Endpoints

### 1. GitHub OAuth Redirect

**GET** `/auth/github/login`

Initiates GitHub OAuth flow.

**Parameters:**
- `redirect_uri` (optional): Redirect URL after authentication

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "auth_url": "https://github.com/login/oauth/authorize?client_id=...",
    "state": "random_state_string"
  }
}
```

### 2. GitHub OAuth Callback

**GET** `/auth/github/callback`

Handles GitHub OAuth callback.

**Query Parameters:**
- `code` (required): OAuth code from GitHub
- `state` (required): State parameter

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "uuid",
      "github_username": "john_doe",
      "email": "john@example.com",
      "avatar_url": "https://avatars.githubusercontent.com/...",
      "subscription_tier": "free"
    }
  }
}
```

### 3. Logout

**POST** `/auth/logout`

Revokes user session.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Logged out successfully"
}
```

### 4. Refresh Token

**POST** `/auth/refresh`

Refreshes JWT token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600
  }
}
```

## Repository Endpoints

### 1. Add Repository

**POST** `/repositories`

Adds a GitHub repository for analysis.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "github_url": "https://github.com/username/repository",
  "name": "Custom Repository Name (optional)",
  "description": "Repository description (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "statusCode": 201,
  "data": {
    "id": "uuid",
    "repo_name": "repository",
    "repo_url": "https://github.com/username/repository",
    "user_id": "uuid",
    "indexing_status": "pending",
    "created_at": "2024-06-16T10:30:00Z"
  }
}
```

### 2. List User Repositories

**GET** `/repositories`

Lists all repositories for the authenticated user.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Results per page (default: 10, max: 100)
- `sort` (optional): Sort field (created_at, updated_at, name)
- `order` (optional): Sort order (asc, desc)
- `status` (optional): Filter by indexing status

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "repositories": [
      {
        "id": "uuid",
        "repo_name": "repository",
        "repo_url": "https://github.com/username/repository",
        "language_primary": "Python",
        "file_count": 150,
        "indexing_status": "completed",
        "embedding_count": 5000,
        "created_at": "2024-06-16T10:30:00Z",
        "updated_at": "2024-06-16T11:00:00Z"
      }
    ],
    "pagination": {
      "total": 25,
      "page": 1,
      "limit": 10,
      "total_pages": 3
    }
  }
}
```

### 3. Get Repository Details

**GET** `/repositories/{repository_id}`

Retrieves detailed information about a repository.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `repository_id` (required): UUID of repository

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "repository": {
      "id": "uuid",
      "repo_name": "repository",
      "repo_url": "https://github.com/username/repository",
      "description": "Repository description",
      "language_primary": "Python",
      "languages_detected": ["Python", "JavaScript", "SQL"],
      "file_count": 150,
      "total_lines_of_code": 25000,
      "github_stars": 1500,
      "github_forks": 300,
      "indexing_status": "completed",
      "embedding_count": 5000,
      "last_analyzed_at": "2024-06-16T11:00:00Z",
      "created_at": "2024-06-16T10:30:00Z"
    },
    "statistics": {
      "total_files": 150,
      "total_chunks": 5000,
      "avg_chunk_size": 150,
      "code_to_comment_ratio": 0.85
    }
  }
}
```

### 4. Index Repository

**POST** `/repositories/{repository_id}/index`

Starts indexing process for a repository.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `repository_id` (required): UUID of repository

**Request Body (optional):**
```json
{
  "force_reindex": false,
  "language_filter": ["Python", "JavaScript"],
  "exclude_patterns": ["*.test.js", "__pycache__/*"],
  "max_file_size_mb": 10
}
```

**Response:**
```json
{
  "success": true,
  "statusCode": 202,
  "data": {
    "repository_id": "uuid",
    "indexing_job_id": "uuid",
    "status": "in_progress",
    "message": "Indexing started. This may take several minutes.",
    "started_at": "2024-06-16T10:30:00Z"
  }
}
```

### 5. Get Indexing Status

**GET** `/repositories/{repository_id}/index-status`

Gets the current indexing status.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `repository_id` (required): UUID of repository

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "repository_id": "uuid",
    "status": "in_progress",
    "progress": {
      "files_parsed": 120,
      "files_total": 150,
      "chunks_created": 4500,
      "embeddings_generated": 4000,
      "percentage": 75
    },
    "started_at": "2024-06-16T10:30:00Z",
    "estimated_completion_at": "2024-06-16T11:15:00Z"
  }
}
```

### 6. Delete Repository

**DELETE** `/repositories/{repository_id}`

Deletes a repository and all associated data.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `repository_id` (required): UUID of repository

**Query Parameters:**
- `confirm` (required): Set to "true" to confirm deletion

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Repository deleted successfully"
}
```

### 7. Get Repository Architecture

**GET** `/repositories/{repository_id}/architecture`

Gets analyzed architecture of the repository.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `repository_id` (required): UUID of repository

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "architecture": {
      "modules": [
        {
          "name": "auth",
          "description": "Authentication module",
          "files": 5,
          "dependencies": ["core", "db"]
        }
      ],
      "services": [
        {
          "name": "UserService",
          "methods": 15,
          "dependencies": ["DatabaseService"]
        }
      ],
      "patterns_detected": ["MVC", "Singleton", "Factory"],
      "data_flow_diagram": "..."
    }
  }
}
```

## Chat Endpoints

### 1. Send Query

**POST** `/chat`

Sends a question about the codebase.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "repository_id": "uuid",
  "conversation_id": "uuid (optional, creates new if not provided)",
  "query": "How does authentication work in this project?",
  "context_limit": 5,
  "model_preference": "gpt-4o (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "message_id": "uuid",
    "conversation_id": "uuid",
    "query": "How does authentication work in this project?",
    "response": "Authentication is implemented using OAuth2...",
    "citations": [
      {
        "id": 1,
        "file_path": "src/auth/oauth.py",
        "snippet": "def oauth_callback(...)",
        "start_line": 42,
        "end_line": 58,
        "relevance_score": 0.98
      }
    ],
    "confidence_score": 0.92,
    "processing_time_ms": 1250,
    "tokens_used": {
      "query_tokens": 15,
      "response_tokens": 156
    }
  }
}
```

### 2. Stream Query

**POST** `/chat/stream`

Sends a query with streaming response.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`
- `Content-Type: application/json`

**Request Body:** (same as Send Query)

**Response:** (Server-Sent Events - continuous stream)
```
data: {"type": "token", "content": "Authentication"}
data: {"type": "token", "content": " is"}
data: {"type": "citation", "content": {...}}
data: {"type": "complete", "message_id": "uuid"}
```

### 3. Get Conversation History

**GET** `/chat/conversations/{conversation_id}`

Retrieves conversation history.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `conversation_id` (required): UUID of conversation

**Query Parameters:**
- `limit` (optional): Number of messages (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "conversation": {
      "id": "uuid",
      "repository_id": "uuid",
      "title": "Authentication Discussion",
      "created_at": "2024-06-16T10:30:00Z",
      "message_count": 5
    },
    "messages": [
      {
        "id": "uuid",
        "type": "user",
        "content": "How does authentication work?",
        "created_at": "2024-06-16T10:30:00Z"
      },
      {
        "id": "uuid",
        "type": "assistant",
        "content": "Authentication is implemented using OAuth2...",
        "citations": [...],
        "confidence_score": 0.92,
        "created_at": "2024-06-16T10:31:00Z"
      }
    ]
  }
}
```

### 4. List User Conversations

**GET** `/chat/conversations`

Lists all conversations for the user.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Query Parameters:**
- `repository_id` (optional): Filter by repository
- `page` (optional): Page number (default: 1)
- `limit` (optional): Results per page (default: 20)

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "conversations": [
      {
        "id": "uuid",
        "repository_id": "uuid",
        "title": "Authentication Discussion",
        "message_count": 5,
        "last_message_at": "2024-06-16T10:35:00Z",
        "created_at": "2024-06-16T10:30:00Z"
      }
    ],
    "pagination": {
      "total": 15,
      "page": 1,
      "limit": 20
    }
  }
}
```

### 5. Delete Conversation

**DELETE** `/chat/conversations/{conversation_id}`

Deletes a conversation.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `conversation_id` (required): UUID of conversation

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Conversation deleted successfully"
}
```

### 6. Provide Feedback

**POST** `/chat/messages/{message_id}/feedback`

Provides feedback on a response.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `message_id` (required): UUID of message

**Request Body:**
```json
{
  "rating": 4,
  "feedback_type": "helpful",
  "accuracy": true,
  "completeness": true,
  "clarity": true,
  "feedback_text": "Very helpful response"
}
```

**Response:**
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Feedback recorded successfully"
}
```

## Documentation Endpoints

### 1. Generate Documentation

**POST** `/documentation/generate`

Generates documentation for a repository.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Request Body:**
```json
{
  "repository_id": "uuid",
  "doc_type": "README",
  "include_api_docs": true,
  "include_architecture": true,
  "include_examples": true,
  "language": "markdown"
}
```

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "documentation_id": "uuid",
    "repository_id": "uuid",
    "doc_type": "README",
    "content": "# Project Name\n\n...",
    "generated_at": "2024-06-16T10:30:00Z"
  }
}
```

### 2. Get Generated Documentation

**GET** `/documentation/{documentation_id}`

Retrieves generated documentation.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Path Parameters:**
- `documentation_id` (required): UUID of documentation

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "id": "uuid",
    "repository_id": "uuid",
    "doc_type": "README",
    "content": "# Project Name\n\n...",
    "html_preview": "<h1>Project Name</h1>...",
    "generated_at": "2024-06-16T10:30:00Z"
  }
}
```

## Analytics Endpoints

### 1. Get Dashboard Analytics

**GET** `/analytics/dashboard`

Gets analytics dashboard data.

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`

**Query Parameters:**
- `period` (optional): Time period (7days, 30days, 90days, all)
- `repository_id` (optional): Filter by repository

**Response:**
```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "overview": {
      "total_queries": 1250,
      "avg_query_time_ms": 1200,
      "avg_confidence_score": 0.87,
      "total_repositories": 5
    },
    "queries_by_day": [
      {
        "date": "2024-06-16",
        "count": 125,
        "avg_response_time": 1200
      }
    ],
    "top_questions": [
      {
        "query": "How does authentication work?",
        "count": 25
      }
    ],
    "model_usage": {
      "gpt-4o": 800,
      "llama-3": 450
    }
  }
}
```

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Rate Limiting

Rate limits per authenticated user:

- **Free tier**: 100 queries/day, 10 repositories
- **Pro tier**: 10,000 queries/day, 100 repositories
- **Enterprise**: Unlimited

Headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 75
X-RateLimit-Reset: 1624780800
```

## Pagination

List endpoints support pagination:

```json
{
  "data": {...},
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 10,
    "total_pages": 15,
    "has_next": true,
    "has_prev": false
  }
}
```

## Versioning

All endpoints are versioned. Current version: `v1`

Future versions will be available at:
- `https://api.teamflow.ai/v2`

## Webhooks (Future)

Webhook events:
- `repository.indexed`
- `documentation.generated`
- `analysis.complete`

## Conclusion

This API provides complete integration for:
- Repository management
- AI-powered code querying
- Documentation generation
- Analytics and insights
- User authentication and management
