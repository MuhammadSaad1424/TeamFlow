# UML & Design Diagrams

## Class Diagram - Backend Architecture

```mermaid
classDiagram
    class User {
        -uuid id
        -str github_id
        -str email
        -str display_name
        -str avatar_url
        -datetime created_at
        +get_repositories() Repository[]
        +get_conversations() Conversation[]
        +authenticate() bool
    }
    
    class Repository {
        -uuid id
        -uuid user_id
        -str repo_name
        -str repo_url
        -str language_primary
        -int file_count
        -str indexing_status
        +index_repository() bool
        +get_files() RepositoryFile[]
        +get_chunks() CodeChunk[]
        +analyze_architecture() Architecture
    }
    
    class RepositoryFile {
        -uuid id
        -uuid repository_id
        -str file_path
        -str language
        -int line_count
        +parse() CodeChunk[]
        +get_content() str
    }
    
    class CodeChunk {
        -uuid id
        -uuid file_id
        -str raw_content
        -str entity_name
        -str entity_type
        -int start_line
        +get_embedding() Embedding
        +get_citations() Citation[]
        +get_dependencies() CodeChunk[]
    }
    
    class Embedding {
        -uuid id
        -uuid chunk_id
        -vector vector
        -str model
        -float relevance_score
        +similarity_search(query: str) Embedding[]
        +rerank(candidates: Embedding[]) Embedding[]
    }
    
    class Conversation {
        -uuid id
        -uuid user_id
        -uuid repository_id
        -str title
        -int message_count
        +add_message(msg: Message) void
        +get_messages() Message[]
    }
    
    class Message {
        -uuid id
        -uuid conversation_id
        -str query_text
        -str response_text
        -float confidence_score
        +generate_response() str
        +add_citations() Citation[]
    }
    
    class Citation {
        -uuid id
        -uuid message_id
        -uuid chunk_id
        -str snippet_text
        -float relevance_score
        +get_source_code() str
    }
    
    class RAGPipeline {
        -vector_db: VectorDB
        -llm_client: LLMClient
        -embedder: EmbeddingModel
        +ingest_repository(repo: Repository) void
        +retrieve_context(query: str) Context[]
        +rerank_results(results: Context[]) Context[]
        +generate_response(context: Context[]) Response
    }
    
    class VectorDB {
        -store: ChromaDB~Pinecone
        +add_vectors(embeddings: Embedding[]) void
        +search(query_vector: vector) Embedding[]
        +delete(embedding_id: uuid) void
    }
    
    class LLMClient {
        -model: str
        -api_key: str
        +generate(prompt: str) str
        +stream(prompt: str) Iterator~str
    }
    
    class RepositoryAnalyzer {
        -tree_sitter: Parser
        -dependency_graph: Graph
        +parse_codebase(repo: Repository) void
        +extract_architecture() Architecture
        +build_dependency_graph() Graph
        +detect_patterns() Pattern[]
    }
    
    class Architecture {
        -modules: str[]
        -services: Service[]
        -patterns: str[]
        +get_data_flow() DataFlow
        +get_module_relationships() Relationship[]
    }
    
    User "1" --> "*" Repository
    User "1" --> "*" Conversation
    Repository "1" --> "*" RepositoryFile
    Repository "1" --> "*" CodeChunk
    RepositoryFile "1" --> "*" CodeChunk
    CodeChunk "1" --> "1" Embedding
    Conversation "1" --> "*" Message
    Message "*" --> "*" Citation
    Citation "*" --> "1" CodeChunk
    RAGPipeline --> VectorDB
    RAGPipeline --> LLMClient
    RAGPipeline --> Embedding
    RepositoryAnalyzer --> Repository
    RepositoryAnalyzer --> Architecture
```

