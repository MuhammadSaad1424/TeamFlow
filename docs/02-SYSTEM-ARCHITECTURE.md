# System Architecture & Design

## High-Level System Overview

```mermaid
graph TB
    subgraph Client["Client Layer"]
        WEB["Web Dashboard<br/>Next.js + React"]
        MOBILE["Mobile App<br/>Future Phase"]
    end
    
    subgraph API["API Gateway & Load Balancing"]
        LB["Load Balancer"]
        APIGW["API Gateway"]
    end
    
    subgraph Backend["Backend Services"]
        AUTH["Auth Service"]
        REPO["Repository Service"]
        CHAT["Chat Service"]
        DOC["Documentation Service"]
        ANALYTICS["Analytics Service"]
    end
    
    subgraph RAG["RAG Pipeline"]
        PARSER["Code Parser"]
        CHUNKER["Code Chunker"]
        EMBED["Embedding Generator"]
        RETRIEVE["Retrieval Engine"]
        RANK["Reranking Engine"]
        GENERATE["LLM Response Generator"]
    end
    
    subgraph Data["Data Layer"]
        POSTGRES[("PostgreSQL<br/>Primary DB")]
        VECTOR["Vector DB<br/>ChromaDB/Pinecone"]
        REDIS["Redis Cache"]
        S3["Object Storage<br/>GitHub Repos"]
    end
    
    subgraph External["External Services"]
        GITHUB["GitHub API"]
        OPENAI["OpenAI API"]
        LLM["LLM Providers"]
    end
    
    WEB --> LB
    LB --> APIGW
    APIGW --> AUTH
    APIGW --> REPO
    APIGW --> CHAT
    APIGW --> DOC
    APIGW --> ANALYTICS
    
    REPO --> PARSER
    PARSER --> CHUNKER
    CHUNKER --> EMBED
    EMBED --> VECTOR
    
    CHAT --> RETRIEVE
    RETRIEVE --> VECTOR
    RETRIEVE --> RANK
    RANK --> GENERATE
    GENERATE --> POSTGRES
    
    AUTH --> POSTGRES
    REPO --> POSTGRES
    CHAT --> POSTGRES
    DOC --> POSTGRES
    ANALYTICS --> POSTGRES
    
    REPO --> S3
    REPO --> GITHUB
    EMBED --> OPENAI
    GENERATE --> LLM
    
    RETRIEVE --> REDIS
    GENERATE --> REDIS
```

## Layered Architecture

### 1. Presentation Layer

**Components:**
- Web Dashboard (Next.js)
- Chat Interface
- Code Viewer
- Architecture Visualizer
- Analytics Dashboard

**Responsibilities:**
- User interaction
- Real-time updates
- Responsive design
- Accessibility compliance

### 2. API Layer

**Components:**
- API Gateway (FastAPI)
- Request validation
- Rate limiting
- CORS handling
- Response formatting

**Endpoints:**
- `/api/v1/auth/*` - Authentication
- `/api/v1/repositories/*` - Repository management
- `/api/v1/chat/*` - Conversation
- `/api/v1/documentation/*` - Document generation
- `/api/v1/analytics/*` - Analytics

### 3. Business Logic Layer

**Services:**
- **AuthService**: User authentication, OAuth integration
- **RepositoryService**: Repository ingestion, indexing
- **ChatService**: Conversation management, query routing
- **DocumentationService**: Document generation
- **AnalyticsService**: Usage tracking, metrics

### 4. RAG Pipeline Layer

**Components:**
- **Code Parser**: Extract code structure
- **Code Chunker**: Intelligent segmentation
- **Embedding Module**: Vector generation
- **Retrieval Module**: Hybrid search
- **Reranking Module**: Result ranking
- **Generation Module**: LLM response creation

### 5. Data Layer

**Components:**
- **PostgreSQL**: Relational data
- **Vector DB**: Embeddings storage
- **Redis**: Caching layer
- **Object Storage**: File storage

## RAG Pipeline Architecture

