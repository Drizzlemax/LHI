# PANDORA Agent Task Definitions

**Version:** 1.0.0  
**Purpose:** Break down each service into agent-executable tasks  
**Usage:** Copy tasks into agent prompts or task queues

---

## Table of Contents

1. [User Service Tasks](#1-user-service-tasks)
2. [Content Service Tasks](#2-content-service-tasks)
3. [Search Service Tasks](#3-search-service-tasks)
4. [Learning Service Tasks](#4-learning-service-tasks)
5. [Quiz Service Tasks](#5-quiz-service-tasks)
6. [Recommendation Service Tasks](#6-recommendation-service-tasks)
7. [AI Gateway Tasks](#7-ai-gateway-tasks)
8. [Crawler Service Tasks](#8-crawler-service-tasks)
9. [Shared Library Tasks](#9-shared-library-tasks)
10. [Frontend Tasks](#10-frontend-tasks)
11. [Infrastructure Tasks](#11-infrastructure-tasks)

---

## 1. User Service Tasks

**Service Path:** `services/user-service/`  
**API Spec:** See `api-spec.yaml` - Auth and Users sections  
**Dependencies:** PostgreSQL, Redis

### Task U-1: Project Setup
```
TASK: Initialize User Service Project Structure

INPUT:
- Language: Python 3.12
- Framework: FastAPI
- ORM: SQLAlchemy 2.0
- Reference: DEVELOPMENT_GUIDE.md

ACTIONS:
1. Create directory structure:
   - src/api/routes/
   - src/core/config.py
   - src/core/security.py
   - src/models/
   - src/schemas/
   - src/services/
   - src/repositories/
   - tests/unit/
   - tests/integration/

2. Create pyproject.toml with dependencies:
   - fastapi>=0.109.0
   - uvicorn[standard]>=0.27.0
   - sqlalchemy[asyncio]>=2.0.25
   - pydantic>=2.5.0
   - python-jose[cryptography]>=3.3.0
   - passlib[bcrypt]>=1.7.4
   - python-multipart>=0.0.6
   - httpx>=0.26.0
   - pytest>=7.4.0
   - pytest-asyncio>=0.21.0

3. Create Dockerfile based on DEVELOPMENT_GUIDE.md template

4. Create src/__init__.py, src/api/__init__.py, etc.

OUTPUT:
- Complete project structure
- pyproject.toml
- Dockerfile
- .env.example
```

### Task U-2: Database Models
```
TASK: Implement User Database Models

INPUT:
- ERD from PANDORA_ARCHITECTURE.md Section 3
- SQLAlchemy 2.0 patterns

ACTIONS:
1. Create src/models/base.py:
   - Base class with UUID primary key
   - Timestamps (created_at, updated_at)
   - Soft delete support

2. Create src/models/user.py:
   - User model matching UserProfile schema
   - Fields: id, email, password_hash, full_name, role, avatar_url, is_verified, mfa_enabled
   - Relationships to Institution, LearningProfile

3. Create src/models/institution.py:
   - Institution model
   - Fields: id, name, domain, tier, settings

4. Create src/models/learning_profile.py:
   - LearningProfile model
   - Fields: id, user_id, education_level, knowledge_state (JSONB), learning_style, preferences

5. Create src/models/session.py:
   - Session model for JWT tracking
   - Fields: id, user_id, token_hash, expires_at, is_revoked

6. Create Alembic migration files

OUTPUT:
- Complete SQLAlchemy models
- Alembic migrations
```

### Task U-3: Authentication Endpoints
```
TASK: Implement Authentication Endpoints

INPUT:
- API spec: /auth/* endpoints in api-spec.yaml
- Security: JWT RS256, refresh token rotation

ACTIONS:
1. Create src/core/config.py:
   - Settings from environment variables
   - JWT configuration
   - Database URLs

2. Create src/core/security.py:
   - Password hashing (bcrypt)
   - JWT token creation/validation
   - Token refresh logic
   - MFA verification

3. Create src/api/routes/auth.py:
   - POST /auth/register
   - POST /auth/login
   - POST /auth/refresh
   - POST /auth/logout
   - POST /auth/mfa/setup
   - POST /auth/mfa/verify

4. Create src/schemas/auth.py:
   - RegisterRequest, LoginRequest
   - AuthResponse, TokenPayload
   - MFASetupResponse

5. Implement Redis session storage

OUTPUT:
- Working authentication endpoints
- Token generation and validation
- Session management
```

### Task U-4: User Management Endpoints
```
TASK: Implement User Management Endpoints

INPUT:
- API spec: /users/* endpoints in api-spec.yaml

ACTIONS:
1. Create src/api/routes/users.py:
   - GET /users/me
   - PATCH /users/me
   - GET /users/me/learning-profile
   - PUT /users/me/learning-profile
   - GET /users/me/preferences
   - PATCH /users/me/preferences

2. Create src/schemas/user.py:
   - UserProfile, UserProfileUpdate
   - LearningProfile, LearningProfileUpdate
   - UserPreferences, UserPreferencesUpdate

3. Create src/services/user_service.py:
   - get_current_user()
   - update_user()
   - get_learning_profile()
   - update_learning_profile()

4. Create src/repositories/user_repository.py:
   - Async SQLAlchemy queries
   - User CRUD operations

OUTPUT:
- Complete user management API
- Learning profile updates
```

### Task U-5: Write Unit Tests
```
TASK: Write Unit Tests for User Service

INPUT:
- Service implementation from Tasks U-1 to U-4
- Testing patterns from DEVELOPMENT_GUIDE.md

ACTIONS:
1. Create tests/unit/conftest.py:
   - Fixtures for AsyncClient
   - Mock database sessions
   - Test user data factories

2. Create tests/unit/test_auth.py:
   - Test registration flow
   - Test login/logout
   - Test token refresh
   - Test MFA setup

3. Create tests/unit/test_users.py:
   - Test user profile retrieval
   - Test profile updates
   - Test learning profile management

4. Create tests/unit/test_security.py:
   - Password hashing tests
   - JWT validation tests

5. Achieve 80%+ code coverage

OUTPUT:
- Complete test suite
- Coverage report
```

---

## 2. Content Service Tasks

**Service Path:** `services/content-service/`  
**API Spec:** See `api-spec.yaml` - Content section  
**Dependencies:** PostgreSQL, S3/MinIO

### Task C-1: Project Setup
```
TASK: Initialize Content Service Project Structure

ACTIONS:
1. Create directory structure:
   - src/api/routes/
   - src/core/config.py
   - src/models/
   - src/schemas/
   - src/services/
   - src/repositories/
   - src/storage/ (S3 integration)
   - tests/

2. Create pyproject.toml with dependencies:
   - fastapi>=0.109.0
   - sqlalchemy[asyncio]>=2.0.25
   - boto3>=1.34.0
   - python-multipart>=0.0.6
   - aiofiles>=23.0.0
   - pydantic>=2.5.0

OUTPUT:
- Complete project structure
```

### Task C-2: Content Models
```
TASK: Implement Content Database Models

INPUT:
- ERD from PANDORA_ARCHITECTURE.md Section 3

ACTIONS:
1. Create src/models/content.py:
   - Content model (book, article, video, course, lesson, quiz, interactive, document)
   - Fields: id, title, description, content_type, education_level, language, metadata
   - Relationships to ContentMetadata, ContentVector

2. Create src/models/content_metadata.py:
   - ContentMetadata model
   - Fields: content_id, authors, publication_date, license, source_url, ratings

3. Create src/models/media_asset.py:
   - MediaAsset model
   - Fields: id, content_id, asset_type, url, size, mime_type

4. Create Alembic migrations

OUTPUT:
- Complete content models
```

### Task C-3: Content CRUD Endpoints
```
TASK: Implement Content CRUD Endpoints

INPUT:
- API spec: /content/* endpoints in api-spec.yaml

ACTIONS:
1. Create src/api/routes/content.py:
   - GET /content (list with pagination)
   - GET /content/{content_id}
   - GET /content/{content_id}/related
   - POST /content (create)
   - PUT /content/{content_id}
   - DELETE /content/{content_id}

2. Create src/schemas/content.py:
   - ContentSummary, ContentDetail
   - ContentCreate, ContentUpdate
   - ContentListResponse

3. Create src/services/content_service.py:
   - get_content_list()
   - get_content_detail()
   - get_related_content()
   - create_content()
   - update_content()

4. Create src/storage/s3_client.py:
   - Upload/download media files
   - Presigned URLs
   - File type validation

OUTPUT:
- Working content API
- S3 integration
```

### Task C-4: Write Unit Tests
```
TASK: Write Unit Tests for Content Service

ACTIONS:
1. Create tests/unit/conftest.py with content fixtures
2. Create tests/unit/test_content.py
3. Create tests/unit/test_storage.py
4. Achieve 80%+ coverage

OUTPUT:
- Complete test suite
```

---

## 3. Search Service Tasks

**Service Path:** `services/search-service/`  
**API Spec:** See `api-spec.yaml` - Search section  
**Dependencies:** Elasticsearch, Qdrant, PostgreSQL

### Task S-1: Project Setup
```
TASK: Initialize Search Service Project Structure

ACTIONS:
1. Create directory structure:
   - src/api/routes/
   - src/core/config.py
   - src/search/ (ES client)
   - src/vector/ (Qdrant client)
   - src/services/
   - tests/

2. Create pyproject.toml with dependencies:
   - fastapi>=0.109.0
   - elasticsearch[async]>=8.11.0
   - qdrant-client>=1.7.0
   - httpx>=0.26.0

OUTPUT:
- Complete project structure
```

### Task S-2: Elasticsearch Integration
```
TASK: Implement Elasticsearch Search

INPUT:
- Elasticsearch 8.x configuration

ACTIONS:
1. Create src/search/client.py:
   - Async Elasticsearch client
   - Connection pooling
   - Index management

2. Create src/search/indexer.py:
   - Index creation with mappings
   - Bulk indexing
   - Mapping for content fields:
     * title (text with autocomplete)
     * description (text)
     * tags (keyword array)
     * education_level (keyword)
     * content_type (keyword)
     * created_at (date)

3. Create src/search/query_builder.py:
   - Full-text search
   - Filters (education_level, content_type, language)
   - Aggregations
   - Highlighting

4. Create src/search/reranker.py:
   - RRF (Reciprocal Rank Fusion)
   - Hybrid score combination

OUTPUT:
- Working Elasticsearch integration
```

### Task S-3: Vector Search Integration
```
TASK: Implement Vector Search with Qdrant

INPUT:
- Qdrant configuration from PANDORA_ARCHITECTURE.md

ACTIONS:
1. Create src/vector/client.py:
   - Async Qdrant client
   - Collection management
   - Connection pooling

2. Create src/vector/indexer.py:
   - Collection creation with HNSW config
   - Batch upsert
   - Payload management

3. Create src/vector/searcher.py:
   - Vector similarity search
   - Filtered search
   - Result pagination

OUTPUT:
- Working vector search
```

### Task S-4: Search Endpoints
```
TASK: Implement Search Endpoints

INPUT:
- API spec: /search/* endpoints in api-spec.yaml

ACTIONS:
1. Create src/api/routes/search.py:
   - GET /search (hybrid search)
   - GET /search/suggest (autocomplete)

2. Create src/services/search_service.py:
   - hybrid_search() - combine ES + Qdrant
   - get_suggestions() - autocomplete

3. Create src/services/indexing_service.py:
   - index_content()
   - delete_from_index()
   - bulk_reindex()

OUTPUT:
- Working search API
```

### Task S-5: Write Unit Tests
```
TASK: Write Unit Tests for Search Service

ACTIONS:
1. Create tests/unit/conftest.py with search fixtures
2. Create tests/unit/test_search.py
3. Create tests/unit/test_vector_search.py
4. Achieve 80%+ coverage

OUTPUT:
- Complete test suite
```

---

## 4. Learning Service Tasks

**Service Path:** `services/learning-service/`  
**API Spec:** See `api-spec.yaml` - Learning Paths, Progress sections  
**Dependencies:** PostgreSQL, Redis, Knowledge Graph (Neo4j)

### Task L-1: Project Setup
```
TASK: Initialize Learning Service Project Structure

ACTIONS:
1. Create directory structure:
   - src/api/routes/
   - src/core/config.py
   - src/models/
   - src/schemas/
   - src/services/
   - src/graph/ (Neo4j client)
   - tests/

2. Create pyproject.toml with dependencies:
   - fastapi>=0.109.0
   - sqlalchemy[asyncio]>=2.0.25
   - neo4j>=5.14.0
   - redis>=5.0.0

OUTPUT:
- Complete project structure
```

### Task L-2: Learning Path Models
```
TASK: Implement Learning Path Database Models

INPUT:
- ERD from PANDORA_ARCHITECTURE.md Section 3

ACTIONS:
1. Create src/models/learning_path.py:
   - LearningPath model
   - Fields: id, user_id, course_id, title, description, goal, status, progress_percentage

2. Create src/models/module.py:
   - Module model
   - Fields: id, learning_path_id, title, description, order_index, estimated_hours

3. Create src/models/path_lesson.py:
   - PathLesson model
   - Fields: id, module_id, content_id, title, order_index, status, estimated_minutes

4. Create src/models/progress.py:
   - UserProgress model
   - Fields: id, user_id, lesson_id, status, quiz_results, time_spent_seconds

5. Create Alembic migrations

OUTPUT:
- Complete learning path models
```

### Task L-3: Learning Path Endpoints
```
TASK: Implement Learning Path Endpoints

INPUT:
- API spec: /learning-paths/*, /learning-paths/{id}/progress endpoints

ACTIONS:
1. Create src/api/routes/learning_paths.py:
   - GET /learning-paths (list user's paths)
   - POST /learning-paths (create path)
   - GET /learning-paths/{path_id}
   - PATCH /learning-paths/{path_id}
   - DELETE /learning-paths/{path_id}

2. Create src/api/routes/progress.py:
   - GET /learning-paths/{path_id}/progress
   - PATCH /learning-paths/{path_id}/progress

3. Create src/schemas/learning_path.py:
   - CreateLearningPathRequest
   - LearningPathSummary, LearningPathDetail
   - PathModule, PathLesson

4. Create src/services/learning_path_service.py:
   - create_learning_path()
   - get_learning_path()
   - update_learning_path()
   - get_path_progress()
   - update_progress()

OUTPUT:
- Working learning path API
```

### Task L-4: Progress Tracking
```
TASK: Implement Progress Tracking

INPUT:
- Analytics requirements from PANDORA_ARCHITECTURE.md

ACTIONS:
1. Create src/services/progress_service.py:
   - track_lesson_progress()
   - calculate_module_progress()
   - calculate_path_progress()
   - update_streak()

2. Create src/services/analytics_service.py:
   - get_progress_analytics()
   - get_strengths_weaknesses()

3. Create src/graph/neo4j_client.py:
   - Connect to Neo4j
   - Query concept relationships

4. Create src/graph/prerequisite_checker.py:
   - check_prerequisites()
   - suggest_next_lesson()

OUTPUT:
- Progress tracking logic
- Knowledge graph integration
```

### Task L-5: Write Unit Tests
```
TASK: Write Unit Tests for Learning Service

ACTIONS:
1. Create tests/unit/conftest.py
2. Create tests/unit/test_learning_paths.py
3. Create tests/unit/test_progress.py
4. Create tests/unit/test_analytics.py
5. Achieve 80%+ coverage

OUTPUT:
- Complete test suite
```

---

## 5. Quiz Service Tasks

**Service Path:** `services/quiz-service/`  
**API Spec:** See `api-spec.yaml` - Assessments section  
**Dependencies:** PostgreSQL, Redis

### Task Q-1: Project Setup
```
TASK: Initialize Quiz Service Project Structure

ACTIONS:
1. Create directory structure:
   - src/api/routes/
   - src/core/config.py
   - src/models/
   - src/schemas/
   - src/services/
   - src/irt/ (Item Response Theory)
   - tests/

2. Create pyproject.toml with dependencies:
   - fastapi>=0.109.0
   - sqlalchemy[asyncio]>=2.0.25
   - redis>=5.0.0

OUTPUT:
- Complete project structure
```

### Task Q-2: Assessment Models
```
TASK: Implement Assessment Database Models

INPUT:
- Quiz requirements from PANDORA_ARCHITECTURE.md Section 12

ACTIONS:
1. Create src/models/assessment.py:
   - Assessment model
   - Fields: id, content_id, title, description, question_count, time_limit_minutes

2. Create src/models/question.py:
   - Question model
   - Fields: id, assessment_id, question_text, question_type, options (JSONB), points

3. Create src/models/attempt.py:
   - AssessmentAttempt model
   - Fields: id, assessment_id, user_id, started_at, completed_at, score

4. Create src/models/answer.py:
   - Answer model
   - Fields: id, attempt_id, question_id, answer, is_correct, points_earned

5. Create Alembic migrations

OUTPUT:
- Complete assessment models
```

### Task Q-3: Quiz Endpoints
```
TASK: Implement Quiz Endpoints

INPUT:
- API spec: /assessments/* endpoints in api-spec.yaml

ACTIONS:
1. Create src/api/routes/assessments.py:
   - GET /assessments/{assessment_id}
   - POST /assessments/{assessment_id}/start
   - POST /assessments/{assessment_id}/submit

2. Create src/schemas/assessment.py:
   - Assessment
   - AssessmentAttempt
   - AssessmentQuestion
   - AssessmentSubmission
   - AssessmentResult

3. Create src/services/quiz_service.py:
   - get_assessment()
   - start_attempt()
   - submit_attempt()
   - grade_submission()

OUTPUT:
- Working quiz API
```

### Task Q-4: Adaptive Testing
```
TASK: Implement Computer Adaptive Testing

INPUT:
- IRT requirements from PANDORA_ARCHITECTURE.md Section 12.2

ACTIONS:
1. Create src/irt/ability_estimator.py:
   - Maximum Likelihood Estimation
   - Newton-Raphson updates
   - Standard error calculation

2. Create src/irt/item_selector.py:
   - Maximum Fisher Information
   - Item selection algorithm

3. Create src/services/adaptive_service.py:
   - select_next_question()
   - update_ability_estimate()
   - check_termination()

OUTPUT:
- Adaptive testing logic
```

### Task Q-5: Write Unit Tests
```
TASK: Write Unit Tests for Quiz Service

ACTIONS:
1. Create tests/unit/test_assessments.py
2. Create tests/unit/test_adaptive.py
3. Create tests/unit/test_grading.py
4. Achieve 80%+ coverage

OUTPUT:
- Complete test suite
```

---

## 6. Recommendation Service Tasks

**Service Path:** `services/recommendation-service/`  
**API Spec:** See `api-spec.yaml` - Recommendations section  
**Dependencies:** PostgreSQL, Qdrant, Redis

### Task R-1: Project Setup
```
TASK: Initialize Recommendation Service Project Structure

ACTIONS:
1. Create directory structure:
   - src/api/routes/
   - src/core/config.py
   - src/services/
   - src/algorithms/ (bandits, collaborative, content-based)
   - src/features/ (feature extraction)
   - tests/

2. Create pyproject.toml with dependencies:
   - fastapi>=0.109.0
   - qdrant-client>=1.7.0
   - numpy>=1.26.0
   - scipy>=1.11.0

OUTPUT:
- Complete project structure
```

### Task R-2: Recommendation Endpoints
```
TASK: Implement Recommendation Endpoints

INPUT:
- API spec: /recommendations/* endpoints in api-spec.yaml

ACTIONS:
1. Create src/api/routes/recommendations.py:
   - GET /recommendations
   - POST /recommendations/explain

2. Create src/schemas/recommendation.py:
   - Recommendation
   - RecommendationListResponse
   - RecommendationExplanation

3. Create src/services/recommendation_service.py:
   - get_recommendations()
   - explain_recommendation()

OUTPUT:
- Working recommendation API
```

### Task R-3: Multi-Armed Bandit Implementation
```
TASK: Implement Multi-Armed Bandit for Recommendations

INPUT:
- MAB requirements from PANDORA_ARCHITECTURE.md Section 10

ACTIONS:
1. Create src/algorithms/epsilon_greedy.py:
   - EpsilonGreedy class
   - Explore/exploit balance
   - Reward tracking

2. Create src/algorithms/thompson_sampling.py:
   - ThompsonSampling class
   - Beta distribution sampling
   - Posterior updates

3. Create src/algorithms/ucb.py:
   - UCBStrategy class
   - Confidence bounds

OUTPUT:
- Working MAB algorithms
```

### Task R-4: Candidate Generation
```
TASK: Implement Candidate Generation Strategies

INPUT:
- Recommendation strategies from PANDORA_ARCHITECTURE.md Section 10.2

ACTIONS:
1. Create src/algorithms/content_based.py:
   - ContentBasedFilter class
   - TF-IDF similarity
   - Embedding similarity

2. Create src/algorithms/collaborative.py:
   - CollaborativeFilter class
   - User-user similarity
   - Item-item similarity

3. Create src/algorithms/knowledge_graph.py:
   - KnowledgeGraphRecommender class
   - Prerequisite-based recommendations

4. Create src/algorithms/diversity.py:
   - MMR (Maximal Marginal Relevance)
   - Category balancing

OUTPUT:
- Candidate generation strategies
```

### Task R-5: Write Unit Tests
```
TASK: Write Unit Tests for Recommendation Service

ACTIONS:
1. Create tests/unit/test_bandits.py
2. Create tests/unit/test_candidates.py
3. Create tests/unit/test_diversity.py
4. Achieve 80%+ coverage

OUTPUT:
- Complete test suite
```

---

## 7. AI Gateway Tasks

**Service Path:** `services/ai-gateway/`  
**API Spec:** See `api-spec.yaml` - AI section  
**Dependencies:** vLLM, Qdrant, PostgreSQL

### Task A-1: Project Setup
```
TASK: Initialize AI Gateway Project Structure

ACTIONS:
1. Create directory structure:
   - src/api/routes/
   - src/core/config.py
   - src/llm/ (vLLM client)
   - src/prompts/ (prompt templates)
   - src/services/
   - tests/

2. Create pyproject.toml with dependencies:
   - fastapi>=0.109.0
   - httpx>=0.26.0
   - langchain>=0.1.0
   - llama-index>=0.9.0
   - qdrant-client>=1.7.0

OUTPUT:
- Complete project structure
```

### Task A-2: LLM Client
```
TASK: Implement LLM Gateway Client

INPUT:
- vLLM configuration from PANDORA_ARCHITECTURE.md Section 7

ACTIONS:
1. Create src/llm/client.py:
   - Async HTTP client for vLLM
   - OpenAI-compatible API
   - Streaming support
   - Token counting

2. Create src/llm/router.py:
   - Model selection logic
   - Fallback handling
   - Cost optimization

3. Create src/llm/cache.py:
   - Semantic caching with Redis
   - Cache invalidation

OUTPUT:
- Working LLM client
```

### Task A-3: Prompt Templates
```
TASK: Implement Prompt Templates

INPUT:
- Prompt requirements from PANDORA_ARCHITECTURE.md Section 7.3

ACTIONS:
1. Create src/prompts/curriculum_generator.py:
   - System prompt template
   - User prompt template
   - Output schema

2. Create src/prompts/quiz_generator.py:
   - MCQ generation prompt
   - Short answer prompt
   - Essay prompt

3. Create src/prompts/concept_explainer.py:
   - Explanation prompt
   - Learning style variants

4. Create src/prompts/research_assistant.py:
   - Research synthesis prompt
   - Citation formatting

OUTPUT:
- Working prompt templates
```

### Task A-4: AI Endpoints
```
TASK: Implement AI Endpoints

INPUT:
- API spec: /ai/* endpoints in api-spec.yaml

ACTIONS:
1. Create src/api/routes/ai.py:
   - POST /ai/curriculum/generate
   - GET /ai/curriculum/{job_id}
   - POST /ai/explain
   - POST /ai/quiz/generate
   - POST /ai/research
   - POST /ai/summarize

2. Create src/schemas/ai.py:
   - CurriculumGenerationRequest
   - ConceptExplanationRequest
   - QuizGenerationRequest
   - ResearchRequest
   - AsyncJobResponse

3. Create src/services/curriculum_service.py:
   - generate_curriculum()
   - parse_llm_output()

4. Create src/services/explanation_service.py:
   - explain_concept()
   - apply_learning_style()

5. Create src/services/research_service.py:
   - research_query()
   - synthesize_results()

OUTPUT:
- Working AI endpoints
```

### Task A-5: RAG Pipeline
```
TASK: Implement RAG Pipeline

INPUT:
- RAG requirements from PANDORA_ARCHITECTURE.md Section 5

ACTIONS:
1. Create src/services/rag_service.py:
   - retrieve_relevant_chunks()
   - construct_prompt()
   - generate_response()

2. Create src/services/chunking_service.py:
   - Hierarchical chunking
   - Semantic chunking
   - Overlap handling

3. Create src/services/retrieval_service.py:
   - Hybrid search (vector + keyword)
   - Reranking with cross-encoder

OUTPUT:
- Working RAG pipeline
```

### Task A-6: Write Unit Tests
```
TASK: Write Unit Tests for AI Gateway

ACTIONS:
1. Create tests/unit/test_llm_client.py
2. Create tests/unit/test_prompts.py
3. Create tests/unit/test_rag.py
4. Achieve 80%+ coverage

OUTPUT:
- Complete test suite
```

---

## 8. Crawler Service Tasks

**Service Path:** `services/crawler-service/`  
**Dependencies:** PostgreSQL, Kafka, Redis

### Task CR-1: Project Setup
```
TASK: Initialize Crawler Service Project Structure

ACTIONS:
1. Create directory structure:
   - src/extractors/ (content extraction)
   - src/parsers/ (HTML, PDF, etc.)
   - src/validators/ (license, robots.txt)
   - src/pipeline/ (processing pipeline)
   - tests/

2. Create pyproject.toml with dependencies:
   - httpx>=0.26.0
   - beautifulsoup4>=4.12.0
   - playwright>=1.40.0
   - pypdf2>=3.0.0
   - robotexclusionrulesparser>=1.7.0
   - aiokafka>=0.9.0

OUTPUT:
- Complete project structure
```

### Task CR-2: Respectful Crawler
```
TASK: Implement Respectful Crawler

INPUT:
- Crawler requirements from PANDORA_ARCHITECTURE.md Section 6

ACTIONS:
1. Create src/validators/robots_checker.py:
   - Parse robots.txt
   - Check crawl permissions
   - Respect crawl-delay

2. Create src/validators/license_checker.py:
   - Detect license type
   - Validate public domain
   - Flag for review

3. Create src/pipeline/polite_crawler.py:
   - Rate limiting
   - Politeness queue
   - Retry logic

OUTPUT:
- Respectful crawler implementation
```

### Task CR-3: Content Extractors
```
TASK: Implement Content Extractors

INPUT:
- Content extraction from various sources

ACTIONS:
1. Create src/extractors/html_extractor.py:
   - HTML parsing with BeautifulSoup
   - Article extraction
   - Metadata extraction

2. Create src/extractors/pdf_extractor.py:
   - PDF text extraction
   - Metadata extraction
   - Section detection

3. Create src/parsers/content_normalizer.py:
   - Clean HTML
   - Normalize whitespace
   - Extract main content

OUTPUT:
- Content extraction logic
```

### Task CR-4: Indexing Pipeline
```
TASK: Implement Indexing Pipeline

ACTIONS:
1. Create src/pipeline/indexing_pipeline.py:
   - Content validation
   - Chunking
   - Embedding generation
   - Vector DB indexing

2. Create src/pipeline/kafka_producer.py:
   - Produce to Kafka topics
   - Schema serialization

3. Create src/pipeline/kafka_consumer.py:
   - Consume from topics
   - Process in batches

OUTPUT:
- Indexing pipeline
```

### Task CR-5: Write Unit Tests
```
TASK: Write Unit Tests for Crawler Service

ACTIONS:
1. Create tests/unit/test_robots.py
2. Create tests/unit/test_extractors.py
3. Create tests/unit/test_pipeline.py
4. Achieve 80%+ coverage

OUTPUT:
- Complete test suite
```

---

## 9. Shared Library Tasks

**Library Path:** `shared/`  
**Purpose:** Common code used by all services

### Task SH-1: Create Shared Models
```
TASK: Create Shared Pydantic Models

INPUT:
- Common schemas from api-spec.yaml

ACTIONS:
1. Create shared/models/base.py:
   - BaseModel with common config
   - Pagination schemas
   - Error schemas

2. Create shared/models/user.py:
   - UserProfile
   - LearningProfile

3. Create shared/models/content.py:
   - ContentSummary
   - ContentDetail

4. Create shared/models/common.py:
   - Error
   - HealthResponse

OUTPUT:
- Shared model library
```

### Task SH-2: Create Shared Utilities
```
TASK: Create Shared Utilities

ACTIONS:
1. Create shared/utils/logging.py:
   - Structured logging setup
   - Context injection

2. Create shared/utils/tracing.py:
   - OpenTelemetry setup
   - Trace context propagation

3. Create shared/utils/retry.py:
   - Retry decorators
   - Exponential backoff

4. Create shared/utils/datetime.py:
   - Timezone utilities
   - Duration formatting

OUTPUT:
- Shared utility library
```

### Task SH-3: Create Shared Exceptions
```
TASK: Create Shared Exception Classes

ACTIONS:
1. Create shared/exceptions/base.py:
   - PANDORAException
   - Error codes

2. Create shared/exceptions/auth.py:
   - AuthenticationError
   - AuthorizationError

3. Create shared/exceptions/content.py:
   - ContentNotFoundError
   - ContentValidationError

OUTPUT:
- Shared exception library
```

---

## 10. Frontend Tasks

**Service Path:** `web/`  
**Framework:** Next.js 14, TypeScript

### Task F-1: Project Setup
```
TASK: Initialize Frontend Project Structure

ACTIONS:
1. Create Next.js 14 app with App Router
2. Set up TypeScript
3. Configure Tailwind CSS
4. Set up shadcn/ui
5. Configure ESLint and Prettier

OUTPUT:
- Complete Next.js project
```

### Task F-2: Authentication Pages
```
TASK: Implement Authentication Pages

INPUT:
- Auth flow from PANDORA_ARCHITECTURE.md Section 8

ACTIONS:
1. Create app/(auth)/login/page.tsx
2. Create app/(auth)/register/page.tsx
3. Create app/(auth)/forgot-password/page.tsx
4. Implement AuthProvider context
5. Create login/register forms with validation

OUTPUT:
- Working auth pages
```

### Task F-3: Dashboard
```
TASK: Implement Dashboard Page

INPUT:
- Dashboard requirements

ACTIONS:
1. Create app/(app)/dashboard/page.tsx
2. Implement learning path cards
3. Create progress widgets
4. Add recommendation carousel

OUTPUT:
- Working dashboard
```

### Task F-4: Learning Path UI
```
TASK: Implement Learning Path UI

INPUT:
- Learning path views

ACTIONS:
1. Create app/(app)/learning-paths/page.tsx (list)
2. Create app/(app)/learning-paths/[id]/page.tsx (detail)
3. Create learning path card component
4. Create progress bar component
5. Implement path navigation

OUTPUT:
- Learning path pages
```

### Task F-5: Search UI
```
TASK: Implement Search Interface

INPUT:
- Search from api-spec.yaml

ACTIONS:
1. Create app/(app)/search/page.tsx
2. Create search input component
3. Create filter sidebar
4. Create search results list
5. Implement infinite scroll

OUTPUT:
- Working search UI
```

### Task F-6: Quiz Interface
```
TASK: Implement Quiz UI

INPUT:
- Quiz requirements

ACTIONS:
1. Create quiz component
2. Implement question types (MCQ, short answer)
3. Create timer component
4. Add progress indicator
5. Create results view

OUTPUT:
- Working quiz interface
```

### Task F-7: Write Tests
```
TASK: Write Frontend Tests

ACTIONS:
1. Set up Vitest
2. Create tests for auth flow
3. Create tests for dashboard
4. Create tests for search
5. Set up Playwright for E2E

OUTPUT:
- Complete test suite
```

---

## 11. Infrastructure Tasks

**Service Path:** `infrastructure/`  
**IaC:** Terraform, Kubernetes

### Task I-1: Terraform Setup
```
TASK: Set Up Terraform Infrastructure

INPUT:
- Cloud provider: AWS (can be adapted to GCP)

ACTIONS:
1. Create terraform/modules/vpc/
2. Create terraform/modules/eks/
3. Create terraform/modules/rds/
4. Create terraform/modules/redis/
5. Create terraform/environments/production/
6. Create terraform/environments/staging/

OUTPUT:
- Terraform modules
- Environment configurations
```

### Task I-2: Kubernetes Setup
```
TASK: Set Up Kubernetes Configuration

INPUT:
- Kubernetes setup from PANDORA_ARCHITECTURE.md

ACTIONS:
1. Create kubernetes/base/ namespace.yaml
2. Create kubernetes/base/service-account.yaml
3. Create kubernetes/base/configmap.yaml
4. Create kubernetes/overlays/production/
5. Create kubernetes/overlays/staging/
6. Create Helm charts for each service

OUTPUT:
- Kubernetes manifests
- Helm charts
```

### Task I-3: CI/CD Pipeline
```
TASK: Set Up CI/CD Pipeline

INPUT:
- GitHub Actions setup

ACTIONS:
1. Create .github/workflows/ci.yml
2. Create .github/workflows/cd.yml
3. Set up ArgoCD Application resources
4. Create Dockerfile for each service

OUTPUT:
- CI/CD pipeline
```

---

## Agent Task Execution Order

```
Phase 1: Dependencies
├── SH-1: Shared Models (all services depend on this)
├── SH-2: Shared Utilities
├── SH-3: Shared Exceptions
└── I-1: Terraform Setup (infrastructure team)

Phase 2: Core Services (parallel)
├── U-1 to U-5: User Service
├── C-1 to C-4: Content Service
└── I-2: Kubernetes Setup

Phase 3: Data Services (parallel)
├── S-1 to S-5: Search Service
├── L-1 to L-5: Learning Service
└── CR-1 to CR-5: Crawler Service

Phase 4: Feature Services (parallel)
├── Q-1 to Q-5: Quiz Service
├── R-1 to R-5: Recommendation Service
└── A-1 to A-6: AI Gateway

Phase 5: Frontend
└── F-1 to F-7: Frontend

Phase 6: Integration
└── I-3: CI/CD Pipeline
```

---

## Task Metadata Format

Each task should output:

```yaml
task_id: "U-3"
status: "completed"
service: "user-service"
files_created:
  - "src/api/routes/auth.py"
  - "src/core/security.py"
  - "src/schemas/auth.py"
files_modified: []
tests_created:
  - "tests/unit/test_auth.py"
lines_of_code: 850
coverage: 82%
dependencies_met:
  - "U-1"
  - "SH-1"
next_tasks:
  - "U-4"
blocking_tasks: []
```

---

*Last updated: 2026-08-05*