## Sequence Diagram - Repository Indexing Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend as Backend API
    participant GitHubAPI as GitHub API
    participant Parser as Code Parser
    participant Chunker as Code Chunker
    participant Embedder as Embedding Module
    participant VectorDB as Vector DB
    participant PostgreSQL
    
    User->>Frontend: Submit GitHub URL
    Frontend->>Backend: POST /api/repositories
    Backend->>PostgreSQL: Create repository record
    PostgreSQL-->>Backend: Repository created
    
    Backend->>GitHubAPI: Clone/Download repo
    GitHubAPI-->>Backend: Repository files
    
    Backend->>Parser: Parse all files
    Parser->>Parser: Build AST
    Parser->>Parser: Extract functions/classes
    Parser-->>Backend: Parsed code structures
    
    Backend->>PostgreSQL: Save file metadata
    Backend->>Chunker: Split into chunks
    Chunker->>Chunker: Intelligent segmentation
    Chunker-->>Backend: Code chunks array
    
    Backend->>PostgreSQL: Save chunks
    PostgreSQL-->>Backend: Chunks stored
    
    Backend->>Embedder: Generate embeddings
    Embedder->>Embedder: Batch processing
    Embedder-->>Backend: Embeddings vector[]
    
    Backend->>VectorDB: Store vectors
    VectorDB-->>Backend: Vector IDs
    
    Backend->>PostgreSQL: Store embedding metadata
    Backend->>PostgreSQL: Update indexing_status = completed
    Backend-->>Frontend: Indexing complete
    Frontend-->>User: Success notification
```

## Sequence Diagram - Chat Query Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant QueryPreprocessor as Query Processor
    participant HybridSearch as Hybrid Search
    participant VectorDB as Vector DB
    participant Reranker as Reranker
    participant ContextBuilder as Context Builder
    participant LLM
    participant PostgreSQL
    
    User->>Frontend: Ask question
    Frontend->>Backend: POST /api/chat
    Backend->>PostgreSQL: Save user query
    
    Backend->>QueryPreprocessor: Preprocess query
    QueryPreprocessor->>QueryPreprocessor: Expand query
    QueryPreprocessor-->>Backend: Expanded queries
    
    Backend->>HybridSearch: Dense + BM25 search
    HybridSearch->>VectorDB: Semantic search
    VectorDB-->>HybridSearch: Top-100 results
    HybridSearch->>HybridSearch: BM25 search
    HybridSearch-->>Backend: Merged results
    
    Backend->>Reranker: Rerank candidates
    Reranker->>Reranker: Cross-encoder scoring
    Reranker-->>Backend: Top-5 results
    
    Backend->>ContextBuilder: Build context
    ContextBuilder->>PostgreSQL: Get full code chunks
    PostgreSQL-->>ContextBuilder: Code content
    ContextBuilder-->>Backend: Complete context
    
    Backend->>LLM: Generate response
    LLM->>LLM: Process with context
    LLM-->>Backend: Response text
    
    Backend->>Backend: Generate citations
    Backend->>Backend: Compute confidence
    Backend->>PostgreSQL: Save response
    Backend-->>Frontend: Response + citations
    Frontend-->>User: Display answer
```

## State Diagram - Repository Indexing

```mermaid
stateDiagram-v2
    [*] --> Pending: User adds repository
    
    Pending --> InProgress: Start indexing
    
    InProgress --> Parsing: Parse files
    Parsing --> Chunking: Extract chunks
    Chunking --> Embedding: Generate embeddings
    Embedding --> Storage: Store vectors
    
    Storage --> Completed: Indexing done
    
    InProgress --> Failed: Error occurs
    Parsing --> Failed
    Chunking --> Failed
    Embedding --> Failed
    Storage --> Failed
    
    Failed --> Pending: Retry
    
    Completed --> Updating: User re-indexes
    Updating --> InProgress
    
    Completed --> [*]
    Failed --> [*]
```

## Activity Diagram - Code Analysis Pipeline