```mermaid
graph LR
    subgraph Input["Input"]
        REPO["GitHub Repository"]
        QUERY["User Query"]
    end
    
    subgraph Ingestion["Ingestion & Indexing"]
        CLONE["Clone Repository"]
        PARSE["Parse Code<br/>Tree-Sitter"]
        STRUCTURE["Extract Structure"]
        CHUNK["Chunk Code"]
        METADATA["Generate Metadata"]
    end
    
    subgraph Embedding["Embedding Generation"]
        PREP["Prepare Chunks"]
        EMBED["Generate Embeddings<br/>text-embedding-3-large"]
        BATCH["Batch Processing"]
    end
    
    subgraph Storage["Vector Storage"]
        INDEX["Create Index"]
        STORE["Store Vectors<br/>ChromaDB/Pinecone"]
        METADATA_STORE["Store Metadata<br/>PostgreSQL"]
    end
    
    subgraph QueryProcessing["Query Processing"]
        PREPROCESS["Preprocess Query"]
        EXPAND["Expand Query<br/>Synonyms, Variations"]
        HYBRID["Hybrid Search<br/>Dense + BM25"]
        RETRIEVE["Retrieve Top-K<br/>Results"]
    end
    
    subgraph Ranking["Ranking & Filtering"]
        RERANK["Cross-Encoder<br/>Reranking"]
        FILTER["Filter by<br/>Relevance"]
        CONTEXT["Build Context<br/>Window"]
    end
    
    subgraph Generation["Response Generation"]
        PROMPT["Build Prompt<br/>with Context"]
        LLM["Call LLM<br/>GPT-4o/Llama"]
        CITE["Generate Citations"]
        SCORE["Compute Confidence"]
    end
    
    subgraph Output["Output"]
        RESPONSE["Final Response"]
        SOURCES["Source Citations"]
        CONFIDENCE["Confidence Score"]
    end
    
    REPO --> CLONE
    CLONE --> PARSE
    PARSE --> STRUCTURE
    STRUCTURE --> CHUNK
    CHUNK --> METADATA
    METADATA --> PREP
    
    PREP --> EMBED
    EMBED --> BATCH
    BATCH --> INDEX
    INDEX --> STORE
    INDEX --> METADATA_STORE
    
    QUERY --> PREPROCESS
    PREPROCESS --> EXPAND
    EXPAND --> HYBRID
    HYBRID --> RETRIEVE
    
    RETRIEVE --> RERANK
    RERANK --> FILTER
    FILTER --> CONTEXT
    
    CONTEXT --> PROMPT
    PROMPT --> LLM
    LLM --> CITE
    CITE --> SCORE
    
    SCORE --> RESPONSE
    RESPONSE --> SOURCES
    SOURCES --> CONFIDENCE
```

## Component Interaction Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>Next.js
    participant Gateway as API Gateway
    participant AuthSvc as Auth Service
    participant ChatSvc as Chat Service
    participant RAGPipeline as RAG Pipeline
    participant VectorDB as Vector DB
    participant PostgreSQL as PostgreSQL
    participant LLM as LLM API
    
    User->>Frontend: Ask Question
    Frontend->>Gateway: POST /api/chat
    Gateway->>AuthSvc: Verify Token
    AuthSvc->>PostgreSQL: Check User
    AuthSvc-->>Gateway: Token Valid
    Gateway->>ChatSvc: Process Query
    ChatSvc->>RAGPipeline: Retrieve Context
    RAGPipeline->>VectorDB: Semantic Search
    VectorDB-->>RAGPipeline: Top-K Results
    RAGPipeline->>PostgreSQL: Get Full Code Context
    PostgreSQL-->>RAGPipeline: Code Chunks
    RAGPipeline->>ChatSvc: Prepared Context
    ChatSvc->>LLM: Generate Response
    LLM-->>ChatSvc: Response + Citations
    ChatSvc->>PostgreSQL: Save Conversation
    ChatSvc-->>Gateway: Response + Metadata
    Gateway-->>Frontend: Response
    Frontend-->>User: Display Answer
