# Architecture Decision Records (ADR)

**Status:** Active  
**Last Updated:** 2026-08-05

---

## ADR-001: Microservices Architecture over Monolith

**Date:** 2026-01-15  
**Status:** Accepted

### Context
PANDORA needs to support multiple independent features (content search, learning paths, AI generation, assessments) that can be developed, deployed, and scaled independently.

### Decision
Adopt microservices architecture with 8-10 distinct services.

### Consequences

**Positive:**
- Independent deployment and scaling
- Technology flexibility per service
- Fault isolation
- Team autonomy
- Easier to understand individual services

**Negative:**
- Increased operational complexity
- Network latency between services
- Distributed debugging challenges
- Data consistency complexities
- More infrastructure to manage

**Mitigation:**
- Service mesh (Istio) for mTLS and traffic management
- Centralized logging with correlation IDs
- Shared library for common patterns
- Contract testing between services

---

## ADR-002: PostgreSQL as Primary Database

**Date:** 2026-01-16  
**Status:** Accepted

### Context
We need a relational database for user data, learning paths, and structured content metadata. Strong ACID guarantees are essential.

### Decision
Use PostgreSQL 16 as the primary database with the following extensions:
- `pgvector` for hybrid vector search
- `pg_trgm` for fuzzy text search
- `uuid-ossp` for UUID generation

### Consequences

**Positive:**
- ACID compliance for critical transactions
- Excellent performance with proper indexing
- Rich feature set (JSON, full-text, etc.)
- Strong community and documentation
- Cost-effective (managed options available)
- Vector search capability with pgvector

**Negative:**
- Vertical scaling limits
- Complex sharding for very large scale
- License considerations for some extensions

**Alternatives Considered:**
- **MySQL**: Less feature-rich, worse for JSON operations
- **CockroachDB**: Better horizontal scaling, higher latency
- **MongoDB**: No joins, weaker for relational data

---

## ADR-003: Qdrant for Vector Database

**Date:** 2026-01-18  
**Status:** Accepted

### Context
We need to store and query high-dimensional embeddings for semantic search and RAG applications.

### Decision
Use Qdrant as the vector database with hybrid filtering support.

### Consequences

**Positive:**
- Rust-based for excellent performance
- Hybrid filtering (vector + metadata)
- Efficient quantization (int8, binary)
- Easy deployment (Docker, managed)
- Good API and SDK support

**Negative:**
- Smaller community than Milvus
- Less battle-tested at extreme scale

**Alternatives Considered:**
- **Milvus**: Larger community, but more complex
- **Weaviate**: More features but slower
- **pgvector**: Simpler but less performant at scale

---

## ADR-004: Neo4j for Knowledge Graph

**Date:** 2026-01-20  
**Status:** Accepted

### Context
We need to model educational concepts, prerequisites, and relationships between content for curriculum generation and recommendations.

### Decision
Use Neo4j Community Edition (self-hosted) with the Graph Data Science library.

### Consequences

**Positive:**
- Excellent Cypher query language
- Rich visualization tools
- GDS library for graph algorithms
- Good performance for connected data

**Negative:**
- Enterprise features require paid license
- Clustering is enterprise-only
- Memory-intensive for large graphs

**Alternatives Considered:**
- **Amazon Neptune**: Managed but expensive, less flexible
- **ArangoDB**: Multi-model but weaker graph ecosystem
- **Redis Graph**: Simpler but less mature

---

## ADR-005: Kafka for Event Streaming

**Date:** 2026-01-22  
**Status:** Accepted

### Context
We need asynchronous communication between services for:
- Content indexing pipeline
- User activity tracking
- Cross-service notifications
- ML feature updates

### Decision
Use Apache Kafka with:
- Schema Registry for message validation
- Kafka Connect for data integration
- KSQL for stream processing

### Consequences

**Positive:**
- Durable message storage
- Replay capability for failed processing
- Exactly-once semantics
- High throughput
- Mature ecosystem

**Negative:**
- Operational complexity
- Requires careful topic partitioning strategy
- Higher resource usage

**Alternatives Considered:**
- **RabbitMQ**: Simpler but no replay, less durable
- **NATS**: Lighter but lacks durability
- **AWS Kinesis**: Vendor lock-in, less flexible

---

## ADR-006: FastAPI for Python Services

**Date:** 2026-01-25  
**Status:** Accepted

### Context
We need a modern, async-capable web framework for Python services with excellent developer experience and automatic API documentation.

### Decision
Use FastAPI as the primary framework for all Python-based services.

### Consequences

**Positive:**
- Native async support
- Automatic OpenAPI documentation
- Pydantic integration for validation
- High performance (similar to Node/Go)
- Type hints with mypy support

**Negative:**
- Less mature than Django for complex apps
- Smaller ecosystem (no built-in admin panel)
- Async subtleties can be confusing

