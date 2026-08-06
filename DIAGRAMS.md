# PANDORA Architecture Diagrams

**Version:** 1.0.0  
**Last Updated:** 2026-08-05

This document contains all architecture diagrams in Mermaid format for easy rendering in documentation tools.

---

## 1. System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Application<br/>Next.js]
        MOB[Mobile Apps<br/>React Native]
        API_CLIENT[API Clients]
        BOT[AI Chatbots]
    end

    subgraph "Edge Layer"
        CDN[Global CDN<br/>CloudFlare]
        WAF[Web Application<br/>Firewall]
        LB[Load Balancer<br/>ALB]
        EDGE_CACHE[Edge Cache<br/>Workers]
    end

    subgraph "API Gateway"
        KONG[Kong Gateway]
        AUTH[Auth Service]
        RATE[Rate Limiter]
        TRACING[Distributed<br/>Tracing]
    end

    subgraph "Core Services"
        USER[User Service]
        CONTENT[Content Service]
        SEARCH[Search Service]
        LEARNING[Learning Service]
        QUIZ[Quiz Service]
        RECOMMEND[Recommendation Service]
        AI[AI Gateway]
        CRAWLER[Crawler Service]
    end

    subgraph "AI/ML Layer"
        LLM_GATEWAY[LLM Gateway<br/>vLLM]
        EMBEDDING[Embedding Service]
        RERANKER[Reranker]
        VECTOR_DB[(Vector DB<br/>Qdrant)]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL)]
        REDIS[(Redis)]
        NEO4J[(Knowledge Graph<br/>Neo4j)]
        ES[(Elasticsearch)]
        KAFKA[(Kafka)]
        S3[(Object Storage<br/>S3/MinIO)]
    end

    subgraph "Infrastructure"
        K8S[Kubernetes]
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
        LOKI[Loki]
        JAEGER[Jaeger]
    end

    WEB --> CDN
    MOB --> CDN
    API_CLIENT --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> KONG
    KONG --> AUTH
    KONG --> RATE
    KONG --> TRACING
    AUTH --> USER
    USER --> PG
    CONTENT --> PG
    CONTENT --> S3
    SEARCH --> ES
    SEARCH --> VECTOR_DB
    LEARNING --> PG
    QUIZ --> PG
    RECOMMEND --> PG
    RECOMMEND --> VECTOR_DB
    AI --> LLM_GATEWAY
    AI --> VECTOR_DB
    EMBEDDING --> VECTOR_DB
    CRAWLER --> KAFKA
    KAFKA --> PG
    KAFKA --> NEO4J
    KAFKA --> VECTOR_DB
    USER --> REDIS
    CONTENT --> REDIS
    LEARNING --> REDIS
    NEO4J --> KAFKA
    K8S --> PROMETHEUS
    K8S --> GRAFANA
    K8S --> LOKI
    K8S --> JAEGER
```

---

## 2. Data Flow

```mermaid
flowchart LR
    subgraph "Content Ingestion"
        A[Web Crawler] --> B[Robots.txt Check]
        B --> C{Legal?}
        C -->|Yes| D[License Validator]
        C -->|No| E[Skip]
        D --> F[Content Extractor]
        F --> G[Cleaner]
        G --> H[Chunker]
        H --> I[Embedding]
        I --> J[Vector DB]
        G --> K[Knowledge Graph]
        K --> L[Neo4j]
    end

    subgraph "User Request"
        M[User Query] --> N[API Gateway]
        N --> O[Auth]
        O --> P[Search Service]
        P --> Q[Vector Search]
        P --> R[BM25 Search]
        Q --> S[RRF Merger]
        R --> S
        S --> T[Reranker]
        T --> U[Results]
    end

    subgraph "AI Processing"
        U --> V[LLM Gateway]
        V --> W[Curriculum Gen]
        V --> X[Quiz Gen]
        V --> Y[Research]
        W --> Z[Response]
        X --> Z
        Y --> Z
    end
```

---

## 3. Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as API Gateway
    participant AUTH as Auth Service
    participant IDP as Identity Provider
    participant DB as User DB
    participant CACHE as Redis

    U->>FE: Click Login
    FE->>API: POST /auth/login
    API->>AUTH: Validate Request
    AUTH->>IDP: SAML/OAuth Redirect
    IDP->>U: Show Login Form
    U->>IDP: Enter Credentials
    IDP->>AUTH: Return Token/Assertion
    AUTH->>DB: Get/Create User
    AUTH->>CACHE: Store Session
    AUTH->>API: Return JWT
    API->>FE: Return Auth Response
    FE->>U: Login Success
```