```

## Database Layer Architecture

```mermaid
graph TB
    subgraph Relational["Relational Layer<br/>PostgreSQL"]
        USERS["Users Table"]
        REPOS["Repositories Table"]
        FILES["Files Table"]
        CHUNKS["Code Chunks Table"]
        CONVERSATIONS["Conversations Table"]
        MESSAGES["Messages Table"]
        CITATIONS["Citations Table"]
        ANALYTICS["Analytics Table"]
    end
    
    subgraph Vector["Vector Layer<br/>ChromaDB/Pinecone"]
        EMBEDDINGS["Code Embeddings"]
        METADATA["Embedding Metadata"]
        INDICES["Vector Indices"]
    end
    
    subgraph Cache["Cache Layer<br/>Redis"]
        SESSION["User Sessions"]
        QUERY_CACHE["Query Cache"]
        EMBEDDING_CACHE["Embedding Cache"]
    end
    
    subgraph File["File Storage<br/>S3/Local"]
        REPO_FILES["Repository Files"]
        DOCS["Generated Documentation"]
        LOGS["System Logs"]
    end
    
    USERS -.-> SESSION
    REPOS -.-> EMBEDDINGS
    CHUNKS -.-> EMBEDDINGS
    CHUNKS -.-> QUERY_CACHE
    MESSAGES -.-> QUERY_CACHE
```

## Data Flow Diagram - Level 0

```mermaid
graph TB
    USER["👤 User"]
    SYSTEM["🔄 TeamFlow AI System"]
    GITHUB["🔗 GitHub"]
    LLM_API["🤖 LLM API"]
    
    USER -->|Repository URL<br/>Query| SYSTEM
    SYSTEM -->|Analyze<br/>Answer| USER
    SYSTEM -->|Clone<br/>Pull| GITHUB
    SYSTEM -->|Generate Response| LLM_API
    LLM_API -->|Response| SYSTEM
```

## Data Flow Diagram - Level 1

```mermaid
graph TB
    subgraph User["User"]
        UI["Web Interface"]
    end
    
    subgraph App["Application"]
        API["API Gateway"]
        AUTH["Auth Service"]
        REPO_MGMT["Repository Manager"]
        CHAT["Chat Engine"]
    end
    
    subgraph Processing["Processing"]
        PARSER["Code Parser"]
        CHUNKER["Code Chunker"]
        EMBEDDER["Embedder"]
        RETRIEVER["Retriever"]
        RANKER["Ranker"]
        GENERATOR["Generator"]
    end
    
    subgraph Storage["Storage"]
        RELDB["Relational DB"]
        VECDB["Vector DB"]
        CACHE["Cache"]
        FILES["File Storage"]
    end
    
    subgraph External["External"]
        GITHUB["GitHub API"]
        LLM["LLM API"]
    end
    
    UI -->|Request| API
    API -->|Auth| AUTH
    API -->|Manage| REPO_MGMT
    API -->|Query| CHAT
    
    REPO_MGMT -->|Fetch| GITHUB
    REPO_MGMT -->|Process| PARSER
    PARSER -->|Segment| CHUNKER
    CHUNKER -->|Embed| EMBEDDER
    EMBEDDER -->|Store| VECDB
    EMBEDDER -->|Store| RELDB
    
    CHAT -->|Retrieve| RETRIEVER
    RETRIEVER -->|Query| VECDB
    RETRIEVER -->|Rank| RANKER
    RANKER -->|Context| GENERATOR
    GENERATOR -->|Call| LLM
    GENERATOR -->|Response| CHAT
    CHAT -->|Save| RELDB
    CHAT -->|Cache| CACHE
    
    API -->|Response| UI