**Alternatives Considered:**
- **Django + Django Ninja**: More features but heavier
- **Starlette**: More minimal, less tooling
- **Flask**: Synchronous, less modern

---

## ADR-007: Next.js for Frontend

**Date:** 2026-01-28  
**Status:** Accepted

### Context
We need a modern React framework with excellent developer experience, SSR/SSG capabilities, and strong ecosystem.

### Decision
Use Next.js 14 with:
- App Router for routing
- Server Components where appropriate
- Vercel for deployment (or self-hosted)

### Consequences

**Positive:**
- Excellent developer experience
- Server-side rendering for SEO
- Strong TypeScript support
- Large ecosystem
- Vercel integration

**Negative:**
- Vendor lock-in risk with Vercel
- Can be complex for simple apps
- RSC mental model shift

**Alternatives Considered:**
- **Remix**: Good but smaller ecosystem
- **Astro**: Better for content-heavy, but less dynamic
- **SvelteKit**: Emerging, smaller community

---

## ADR-008: vLLM for LLM Serving

**Date:** 2026-02-01  
**Status:** Accepted

### Context
We need to serve open-source LLMs (Llama, Mistral) with high throughput and low latency for curriculum generation and other AI features.

### Decision
Use vLLM with:
- PagedAttention for memory efficiency
- Continuous batching for throughput
- Tensor parallelism for large models
- OpenAI-compatible API

### Consequences

**Positive:**
- Industry-leading throughput (up to 24x vs HuggingFace)
- Efficient memory management
- Continuous batching
- OpenAI-compatible API
- Active development

**Negative:**
- GPU memory requirements
- Only supports transformers models
- More complex than simple API calls

**Alternatives Considered:**
- **Text Generation Inference (TGI)**: Good alternative, similar performance
- **Ray Serve**: More flexible but more complex
- **Managed services (Anthropic, OpenAI)**: Higher cost, less control

---

## ADR-009: BGE Embeddings Model

**Date:** 2026-02-05  
**Status:** Accepted

### Context
We need high-quality text embeddings for semantic search and RAG applications.

### Decision
Use BAAI/bge-large-en-v1.5 (1024 dimensions) for embeddings with:
- Quantization for storage efficiency
- Batch processing for throughput

### Consequences

**Positive:**
- Excellent performance on MTEB benchmark
- 1024 dimensions for better semantic capture
- Open-source and self-hostable
- Good multilingual support

**Negative:**
- Large model (1.3GB)
- 1024 dimensions increase storage
- Requires GPU for fast inference

**Alternatives Considered:**
- **OpenAI text-embedding-3**: Better quality but paid, external API
- **Cohere**: Good but external dependency
- **e5-mistral**: Smaller but slightly lower quality

---

## ADR-010: Kubernetes for Container Orchestration

**Date:** 2026-02-10  
**Status:** Accepted

### Context
We need to orchestrate containers across multiple environments with auto-scaling, rolling deployments, and service discovery.

### Decision
Use Kubernetes (EKS for AWS, GKE for GCP) with:
- Helm for package management
- ArgoCD for GitOps
- Istio for service mesh

### Consequences

**Positive:**
- Industry standard
- Excellent auto-scaling
- Strong ecosystem
- GitOps support
- Multi-cloud capability

**Negative:**
- Operational complexity
- Steep learning curve
- Resource overhead

**Alternatives Considered:**
- **ECS/Fargate**: Simpler but less flexible
- **Docker Swarm**: Simpler but less feature-rich
- **Serverless**: Cost unpredictable at scale

---

## ADR-011: Redis for Caching and Sessions

**Date:** 2026-02-12  
**Status:** Accepted

### Context
We need a fast, in-memory data store for:
- API response caching
- Session management
- Rate limiting
- Pub/sub messaging

### Decision
Use Redis 7.2 with Redis Stack features:
- RedisJSON for document storage
- RediSearch for simple full-text search
- RedisGears for serverless functions

### Consequences

**Positive:**
- Excellent performance
- Rich data structures
- Pub/sub support
- Good persistence options
- Cluster mode for scaling

**Negative:**
- Single-threaded (can be bottleneck)
- Memory management critical
- Data loss risk if not persisted

**Alternatives Considered:**
- **Memcached**: Simpler but less features
- **DragonflyDB**: Better performance but newer
- **KeyDB**: Multi-threaded but less mature

---

## ADR-012: Kubernetes Secrets with HashiCorp Vault

**Date:** 2026-02-15  
**Status:** Accepted

### Context
We need secure storage and management of:
- Database credentials
- API keys
- JWT secrets
- External service tokens

### Decision
Use HashiCorp Vault for:
- Dynamic secrets
- Secret rotation
- Encryption as a service
- Audit logging

### Consequences