---

## 4. RAG Pipeline

```mermaid
flowchart TD
    subgraph "Ingestion"
        A[Raw Content] --> B[Content Classifier]
        B --> C[Format Detector]
        C --> D{HTML?}
        D -->|Yes| E[HTML Parser]
        D -->|No| F{PDF?}
        F -->|Yes| G[PDF Parser]
        F -->|No| H[Generic Parser]
        E --> I[Content Cleaner]
        G --> I
        H --> I
        I --> J[Metadata Extractor]
    end

    subgraph "Chunking"
        J --> K[Chunk Strategy]
        K --> L{Hierarchical?}
        L -->|Yes| M[Structure-Aware]
        L -->|No| N{Semantic?}
        N -->|Yes| O[Embedding-Guided]
        N -->|No| P[Fixed Size]
        M --> Q[Chunks]
        O --> Q
        P --> Q
    end

    subgraph "Processing"
        Q --> R[Quality Filter]
        R -->|Pass| S[Entity Extractor]
        R -->|Fail| T[Review Queue]
        S --> U[Concept Tagger]
        U --> V[Embedding Gen]
        V --> W[(Vector DB)]
        U --> X[Graph Builder]
        X --> Y[(Neo4j)]
    end

    subgraph "Query"
        Z[User Query] --> AA[Query Processor]
        AA --> AB[Embedding]
        AB --> AC[Hybrid Search]
        AC --> AD{Rerank?}
        AD -->|Yes| AE[Reranker Model]
        AD -->|No| AF[Return Results]
        AE --> AF
    end
```

---

## 5. Learning Path Generation

```mermaid
flowchart TB
    subgraph "Input"
        A[Learning Goal] --> B[Goal Analyzer]
        B --> C[Target Level]
        C --> D[Current Knowledge]
        D --> E[Prerequisite Graph]
    end

    subgraph "Generation"
        E --> F[Concept Planner]
        F --> G[Sequence Optimizer]
        G --> H[Module Builder]
        H --> I[Lesson Designer]
        I --> J[Assessment Creator]
        J --> K[Resource Matcher]
    end

    subgraph "AI Enhancement"
        K --> L[LLM: Refine Content]
        L --> M[LLM: Generate Examples]
        M --> N[LLM: Create Quizzes]
        N --> O[Quality Checker]
    end

    subgraph "Output"
        O --> P[Curriculum JSON]
        P --> Q[Human Review]
        Q -->|Approve| R[Save Path]
        Q -->|Revise| H
    end
```

---

## 6. Knowledge Graph Schema

```mermaid
erDiagram
    CONCEPT ||--o{ CONCEPT : "prerequisite"
    CONCEPT ||--o{ CONCEPT : "leads_to"
    CONCEPT ||--o{ CONCEPT : "same_as"
    CONCEPT ||--o{ CONTENT : "taught_in"
    CONCEPT ||--o{ ASSESSMENT : "assessed_in"
    CONCEPT ||--o{ SKILL : "develops"
    CONCEPT ||--o| STANDARD : "aligns_to"
    CONTENT ||--o{ LESSON : "has"
    LESSON ||--o| ASSESSMENT : "has"
    LESSON ||--o{ USER_PROGRESS : "tracked_in"
    MODULE ||--o{ LESSON : "contains"
    MODULE ||--o| COURSE : "part_of"
    COURSE ||--o{ LEARNING_PATH : "enrolled_in"
    USER ||--o{ LEARNING_PATH : "creates"
    USER ||--o{ USER_PROGRESS : "has"

    CONCEPT {
        uuid id PK
        string name
        string definition
        string domain
        int education_level
        vector embedding
        timestamp created_at
    }

    CONTENT {
        uuid id PK
        string title
        text body
        string content_type
        int education_level
        string license
        jsonb metadata
        timestamp indexed_at
    }

    LESSON {
        uuid id PK
        uuid content_id FK
        string title
        int order_index
        jsonb learning_objectives
        int estimated_minutes
    }

    MODULE {
        uuid id PK
        uuid course_id FK
        string title
        int order_index
        string description
    }

    COURSE {
        uuid id PK
        string title
        string description
        int education_level
        jsonb curriculum
        enum status
    }

    LEARNING_PATH {
        uuid id PK
        uuid user_id FK
        uuid course_id FK
        float progress
        enum status
        timestamp started_at
    }

    USER {
        uuid id PK
        string email
        string full_name
        jsonb preferences
        jsonb knowledge_state
    }
```

---

## 7. Deployment Architecture