```

## Data Flow Diagram - Level 2 (Detailed Chat Flow)

```mermaid
graph TD
    USER["User Query"]
    
    USER -->|Input| QUERY_VALIDATE["1. Validate Query<br/>- Length check<br/>- Language detection<br/>- Sanitization"]
    
    QUERY_VALIDATE -->|Valid| QUERY_EXPAND["2. Query Expansion<br/>- Synonym generation<br/>- Variation creation<br/>- Related concepts"]
    
    QUERY_EXPAND -->|Expanded Queries| DENSE_SEARCH["3a. Dense Search<br/>- Generate embeddings<br/>- Vector similarity<br/>- Top-K retrieval"]
    
    QUERY_EXPAND -->|Expanded Queries| SPARSE_SEARCH["3b. Sparse Search<br/>- BM25 ranking<br/>- Keyword matching<br/>- TF-IDF"]
    
    DENSE_SEARCH -->|Results| MERGE_RESULTS["4. Merge Results<br/>- Combine rankings<br/>- Remove duplicates<br/>- Normalize scores"]
    
    SPARSE_SEARCH -->|Results| MERGE_RESULTS
    
    MERGE_RESULTS -->|Candidate Set| RERANK["5. Cross-Encoder<br/>Reranking<br/>- Score relevance<br/>- Top-5 selection"]
    
    RERANK -->|Top Results| CONTEXT_BUILD["6. Build Context<br/>- Fetch full chunks<br/>- Related code<br/>- File metadata"]
    
    CONTEXT_BUILD -->|Context| PROMPT_BUILD["7. Build Prompt<br/>- Template filling<br/>- Context formatting<br/>- Instruction injection"]
    
    PROMPT_BUILD -->|Prompt| LLM_CALL["8. Call LLM<br/>- Send request<br/>- Token management<br/>- Streaming"]
    
    LLM_CALL -->|Raw Response| POSTPROCESS["9. Post-Process<br/>- Parse response<br/>- Extract code<br/>- Format output"]
    
    POSTPROCESS -->|Response| CITATION["10. Add Citations<br/>- Match references<br/>- Source linking<br/>- Confidence scoring"]
    
    CITATION -->|Final Response| OUTPUT["Output to User"]
    
    OUTPUT -->|Store| HISTORY["Save to History"]
    
    HISTORY -->|Analytics| ANALYTICS["Track Analytics"]
```

## Authentication Flow

```mermaid
graph LR
    USER["User"]
    APP["Frontend App"]
    BACKEND["Backend API"]
    GITHUB_OAUTH["GitHub OAuth"]
    DB["Database"]
    
    USER -->|Click Login| APP
    APP -->|Redirect| GITHUB_OAUTH
    GITHUB_OAUTH -->|Auth Code| APP
    APP -->|Auth Code| BACKEND
    BACKEND -->|Verify Code| GITHUB_OAUTH
    GITHUB_OAUTH -->|Access Token<br/>User Info| BACKEND
    BACKEND -->|Store/Update| DB
    BACKEND -->|JWT Token| APP
    APP -->|Store Token| APP
    APP -->|Logged In| USER
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Local["Local Development"]
        DOCKER_LOCAL["Docker Compose<br/>- Frontend<br/>- Backend<br/>- PostgreSQL<br/>- Redis<br/>- ChromaDB"]
    end
    
    subgraph Cloud["Cloud Production"]
        subgraph Frontend["Frontend Tier"]
            CDN["CDN<br/>CloudFront/Azure CDN"]
            LB_FE["Load Balancer"]
            FE_INSTANCES["Frontend Instances<br/>×3"]
        end
        
        subgraph Backend["Backend Tier"]
            LB_BE["Load Balancer"]
            API_INSTANCES["API Instances<br/>×5"]
        end
        
        subgraph Data["Data Tier"]
            PRIMARY_DB["PostgreSQL Primary"]
            REPLICA_DB["PostgreSQL Replica"]
            VECTOR_DB["Managed Vector DB<br/>Pinecone/Weaviate"]
            REDIS_CLUSTER["Redis Cluster"]
        end
        
        subgraph Storage["Storage"]
            S3["S3/Blob Storage"]
        end
    end
    
    subgraph Monitoring["Monitoring & Logging"]
        PROMETHEUS["Prometheus"]
        GRAFANA["Grafana"]
        ELK["ELK Stack"]
        SENTRY["Sentry"]
    end
    
    Cloud -.-> Monitoring
```

## Security Architecture

```mermaid
graph TB
    USER["External User"]
    
    USER -->|HTTPS| FIREWALL["Firewall<br/>DDoS Protection"]
    FIREWALL -->|WAF| WAF["Web Application Firewall<br/>- OWASP Rules<br/>- Rate Limiting<br/>- Bot Detection"]
    WAF -->|TLS| LB["Load Balancer<br/>- SSL/TLS<br/>- Certificate"]
    
    LB -->|Token| OAUTH["OAuth 2.0<br/>- GitHub Provider<br/>- Token Validation"]
    OAUTH -->|JWT| API["API Server<br/>- Token Verification<br/>- Rate Limit"]
    API -->|Auth| RBAC["RBAC Engine<br/>- User Permissions<br/>- Resource Access"]
    RBAC -->|Query| DB["Database<br/>- Encryption at Rest<br/>- Access Control"]
    
    API -->|Sanitize| INPUT["Input Validation<br/>- SQL Injection Prevention<br/>- XSS Prevention<br/>- Command Injection Prevention"]
    
    INPUT -->|Encrypt| VAULT["Secrets Vault<br/>- API Keys<br/>- Credentials<br/>- Tokens"]
    
    DB -->|Monitor| SECURITY["Security Monitoring<br/>- Anomaly Detection<br/>- Audit Logging<br/>- Compliance Checks"]