```mermaid
activity
    start
    :User uploads GitHub URL;
    :Validate repository access;
    decision {Clone successful?}
        --(No)--> :Log error;
        :Notify user;
        stop
        --(Yes)-->
    :Extract all files;
    :Filter by file type;
    :Read file contents;
    :Parse with Tree-Sitter;
    :Build Abstract Syntax Tree;
    partition "Parallel Processing" {
        :Extract functions;
        :Extract classes;
        :Extract imports;
        :Extract comments;
    }
    :Merge extracted data;
    :Create code chunks;
    :Generate embeddings;
    fork
        :Store in Vector DB;
    and
        :Store in PostgreSQL;
    end fork
    :Build dependency graph;
    :Analyze architecture;
    :Generate metadata;
    :Update repository status;
    :Notify user of completion;
    stop
```

## Component Diagram - System Components

```mermaid
graph TB
    subgraph Presentation["Presentation Layer"]
        Web["Web Dashboard<br/>Next.js"]
        Mobile["Mobile App<br/>React Native"]
    end
    
    subgraph API["API Layer"]
        Gateway["API Gateway<br/>FastAPI"]
        Auth["Auth Middleware"]
        RateLimit["Rate Limiter"]
    end
    
    subgraph Services["Business Logic"]
        AuthSvc["Auth Service"]
        RepoSvc["Repository Service"]
        ChatSvc["Chat Service"]
        DocSvc["Documentation Service"]
        AnalyticsSvc["Analytics Service"]
    end
    
    subgraph RAG["RAG Pipeline"]
        Parser["Code Parser"]
        Chunker["Code Chunker"]
        Embedder["Embedding Generator"]
        Retriever["Retriever"]
        Reranker["Reranker"]
        Generator["LLM Generator"]
    end
    
    subgraph Data["Data & Storage"]
        PostgreSQL["PostgreSQL"]
        VectorDB["ChromaDB/Pinecone"]
        Redis["Redis Cache"]
        S3["S3 Storage"]
    end
    
    subgraph External["External Services"]
        GitHub["GitHub API"]
        OpenAI["OpenAI API"]
        LLMProvider["LLM Providers"]
    end
    
    Web -.-> Gateway
    Mobile -.-> Gateway
    
    Gateway --> Auth
    Gateway --> RateLimit
    
    Auth --> AuthSvc
    AuthSvc --> PostgreSQL
    
    RateLimit --> RepoSvc
    RateLimit --> ChatSvc
    RateLimit --> DocSvc
    RateLimit --> AnalyticsSvc
    
    RepoSvc --> Parser
    Parser --> Chunker
    Chunker --> Embedder
    Embedder --> VectorDB
    Embedder --> PostgreSQL
    
    ChatSvc --> Retriever
    Retriever --> VectorDB
    Retriever --> Reranker
    Reranker --> Generator
    Generator --> LLMProvider
    Generator --> PostgreSQL
    
    DocSvc --> PostgreSQL
    AnalyticsSvc --> PostgreSQL
    
    RepoSvc --> GitHub
    RepoSvc --> S3
    
    Retriever --> Redis
    Generator --> Redis
```

## Deployment Diagram

```mermaid
graph TB
    subgraph Client["Client Tier"]
        Browser["Web Browser"]
        Mobile["Mobile Device"]
    end
    
    subgraph CloudFront["CDN"]
        CF["CloudFront/Azure CDN"]
    end
    
    subgraph LB["Load Balancing"]
        LB_Main["Main Load Balancer"]
        LB_API["API Load Balancer"]
    end
    
    subgraph Frontend["Frontend Instances"]
        FE1["Frontend Instance 1"]
        FE2["Frontend Instance 2"]
        FE3["Frontend Instance 3"]
    end
    
    subgraph API["API Instances"]
        API1["API Instance 1"]
        API2["API Instance 2"]
        API3["API Instance 3"]
    end
    
    subgraph DB["Database Layer"]
        Primary["PostgreSQL Primary"]
        Replica["PostgreSQL Replica"]
    end
    
    subgraph Cache["Cache Layer"]
        Redis["Redis Cluster"]
    end
    
    subgraph VectorStore["Vector Store"]
        Pinecone["Pinecone/ChromaDB"]
    end
    
    subgraph Monitoring["Monitoring"]
        Prometheus["Prometheus"]
        Grafana["Grafana"]
        Sentry["Sentry"]
    end
    
    Browser --> CF
    Mobile --> CF
    CF --> LB_Main
    
    LB_Main --> FE1
    LB_Main --> FE2
    LB_Main --> FE3
    
    FE1 --> LB_API
    FE2 --> LB_API
    FE3 --> LB_API
    
    LB_API --> API1
    LB_API --> API2
    LB_API --> API3
    
    API1 --> Primary
    API2 --> Primary
    API3 --> Primary
    
    Primary --> Replica
    
    API1 --> Redis
    API2 --> Redis
    API3 --> Redis
    
    API1 --> Pinecone
    API2 --> Pinecone
    API3 --> Pinecone
    
    API1 -.-> Prometheus
    API2 -.-> Prometheus
    API3 -.-> Prometheus
    
    Prometheus --> Grafana
    API1 -.-> Sentry
```