```mermaid
flowchart TB
    subgraph "Cloud Provider AWS"
        subgraph "us-east-1 (Primary)"
            EKS1[Production EKS]
            RDS1[(RDS Primary)]
            S3_1[(S3)]
            CF[CloudFront]
        end

        subgraph "us-west-2 (Secondary)"
            EKS2[DR EKS]
            RDS2[(RDS Replica)]
        end

        subgraph "Global"
            Route53[Route 53]
            WAF[CloudFlare WAF]
        end
    end

    subgraph "GCP"
        GKE[GKE Analytics]
        GCS[(Cloud Storage)]
    end

    subgraph "Edge"
        CF --> WAF
        WAF --> Route53
    end

    Route53 --> EKS1
    Route53 -.->|DR Failover| EKS2
    EKS1 --> RDS1
    EKS2 --> RDS2
    RDS1 -->|Async Replica| RDS2
    EKS1 --> S3_1
    EKS1 --> GCS
    EKS1 --> GKE
```

---

## 8. CI/CD Pipeline

```mermaid
flowchart LR
    subgraph "Code"
        A[Code Commit] --> B[Pre-commit]
        B --> C{Lint Pass?}
        C -->|No| D[Fail]
        C -->|Yes| E[Push]
    end

    subgraph "CI"
        E --> F[GitHub Actions]
        F --> G[Build]
        G --> H[Unit Tests]
        H --> I[Integration Tests]
        I --> J[Security Scan]
        J --> K[Build Image]
        K --> L[Push Registry]
    end

    subgraph "CD"
        L --> M[ArgoCD]
        M --> N[Deploy Staging]
        N --> O[E2E Tests]
        O --> P{Tests Pass?}
        P -->|No| Q[Rollback]
        P -->|Yes| R[Approval]
        R --> S[Deploy Production]
        S --> T[Smoke Tests]
        T --> U[Monitor]
    end
```

---

## 9. Monitoring Architecture

```mermaid
flowchart TB
    subgraph "Services"
        A[User Service]
        B[Content Service]
        C[Search Service]
        D[Learning Service]
        E[AI Gateway]
    end

    subgraph "Collection"
        A --> P1[Prometheus]
        B --> P2[Prometheus]
        C --> P3[Prometheus]
        D --> P4[Prometheus]
        E --> P5[Prometheus]
    end

    subgraph "Aggregation"
        P1 --> PROM[Prometheus Server]
        P2 --> PROM
        P3 --> PROM
        P4 --> PROM
        P5 --> PROM
    end

    subgraph "Visualization"
        PROM --> GRAFANA[Grafana]
        PROM --> ALERT[Alertmanager]
    end

    subgraph "Logs"
        A --> LOKI[Loki]
        B --> LOKI
        C --> LOKI
        D --> LOKI
        E --> LOKI
        LOKI --> GRAFANA
    end

    subgraph "Traces"
        A --> JAEGER[Jaeger]
        B --> JAEGER
        C --> JAEGER
        D --> JAEGER
        E --> JAEGER
        JAEGER --> GRAFANA
    end

    subgraph "Alerting"
        ALERT --> PD[PagerDuty]
        ALERT --> SLACK[Slack]
    end
```

---

## 10. Recommendation Engine

```mermaid
flowchart TB
    subgraph "Input Features"
        A[User Profile] --> F[Feature Store]
        B[User History] --> F
        C[Content Features] --> F
        D[Context] --> F
    end

    subgraph "Candidate Generation"
        F --> G[Multi-Armed Bandit]
        G --> H[Content-Based]
        G --> I[Collaborative]
        G --> J[Knowledge-Graph]
        H --> K[Candidates]
        I --> K
        J --> K
    end

    subgraph "Ranking"
        K --> L[Ranking Model]
        L --> M[Diversity Filter]
        M --> N[Exposure Control]
        N --> O[Ranking Output]
    end

    subgraph "Feedback Loop"
        O --> P[User Response]
        P --> Q[Reward Signal]
        Q --> G
    end
```

---

## 11. Quiz Adaptive Testing

```mermaid
flowchart TB
    subgraph "Start"
        A[Test Start] --> B[Initialize Ability]
        B --> C[Select Item]
    end

    subgraph "Adaptive Loop"
        C --> D[Present Question]
        D --> E[User Response]
        E --> F{Time Up?}
        F -->|No| G[Update Ability]
        F -->|Yes| H[End Test]
        G --> I{Stop Criterion?}
        I -->|No| C
        I -->|Yes| H
    end

    subgraph "Estimation"
        G --> J[Maximum Likelihood]
        J --> K[Standard Error]
        K --> L[Info Threshold]
    end

    subgraph "Output"
        H --> M[Calculate Score]
        M --> N[Generate Feedback]
        N --> O[Test Report]
    end
```