```

## Scalability Architecture

### Horizontal Scaling

```mermaid
graph TB
    LB["Load Balancer<br/>Round-robin/Least-conn"]
    
    LB -->|Route| API1["API Instance 1"]
    LB -->|Route| API2["API Instance 2"]
    LB -->|Route| API3["API Instance 3"]
    
    API1 -->|Connection Pool| DB[("Database<br/>Pooling")]
    API2 -->|Connection Pool| DB
    API3 -->|Connection Pool| DB
    
    API1 -->|Cache| REDIS["Redis Cluster<br/>Partitioned"]
    API2 -->|Cache| REDIS
    API3 -->|Cache| REDIS
    
    API1 -->|Vector Store| VDB["Vector DB<br/>Sharded"]
    API2 -->|Vector Store| VDB
    API3 -->|Vector Store| VDB
```

### Vertical Scaling

- Increase CPU/Memory for compute-intensive tasks
- Database tuning and indexing
- Cache optimization
- Connection pooling

## Performance Optimization Strategies

### Caching Strategy

1. **Query Result Cache**: Cache frequent queries (Redis)
2. **Embedding Cache**: Cache generated embeddings
3. **Citation Cache**: Cache source citations
4. **Metadata Cache**: Cache repository metadata

### Database Optimization

1. **Indexing**: Strategic index placement
2. **Partitioning**: Time-based and range partitioning
3. **Connection Pooling**: Efficient connection management
4. **Query Optimization**: Execution plan analysis

### Vector DB Optimization

1. **Indexing**: HNSW for similarity search
2. **Quantization**: Reduce memory footprint
3. **Batch Operations**: Batch inserts/updates
4. **Caching**: Popular embeddings in memory

## Disaster Recovery & HA

```mermaid
graph TB
    subgraph Primary["Primary Region"]
        PRI_DB[("Database<br/>Primary")]
        PRI_CACHE["Cache<br/>Primary"]
    end
    
    subgraph Secondary["Secondary Region<br/>Standby"]
        SEC_DB[("Database<br/>Replica")]
        SEC_CACHE["Cache<br/>Replica"]
    end
    
    subgraph Failover["Failover Manager"]
        FM["Health Checker"]
        AUTO["Automatic Failover"]
    end
    
    PRI_DB -->|Replication| SEC_DB
    PRI_CACHE -->|Replication| SEC_CACHE
    FM -->|Monitor| PRI_DB
    FM -->|Monitor| PRI_CACHE
    FM -->|Trigger| AUTO
    AUTO -->|Promote| SEC_DB
    AUTO -->|Switch| SEC_CACHE
```

## API Gateway Pattern

```mermaid
graph TB
    CLIENT["Client"]
    GATEWAY["API Gateway"]
    
    CLIENT -->|HTTP/REST| GATEWAY
    
    GATEWAY -->|Route| AUTH_SERVICE["Auth Service"]
    GATEWAY -->|Route| REPO_SERVICE["Repository Service"]
    GATEWAY -->|Route| CHAT_SERVICE["Chat Service"]
    GATEWAY -->|Route| DOC_SERVICE["Documentation Service"]
    GATEWAY -->|Route| ANALYTICS["Analytics Service"]
    
    GATEWAY -->|Middleware| RATE_LIMIT["Rate Limiter"]
    GATEWAY -->|Middleware| LOGGER["Logger"]
    GATEWAY -->|Middleware| CORS["CORS Handler"]
    GATEWAY -->|Middleware| VALIDATOR["Request Validator"]
```

## Conclusion

This architecture follows industry best practices including:
- **Separation of Concerns**: Distinct layers with clear responsibilities
- **Scalability**: Horizontal and vertical scaling capabilities
- **Reliability**: High availability, disaster recovery, monitoring
- **Security**: Multiple security layers, encryption, access control
- **Performance**: Caching, indexing, optimization strategies
- **Maintainability**: Clear structure, modular design, documentation