## Data Flow Diagram - Detailed Chat Processing

```mermaid
graph TD
    Q["User Query<br/>String"]
    
    Q --> V1["Validate Input<br/>- Length check<br/>- Language detection<br/>- Sanitization"]
    V1 --> E1["Query Expansion<br/>- Synonyms<br/>- Related terms<br/>- Variations"]
    
    E1 --> D1["Dense Retrieval<br/>- Generate embedding<br/>- Vector search<br/>- Top-K results"]
    
    E1 --> S1["Sparse Retrieval<br/>- BM25 search<br/>- Keyword matching<br/>- TF-IDF scoring"]
    
    D1 --> M1["Merge Results<br/>- Combine scores<br/>- Remove duplicates<br/>- Normalize"]
    S1 --> M1
    
    M1 --> R1["Reranking<br/>- Cross-encoder scoring<br/>- Top-5 selection<br/>- Confidence calc"]
    
    R1 --> C1["Context Building<br/>- Get full chunks<br/>- Surrounding code<br/>- Dependencies"]
    
    C1 --> P1["Prompt Building<br/>- Template creation<br/>- Context injection<br/>- Instructions"]
    
    P1 --> L1["LLM Call<br/>- Token counting<br/>- Request sending<br/>- Response streaming"]
    
    L1 --> PP1["Post-Processing<br/>- Parse response<br/>- Extract code<br/>- Format output"]
    
    PP1 --> CT1["Citation Generation<br/>- Link references<br/>- Verify accuracy<br/>- Confidence scoring"]
    
    CT1 --> O["Final Output<br/>Response + Citations"]
```

## Use Case Diagram

```mermaid
usecase
    UC_User as "(A) User"
    UC_Dev as "(B) Developer"
    UC_Org as "(C) Organization"
    
    UC_Browse as "Browse Codebase"
    UC_Chat as "Ask AI Questions"
    UC_Generate_Docs as "Generate Documentation"
    UC_Analyze_Arch as "Analyze Architecture"
    UC_Track_Deps as "Track Dependencies"
    UC_Manage_Repos as "Manage Repositories"
    UC_View_Analytics as "View Analytics"
    UC_Collaborate as "Collaborate with Team"
    
    UC_User --> UC_Chat
    UC_User --> UC_Browse
    
    UC_Dev --> UC_Chat
    UC_Dev --> UC_Analyze_Arch
    UC_Dev --> UC_Track_Deps
    UC_Dev --> UC_Generate_Docs
    UC_Dev --> UC_Manage_Repos
    
    UC_Org --> UC_View_Analytics
    UC_Org --> UC_Collaborate
    UC_Org --> UC_Manage_Repos
```

## Entity Relationship Diagram (Visual)

```mermaid
erDiagram
    USERS ||--o{ REPOSITORIES : "owns"
    USERS ||--o{ CONVERSATIONS : "initiates"
    USERS ||--o{ API_KEYS : "generates"
    
    REPOSITORIES ||--o{ REPOSITORY_FILES : "contains"
    REPOSITORIES ||--o{ CODE_CHUNKS : "contains"
    REPOSITORIES ||--o{ EMBEDDINGS : "has"
    REPOSITORIES ||--o{ REPOSITORY_METADATA : "has"
    
    REPOSITORY_FILES ||--o{ CODE_CHUNKS : "divided into"
    
    CODE_CHUNKS ||--o{ EMBEDDINGS : "generates"
    CODE_CHUNKS ||--o{ CITATIONS : "cited by"
    
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    MESSAGES ||--o{ CITATIONS : "includes"
    
    EMBEDDINGS ||--o{ VECTOR_METADATA : "has"
```