---

## 12. Database Architecture

```mermaid
flowchart TB
    subgraph "Primary Region"
        PG_MASTER[(PostgreSQL<br/>Primary)]
        PG_MASTER --> PG_REPLICA1[(PostgreSQL<br/>Read Replica 1)]
        PG_MASTER --> PG_REPLICA2[(PostgreSQL<br/>Read Replica 2)]
    end

    subgraph "Cache Layer"
        REDIS_MASTER[(Redis<br/>Master)]
        REDIS_MASTER --> REDIS_REPLICA[(Redis<br/>Replica)]
    end

    subgraph "Search"
        ES_MASTER[(Elasticsearch<br/>Master)]
        ES_MASTER --> ES_NODE1[(ES Node)]
        ES_MASTER --> ES_NODE2[(ES Node)]
    end

    subgraph "Vectors"
        QDRANT[(Qdrant<br/>Cluster)]
    end

    subgraph "Graph"
        NEO4J[(Neo4j<br/>Cluster)]
    end

    subgraph "Object Storage"
        S3[(S3<br/>Bucket)]
    end
```

---

## 13. Security Architecture

```mermaid
flowchart TB
    subgraph "Perimeter"
        WAF[CloudFlare WAF]
        DDOS[DDoS Protection]
        RATE[Rate Limiting]
    end

    subgraph "Network"
        VPC[VPC]
        SG[Security Groups]
        NACL[Network ACLs]
        VPN[VPN/Zero Trust]
    end

    subgraph "Service Mesh"
        ISTIO[Istio Service Mesh]
        MTLS[mTLS]
        POLICY[Authorization<br/>Policies]
    end

    subgraph "Application"
        AUTH[Authentication]
        AUTHZ[Authorization]
        INPUT[Input Validation]
        OUTPUT[Output Encoding]
    end

    subgraph "Data"
        ENCRYPT_TRANSIT[Encryption<br/>in Transit]
        ENCRYPT_REST[Encryption<br/>at Rest]
        VAULT[HashiCorp Vault]
        KMS[AWS KMS]
    end

    WAF --> DDOS
    DDOS --> RATE
    RATE --> VPC
    VPC --> SG
    VPC --> NACL
    SG --> ISTIO
    NACL --> VPN
    ISTIO --> MTLS
    ISTIO --> POLICY
    MTLS --> AUTH
    POLICY --> AUTHZ
    AUTHZ --> INPUT
    INPUT --> OUTPUT
    OUTPUT --> ENCRYPT_TRANSIT
    ENCRYPT_TRANSIT --> ENCRYPT_REST
    ENCRYPT_REST --> VAULT
    ENCRYPT_REST --> KMS
```

---

## 14. API Gateway Flow

```mermaid
flowchart TB
    subgraph "Request"
        A[Client] --> B[Load Balancer]
    end

    subgraph "Gateway"
        B --> C[Rate Limiter]
        C --> D[Auth Validator]
        D --> E{Cached?}
        E -->|Yes| F[Return Cache]
        E -->|No| G[Route to Service]
    end

    subgraph "Services"
        G --> H[User Service]
        G --> I[Content Service]
        G --> J[Search Service]
        G --> K[AI Gateway]
    end

    subgraph "Response"
        H --> L[Log Request]
        I --> L
        J --> L
        K --> L
        L --> M[Add Headers]
        M --> N[Return to Client]
    end
```

---

## 15. Event-Driven Architecture

```mermaid
flowchart LR
    subgraph "Producers"
        A[User Service]
        B[Content Service]
        C[Crawler]
        D[Learning Service]
    end

    subgraph "Kafka"
        E[(Topic:<br/>user.events)]
        F[(Topic:<br/>content.events)]
        G[(Topic:<br/>learning.events)]
        H[(Topic:<br/>dlq)]
    end

    subgraph "Consumers"
        A --> E
        B --> F
        C --> F
        D --> G
        E --> I[Analytics]
        E --> J[Recommendations]
        F --> K[Search Indexer]
        F --> L[Vector Indexer]
        F -->|Error| H
        G --> M[Progress Tracker]
        G --> N[Notifications]
    end
```

---

## 16. Microservices Communication