**Positive:**
- Industry standard for secrets
- Dynamic credentials
- Automatic rotation
- Fine-grained access control

**Negative:**
- Additional operational overhead
- Complex setup and maintenance
- Single point of failure if not HA

**Alternatives Considered:**
- **AWS Secrets Manager**: Vendor lock-in
- **Kubernetes Secrets**: Basic, no rotation
- **External secrets operator**: More complex

---

## ADR-013: JWT for Authentication

**Date:** 2026-02-18  
**Status:** Accepted

### Context
We need stateless authentication for API access with support for:
- User login
- Service-to-service auth
- Token refresh
- MFA

### Decision
Use JWT with:
- RS256 for asymmetric signing
- Short-lived access tokens (15 min)
- Rotating refresh tokens (7 days)
- Token blacklisting for logout

### Consequences

**Positive:**
- Stateless authentication
- Scalable
- Standard-based
- Supports claims for authorization

**Negative:**
- Token size
- No way to revoke access tokens immediately
- Requires secure key management

**Alternigation:**
- Keep access token lifetime short
- Use token rotation
- Implement blacklist for critical operations

**Alternatives Considered:**
- **Sessions**: Stateful, harder to scale
- **Opaque tokens**: Requires validation endpoint
- **OAuth2 with PASETO**: Newer, less mature

---

## ADR-014: Terraform for Infrastructure as Code

**Date:** 2026-02-20  
**Status:** Accepted

### Context
We need reproducible, version-controlled infrastructure across multiple environments and cloud providers.

### Decision
Use Terraform with:
- Terragrunt for environment management
- Remote state with S3/DynamoDB
- Module-based architecture

### Consequences

**Positive:**
- Cloud-agnostic
- Large ecosystem
- State management
- Plan before apply

**Negative:**
- State management complexity
- Drift detection challenges
- Learning curve

**Alternatives Considered:**
- **Pulumi**: More programmable but less declarative
- **CloudFormation**: AWS-only
- **Ansible**: More procedural, less state-aware

---

## ADR-015: GitOps with ArgoCD

**Date:** 2026-02-22  
**Status:** Accepted

### Context
We need declarative, Git-driven deployments for Kubernetes with:
- Automated sync
- Rollback capabilities
- Multi-environment support

### Decision
Use ArgoCD with:
- Application of Applications pattern
- Image updater for GitOps-native deployments
- Progressive delivery with Argo Rollouts

### Consequences

**Positive:**
- Git as single source of truth
- Automated deployments
- Easy rollback
- Visual UI

**Negative:**
- Additional component to maintain
- Git repository strategy complexity
- Secrets management challenges

**Alternatives Considered:**
- **Flux**: Similar but simpler
- **Jenkins X**: More complex
- **Spinnaker**: Enterprise-focused

---

## ADR-016: RAG Pipeline with LangChain + LlamaIndex

**Date:** 2026-02-25  
**Status:** Accepted

### Context
We need a RAG pipeline for:
- Content ingestion and chunking
- Embedding generation
- Vector storage
- Query processing
- Response generation

### Decision
Use hybrid approach:
- Custom chunking logic for educational content
- LangChain for orchestration
- LlamaIndex for advanced indexing
- Custom reranking pipeline

### Consequences

**Positive:**
- Best-in-class frameworks
- Large community
- Flexible architecture
- Good debugging tools

**Negative:**
- Framework overhead
- Version compatibility issues
- Can be complex

**Alternatives Considered:**
- **LlamaIndex only**: Better for complex data
- **LangChain only**: Better for agents
- **Custom implementation**: More work, less features

---

## ADR-017: Event-Driven Architecture for ML Pipeline

**Date:** 2026-03-01  
**Status:** Accepted

### Context
We need to process content for ML features (embeddings, knowledge graph) asynchronously with:
- Automatic retry
- Ordered processing
- Backpressure handling

### Decision
Use Kafka with:
- Separate topics per processing stage
- Consumer groups for parallel processing
- Dead letter queues for failures

### Consequences

**Positive:**
- Decoupled processing
- Scalable
- Replay capability
- Natural backpressure

**Negative:**
- Complexity
- Latency
- Requires careful design

**Alternatives Considered:**
- **Celery + Redis**: Simpler but less durable
- **AWS SQS**: Simpler but vendor lock-in
- **Custom queue**: Too much work

---

## ADR-018: Multi-Armed Bandit for Recommendations

**Date:** 2026-03-05  
**Status:** Accepted

### Context
We need to balance exploration and exploitation in recommendations while:
- Learning from user behavior
- Adapting to preferences
- Maintaining diversity

### Decision
Implement Thompson Sampling with:
- Contextual features for personalization
- Epsilon-greedy for baseline
- UCB for comparison

### Consequences

**Positive:**
- Handles exploration-exploitation trade-off
- Adapts to user preferences
- Well-studied