## Technology Stack Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend Layer"]
        N["Next.js 15"]
        R["React 18"]
        TS["TypeScript"]
        TC["Tailwind CSS"]
        SH["ShadCN UI"]
        Z["Zustand"]
        FM["Framer Motion"]
    end
    
    subgraph Backend["Backend Layer"]
        F["FastAPI"]
        P["Python 3.12"]
        PD["Pydantic"]
        A["AsyncIO"]
    end
    
    subgraph AI["AI & ML Layer"]
        LC["LangChain"]
        LG["LangGraph"]
        TS1["Tree-Sitter"]
        OAI["OpenAI API"]
        CE["Cross-Encoder"]
    end
    
    subgraph Data["Data Layer"]
        PG["PostgreSQL 15"]
        CD["ChromaDB/Pinecone"]
        RD["Redis"]
        SA["SQLAlchemy"]
    end
    
    subgraph Deployment["Deployment"]
        DK["Docker"]
        DC["Docker Compose"]
        K8S["Kubernetes"]
        AZ["Azure/AWS"]
    end
    
    N --> TS
    R --> TC
    TC --> SH
    SH --> Z
    Z --> FM
    
    F --> P
    P --> PD
    PD --> A
    
    LC --> LG
    LG --> TS1
    TS1 --> OAI
    OAI --> CE
    
    SA --> PG
    PG --> CD
    CD --> RD
    
    DK --> DC
    DC --> K8S
    K8S --> AZ
```

## Machine Learning Pipeline

```mermaid
graph LR
    INPUT["Raw Code"]
    PARSE["Parse Code<br/>Tree-Sitter"]
    FEATURE["Extract Features<br/>- Syntax<br/>- Semantics<br/>- Structure"]
    CHUNK["Create Chunks<br/>Intelligent Segmentation"]
    EMBED["Generate Embeddings<br/>text-embedding-3-large"]
    NORM["Normalize Vectors<br/>L2 Normalization"]
    INDEX["Build Index<br/>HNSW"]
    QUERY["Query Processing<br/>Semantic Search"]
    RERANK["Reranking<br/>Cross-Encoder"]
    CONTEXT["Context Window<br/>Retrieved Chunks"]
    LLM["LLM Processing<br/>GPT-4o/Llama"]
    OUTPUT["Response<br/>+ Citations"]
    
    INPUT --> PARSE
    PARSE --> FEATURE
    FEATURE --> CHUNK
    CHUNK --> EMBED
    EMBED --> NORM
    NORM --> INDEX
    INDEX --> QUERY
    QUERY --> RERANK
    RERANK --> CONTEXT
    CONTEXT --> LLM
    LLM --> OUTPUT
```

## System Quality Attributes

```mermaid
graph TB
    SYSTEM["TeamFlow AI<br/>System"]
    
    SYSTEM --> PERF["Performance<br/>- <3s query response<br/>- 10k embeddings/sec<br/>- 99.9% uptime"]
    SYSTEM --> SCALE["Scalability<br/>- 100k+ file repos<br/>- Horizontal scaling<br/>- Vector partitioning"]
    SYSTEM --> SEC["Security<br/>- End-to-end encryption<br/>- GitHub OAuth<br/>- RBAC"]
    SYSTEM --> REL["Reliability<br/>- Automated backups<br/>- Failover<br/>- Error handling"]
    SYSTEM --> MAINT["Maintainability<br/>- Clean code<br/>- Comprehensive tests<br/>- Documentation"]
```

## Conclusion

These diagrams provide a comprehensive view of:
- System structure and components
- Data flows and interactions
- Deployment architecture
- Technology integration
- Quality attributes and design patterns