```mermaid
flowchart TB
    subgraph "Sync Communication"
        A[API Gateway] -->|HTTP/REST| B[User Service]
        A -->|HTTP/REST| C[Content Service]
        A -->|HTTP/REST| D[Search Service]
        B -->|gRPC| E[AI Gateway]
    end

    subgraph "Async Communication"
        C -->|Kafka| F[Event Bus]
        D -->|Kafka| F
        F -->|Consumer| G[Recommendation Service]
        F -->|Consumer| H[Analytics Service]
        F -->|Consumer| I[Notification Service]
    end

    subgraph "Data Access"
        B -->|SQL| J[(PostgreSQL)]
        C -->|SQL| J
        D -->|SQL| J
        C -->|S3| K[(Object Storage)]
        G -->|Vector| L[(Qdrant)]
        I -->|Cache| M[(Redis)]
    end
```

---

## 17. Frontend Architecture

```mermaid
flowchart TB
    subgraph "Pages"
        A[Dashboard]
        B[Course View]
        C[Learning Path]
        D[Search Results]
        E[Profile]
    end

    subgraph "Shared Components"
        F[Button]
        G[Card]
        H[Modal]
        I[Form]
        J[Table]
    end

    subgraph "Learning Components"
        K[Video Player]
        L[Quiz Component]
        M[Progress Bar]
        N[Concept Map]
        O[Timeline]
    end

    subgraph "State Management"
        P[Zustand Store]
        Q[React Query]
        R[URL State]
    end

    subgraph "API Layer"
        S[API Client]
        T[Auth Interceptor]
        U[Error Handler]
    end

    A --> F
    A --> G
    B --> K
    B --> L
    C --> M
    C --> N
    D --> O
    D --> J
    P --> Q
    Q --> S
    S --> T
    T --> U
```

---

## 18. Development Workflow

```mermaid
flowchart TB
    subgraph "Local Development"
        A[Feature Branch] --> B[Code Changes]
        B --> C[Pre-commit Hooks]
        C --> D[Run Tests]
    end

    subgraph "Pull Request"
        D --> E[Push Branch]
        E --> F[Create PR]
        F --> G[CI Pipeline]
        G --> H{Tests Pass?}
        H -->|No| I[Fix Issues]
        I --> B
        H -->|Yes| J[Code Review]
    end

    subgraph "Merge"
        J --> K[Approve & Merge]
        K --> L[Main Branch]
        L --> M[Tag Release]
    end

    subgraph "Deployment"
        M --> N[Deploy Staging]
        N --> O[E2E Tests]
        O --> P{Tests Pass?}
        P -->|No| Q[Rollback]
        P -->|Yes| R[Deploy Production]
    end
```

---

## 19. Content Licensing Flow

```mermaid
flowchart TD
    A[Crawl Content] --> B{Respect robots.txt?}
    B -->|No| Z[Skip]
    B -->|Yes| C{Valid Source?}
    C -->|No| Z
    C -->|Yes| D[Extract Content]
    D --> E{License Detected?}
    E -->|No| F[Queue for Review]
    E -->|Yes| G{License Type?}
    G -->|CC0| H[Full Index]
    G -->|CC BY| I[Index + Attribute]
    G -->|CC BY-SA| J[Index + ShareAlike]
    G -->|CC BY-NC| K[Index Non-Commercial]
    G -->|Proprietary| L[Exclude]
    G -->|Unknown| F
    F --> M[Human Review]
    M -->|Approved| H
    M -->|Denied| L
    H --> N[Generate Embeddings]
    I --> N
    J --> N
    K --> N
    N --> O[Store in Vector DB]
    O --> P[Index in Search]
```

---

## 20. Cost Optimization Strategy

```mermaid
flowchart TB
    subgraph "Compute Optimization"
        A[Reserved Instances] -->|1-3 yr| B[40% Savings]
        C[Spot Instances] -->|Batch| D[60% Savings]
        E[Auto Scaling] -->|Scale to Zero| F[25% Savings]
    end

    subgraph "Data Optimization"
        G[Aggressive Caching] --> H[Reduce DB Load]
        I[CDN Caching] --> J[Reduce Bandwidth]
        K[Compression] --> L[Reduce Storage]
    end

    subgraph "ML Optimization"
        M[Quantized Models] --> N[GPU Memory]
        O[Batch Processing] --> P[Efficiency]
        Q[Caching Embeddings] --> R[Reduce Compute]
    end

    subgraph "Monitoring"
        S[Cost Dashboard] --> T[Real-time Alerts]
        T --> U[Budget Limits]
    end
```

---

*These diagrams can be rendered in any Mermaid-compatible viewer including GitHub, GitLab, Notion, Obsidian, and more.*