**Negative:**
- Requires careful tuning
- Initial cold-start challenges
- More complex than A/B testing

**Alternatives Considered:**
- **A/B testing**: Simpler but slower to learn
- **Contextual bandits**: More complex
- **Collaborative filtering**: Less adaptive

---

## ADR-019: Elasticsearch for Full-Text Search

**Date:** 2026-03-08  
**Status:** Accepted

### Context
We need advanced full-text search with:
- Faceted filtering
- Relevance tuning
- Aggregations
- Typo tolerance

### Decision
Use Elasticsearch 8.x with:
- Custom analyzers for educational content
- Learning-to-Rank for relevance
- Cross-cluster search for scale

### Consequences

**Positive:**
- Industry-standard search
- Rich feature set
- Good performance
- Strong ecosystem

**Negative:**
- Resource-intensive
- Complex clustering
- Version upgrades tricky

**Alternatives Considered:**
- **OpenSearch**: Apache fork, similar
- **Meilisearch**: Simpler but less features
- **Typesense**: Easier but less scalable

---

## ADR-020: Browser-Based Video with HLS

**Date:** 2026-03-10  
**Status:** Accepted

### Context
We need to deliver video content with:
- Adaptive bitrate streaming
- Offline capability
- Chapter markers
- Progress tracking

### Decision
Use HLS (HTTP Live Streaming) with:
- Video.js for player
- HLS.js for browser support
- Custom chapters and subtitles

### Consequences

**Positive:**
- Adaptive streaming
- Wide browser support
- Standard format
- Good CDN integration

**Negative:**
- More complex than MP4
- Encoding required
- Player complexity

**Alternatives Considered:**
- **DASH**: Similar, slightly less support
- **HLS.js only**: Less features than Video.js
- **YouTube embed**: Less control, ads

---

## ADR-021: WebAssembly for Interactive Content

**Date:** 2026-03-12  
**Status:** Proposed

### Context
We need to support interactive educational content (simulations, code execution) securely in the browser.

### Decision
Use WebAssembly (WASM) with:
- Code execution sandboxing
- Simulation frameworks
- Collaborative features via CRDTs

### Consequences

**Positive:**
- Near-native performance
- Secure sandboxing
- Language-agnostic

**Negative:**
- Larger bundle sizes
- Debugging complexity
- Mobile support varies

**Alternatives Considered:**
- **Server-side execution**: More secure but higher latency
- **Iframes with CSP**: Simpler but less capable
- **Native apps**: Better UX but less accessible

---

## ADR-022: CDN Strategy with CloudFlare

**Date:** 2026-03-15  
**Status:** Accepted

### Context
We need global content delivery with:
- Edge caching
- DDoS protection
- Edge computing for personalization
- Image optimization

### Decision
Use CloudFlare with:
- CDN for static assets
- Workers for edge functions
- Images for optimization
- R2 for static storage (optional)

### Consequences

**Positive:**
- Excellent global network
- Generous free tier
- Edge computing
- Security features

**Negative:**
- Vendor lock-in risk
- Can be opaque
- Pricing can spike

**Alternatives Considered:**
- **AWS CloudFront**: Better AWS integration
- **Fastly**: More control, higher cost
- **Vercel Edge**: Good for Next.js

---

## ADR-023: Observability Stack

**Date:** 2026-03-18  
**Status:** Accepted

### Context
We need comprehensive observability:
- Metrics for performance
- Logs for debugging
- Traces for distributed systems
- Alerts for incidents

### Decision
Use OpenTelemetry with:
- Prometheus for metrics
- Grafana for visualization
- Loki for logs
- Jaeger for traces
- Alertmanager for alerts

### Consequences

**Positive:**
- Vendor-neutral
- Standard instrumentation
- Excellent tools
- Open-source

**Negative:**
- Many moving parts
- Configuration complexity
- Storage costs at scale

**Alternatives Considered:**
- **Datadog**: Easier but expensive
- **New Relic**: Similar to Datadog
- **AWS CloudWatch**: Vendor lock-in

---

## ADR-024: Database Sharding Strategy

**Date:** 2026-03-20  
**Status:** Proposed

### Context
As we scale, PostgreSQL may need sharding for:
- User data (by user_id)
- Content (by content_hash)
- Interactions (by time)

### Decision
Evaluate Vitess/PostgreSQL sharding at 100M+ users.

### Consequences

**Positive:**
- Horizontal scaling
- Geographic distribution
- Fault isolation

**Negative:**
- Complexity
- Cross-shard queries
- Rebalancing challenges

**Alternatives Considered:**
- **Citus**: Simpler, managed option
- **PlanetScale**: Serverless MySQL
- **Aurora**: Managed but horizontal reads only

---

*Document Version: 1.0.0*  
*Architecture Review Board: Active*
