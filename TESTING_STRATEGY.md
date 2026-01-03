# Testing Strategy for Teduco-AI

**Version:** 1.0  
**Last Updated:** December 27, 2025  
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Scope & Levels](#testing-scope--levels)
3. [Testing Tools & Frameworks](#testing-tools--frameworks)
4. [Test Coverage Goals](#test-coverage-goals)
5. [Test Data Strategy](#test-data-strategy)
6. [CI/CD Integration](#cicd-integration)
7. [RAG-Specific Testing](#rag-specific-testing)
8. [LLM Integration Testing](#llm-integration-testing)
9. [Quality Metrics](#quality-metrics)
10. [Test Environment Setup](#test-environment-setup)
11. [Documentation & Maintenance](#documentation--maintenance)

---

## Overview

### Project Context

Teduco is a GenAI-powered education consultation tool with a multi-layered architecture:

- **Frontend**: Next.js 16 with TypeScript (84.3%)
- **Backend**: Python FastAPI with LangChain RAG (11.8%)
- **Database**: PostgreSQL/Supabase (2.9%)
- **Infrastructure**: Docker Compose

### Testing Philosophy

Our testing strategy prioritizes:

1. **High-Value Tests First**: Focus on critical user paths (chatbot, RAG pipeline, university matching)
2. **Maintainability**: Tests should be easy to understand and update
3. **Fast Feedback**: Quick local tests, comprehensive CI tests
4. **External Dependency Mocking**: Mock LLM APIs, web scraping for deterministic tests
5. **Balance**: Comprehensive coverage without sacrificing development velocity

---

## Testing Scope & Levels

### 1. Frontend Testing (Next.js/TypeScript)

#### Unit Tests
- **React Components**: UI rendering, props handling, state management
- **Utility Functions**: Date formatting, string manipulation, data transformations
- **Hooks**: Custom React hooks (`useUserProfile`, `useMessages`, etc.)
- **API Client**: HTTP request logic, error handling, token management

**Example Components to Test:**
```
- ChatInterface
- UserProfile
- DocumentUpload
- UniversitySearch
- OnboardingFlow
```

#### Integration Tests
- **API Routes**: Next.js API routes (if any)
- **React Query Integration**: Data fetching, caching, invalidation
- **Form Submissions**: Complete form flows with validation
- **Authentication Flow**: Login, logout, token refresh

#### E2E Tests
- **Critical User Journeys**:
  - Sign up → Complete onboarding → Ask first question → Receive answer
  - Upload document → Document processed → View in library
  - Search universities → Filter results → View details
- **Multi-language Support**: Turkish and English switching
- **Mobile Responsiveness**: Test on various viewport sizes

#### Visual Regression Tests
- **UI Consistency**: Screenshot comparison for key pages
- **Theme Support**: Light/dark mode rendering
- **Component Library**: Shadcn/UI component rendering

#### Accessibility Tests
- **WCAG 2.1 Level AA Compliance**:
  - Keyboard navigation
  - Screen reader compatibility
  - Color contrast
  - ARIA attributes

### 2. Backend Testing (Python)

#### Unit Tests
- **API Endpoints**: Request/response validation, status codes
- **Business Logic**: User profile management, document processing
- **Data Transformation**: CamelCase ↔ snake_case conversion
- **Authentication**: JWT validation, user extraction
- **Pydantic Models**: Schema validation, type checking

**Key Modules to Test:**
```python
- src/main.py (endpoints)
- src/core/schemas.py (Pydantic models)
- src/db/lib/core.py (database functions)
- src/api/* (API routes)
```

#### Integration Tests
- **LangChain RAG Pipeline**:
  - Document ingestion flow
  - Vector search integration
  - Context retrieval accuracy
- **Database Operations**: CRUD operations with test database
- **Supabase Integration**: Auth, storage, database queries

#### RAG Pipeline Tests
- **Web Scraper (`crawler.py`)**: Mock HTTP responses, HTML parsing
- **PDF Conversion (`conversion.py`)**: Sample PDFs, Markdown output validation
- **Text Splitting (`langchain_splitters.py`)**: Chunk size, overlap, consistency

#### Database Tests
- **Schema Validation**: Table structures, constraints, indexes
- **Migration Tests**: Up/down migration consistency
- **Query Performance**: Vector search latency benchmarks
- **Data Integrity**: Foreign key constraints, cascades

### 3. End-to-End Testing

#### Full User Journeys
```
Journey 1: New User Onboarding
1. Sign up with email
2. Complete profile (education, preferences)
3. Upload transcript/diploma
4. Receive personalized recommendations

Journey 2: Q&A Interaction
1. Ask question in Turkish
2. Receive cited answer
3. Follow-up question
4. View source documents

Journey 3: University Search
1. Search for "computer science UK"
2. Filter by tuition < $30k
3. Save favorite universities
4. Compare programs
```

#### Cross-Browser Testing
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

---

## Testing Tools & Frameworks

### Frontend Stack

#### Testing Framework: **Vitest** (Recommended)
- **Why**: Faster than Jest, native ESM support, Vite integration
- **Alternative**: Jest (if existing setup)

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

#### React Testing Library
- Component rendering and interaction
- User-centric queries (getByRole, getByLabelText)
- Accessibility-first approach

#### E2E: **Playwright** (Recommended)
- **Why**: Cross-browser, auto-wait, parallel execution, trace viewer
- **Alternative**: Cypress (if existing setup)

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
})
```

#### Visual Testing: **Percy** or **Chromatic**
- Percy: Free tier, GitHub integration
- Chromatic: Storybook integration (if using Storybook)

### Backend Stack

#### Testing Framework: **pytest** (Recommended)
- **Why**: Industry standard, powerful fixtures, plugins

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    rag: RAG pipeline tests
    slow: Slow-running tests
```

#### HTTP Testing: **httpx** + **TestClient**
```python
from fastapi.testclient import TestClient
from httpx import AsyncClient

client = TestClient(app)
response = client.get("/profile", headers={"Authorization": f"Bearer {token}"})
```

#### Mocking: **pytest-mock** + **responses**
- pytest-mock: Function mocking
- responses: HTTP request mocking

### API Testing

#### **Postman Collections** (Optional)
- Manual testing and documentation
- Export collections for CI integration

### Performance Testing

#### **Locust** (Recommended for backend)
- Python-based load testing
- Test RAG query throughput
- Monitor vector search latency

```python
# locustfile.py
from locust import HttpUser, task, between

class TeducoUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def ask_question(self):
        self.client.post("/chats/{chat_id}/messages", json={
            "message": "What are the best universities for CS?"
        })
```

#### **k6** (Alternative)
- JavaScript-based, cloud-ready

---

## Test Coverage Goals

### Coverage Targets

| Layer | Unit Coverage | Integration Coverage | E2E Coverage |
|-------|---------------|----------------------|--------------|
| **Frontend** | 80% | 70% | Critical paths 100% |
| **Backend** | 85% | 75% | Critical paths 100% |
| **RAG Pipeline** | 90% | 85% | Core flows 100% |

### Critical Paths (100% Coverage Required)

#### Frontend
1. Authentication flow (login, signup, logout)
2. Chat message sending and receiving
3. Document upload and viewing
4. University search and filtering

#### Backend
1. User authentication and authorization
2. Profile CRUD operations
3. Chat message handling
4. RAG query processing
5. Document ingestion pipeline

#### RAG Pipeline
1. PDF → Markdown conversion
2. Text chunking and splitting
3. Vector embedding generation
4. Similarity search queries
5. Context retrieval and ranking

### Edge Cases to Test

- **Empty States**: No chats, no documents, no results
- **Error States**: Network failures, API errors, invalid inputs
- **Boundary Conditions**: Max file size, max message length, character limits
- **Unicode/Multi-language**: Turkish characters, emojis, RTL text
- **Rate Limiting**: Exceeded quotas, retry logic
- **Concurrent Operations**: Multiple uploads, simultaneous queries

---

## Test Data Strategy

### 1. Synthetic Student Profiles

```typescript
// frontend/tests/fixtures/students.ts
export const mockStudents = {
  undergraduate: {
    firstName: "Ahmet",
    lastName: "Yılmaz",
    education: {
      level: "undergraduate",
      gpa: 3.5,
      major: "Computer Science"
    },
    preferences: {
      countries: ["USA", "UK", "Germany"],
      budget: 30000,
      fieldOfStudy: "Computer Science"
    }
  },
  graduate: {
    firstName: "Zeynep",
    lastName: "Kaya",
    education: {
      level: "graduate",
      gpa: 3.8,
      major: "Data Science"
    }
  }
}
```

### 2. Mock University Data

```python
# backend/tests/fixtures/universities.py
MOCK_UNIVERSITIES = [
    {
        "id": "uni-001",
        "name": "MIT",
        "country": "USA",
        "tuition_usd": 55000,
        "programs": ["Computer Science", "Engineering"],
        "requirements": {
            "gpa_min": 3.5,
            "toefl_min": 100
        }
    },
    # ... more universities
]
```

### 3. Test PDFs and Documents

**Location**: `tests/fixtures/documents/`

```
tests/fixtures/documents/
├── sample_transcript.pdf (1 page, simple layout)
├── complex_diploma.pdf (multi-page, tables, images)
├── turkish_document.pdf (UTF-8, Turkish characters)
├── scanned_document.pdf (OCR required)
└── malformed.pdf (edge case: corrupted)
```

### 4. Mock LLM Responses

```python
# backend/tests/fixtures/llm_responses.py
MOCK_LLM_RESPONSES = {
    "university_question": {
        "question": "What are the best universities for CS in the UK?",
        "answer": "Based on rankings, Imperial College London, Oxford...",
        "sources": ["uni-001", "uni-002"],
        "confidence": 0.92
    },
    "visa_question": {
        "question": "What documents do I need for UK student visa?",
        "answer": "You will need: 1) CAS letter 2) Passport...",
        "sources": ["doc-visa-uk-001"],
        "confidence": 0.88
    }
}
```

### 5. Database Seeding Scripts

```python
# backend/tests/utils/seed_db.py
async def seed_test_database():
    """Populate test database with fixtures"""
    await create_test_users()
    await create_test_universities()
    await create_test_documents()
    await create_test_chats()
```

### 6. Mock Vector Embeddings

```python
# backend/tests/fixtures/embeddings.py
import numpy as np

def generate_mock_embedding(dimension=1536):
    """Generate deterministic mock embedding"""
    return np.random.RandomState(42).rand(dimension).tolist()
```

---

## CI/CD Integration

### GitHub Actions Workflow

**File**: `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  frontend-tests:
    name: Frontend Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Run linter
        working-directory: frontend
        run: npm run lint
      
      - name: Type check
        working-directory: frontend
        run: npx tsc --noEmit
      
      - name: Run unit tests
        working-directory: frontend
        run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend

  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: teduco_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        working-directory: backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx
      
      - name: Run linter
        working-directory: backend
        run: |
          pip install ruff
          ruff check src/
      
      - name: Run unit tests
        working-directory: backend
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/teduco_test
        run: pytest tests/ --cov=src --cov-report=xml -m "not slow"
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
          flags: backend

  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: [frontend-tests, backend-tests]
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install Playwright
        working-directory: frontend
        run: |
          npm ci
          npx playwright install --with-deps chromium
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for services
        run: |
          npx wait-on http://localhost:3000 http://localhost:8000/docs
      
      - name: Run E2E tests
        working-directory: frontend
        run: npx playwright test
      
      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30
```

### Pre-commit Hooks

**File**: `.husky/pre-commit` (using husky)

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Frontend
cd frontend
npm run lint
npx tsc --noEmit
npm run test:changed

# Backend
cd ../backend
ruff check src/
python -m pytest tests/unit/ -x
```

### PR Checks

Required status checks before merge:
- ✅ All unit tests pass
- ✅ Integration tests pass
- ✅ Linting passes
- ✅ Type checking passes
- ✅ Code coverage ≥ 80%
- ✅ No security vulnerabilities (Dependabot)

### Staging Environment Tests

After deployment to staging:
1. Run smoke tests (critical paths)
2. Run performance benchmarks
3. Check database migrations applied
4. Verify environment variables

---

## RAG-Specific Testing

### 1. Vector Similarity Search Accuracy

**Test**: Retrieve top-k most relevant documents

```python
# backend/tests/test_rag_retrieval.py
import pytest
from src.rag.retrieval import retrieve_context

@pytest.mark.rag
def test_university_query_retrieval_accuracy():
    """Test that CS program queries retrieve CS-related docs"""
    query = "computer science programs in USA"
    results = retrieve_context(query, top_k=5)
    
    # Assert all results are CS-related
    assert len(results) == 5
    for result in results:
        assert result.score > 0.7  # High similarity
        assert "computer science" in result.content.lower()
```

### 2. Retrieved Context Relevance

**Metric**: Precision@K, Recall@K, NDCG

```python
def test_context_relevance_metrics():
    """Test retrieval quality metrics"""
    test_cases = load_test_queries()  # Gold standard queries
    
    precision_scores = []
    for case in test_cases:
        results = retrieve_context(case.query, top_k=10)
        relevant_docs = [r for r in results if r.doc_id in case.relevant_doc_ids]
        precision = len(relevant_docs) / len(results)
        precision_scores.append(precision)
    
    avg_precision = sum(precision_scores) / len(precision_scores)
    assert avg_precision > 0.8  # 80% precision required
```

### 3. PDF → Markdown → Chunks Pipeline

```python
# backend/tests/test_rag_pipeline.py
from src.rag.parser.conversion import pdf_to_markdown
from src.rag.chunker.langchain_splitters import split_text

@pytest.mark.rag
def test_pdf_to_chunks_fidelity():
    """Test complete ingestion pipeline preserves information"""
    pdf_path = "tests/fixtures/documents/sample_transcript.pdf"
    
    # Step 1: PDF to Markdown
    markdown = pdf_to_markdown(pdf_path)
    assert len(markdown) > 0
    assert "University" in markdown  # Check key content preserved
    
    # Step 2: Markdown to chunks
    chunks = split_text(markdown, chunk_size=500, overlap=50)
    assert len(chunks) > 0
    
    # Step 3: Verify no information loss
    combined = " ".join([c.page_content for c in chunks])
    assert "University" in combined
    assert len(combined) >= len(markdown) * 0.95  # 95% content retained
```

### 4. Citation and Source Attribution

```python
def test_answer_includes_sources():
    """Test that RAG answers cite sources"""
    response = generate_answer(
        question="What is MIT's CS program ranking?",
        context=mock_mit_context
    )
    
    assert response.answer is not None
    assert response.sources is not None
    assert len(response.sources) > 0
    assert any("MIT" in s.title for s in response.sources)
```

### 5. Multi-language Document Processing

```python
@pytest.mark.parametrize("language,pdf_file", [
    ("english", "english_doc.pdf"),
    ("turkish", "turkish_doc.pdf"),
])
def test_multilingual_parsing(language, pdf_file):
    """Test parsing of documents in different languages"""
    pdf_path = f"tests/fixtures/documents/{pdf_file}"
    markdown = pdf_to_markdown(pdf_path)
    
    assert len(markdown) > 0
    # Check for language-specific characters
    if language == "turkish":
        assert any(c in markdown for c in ["ı", "ğ", "ü", "ş", "ö", "ç"])
```

### 6. Chunking Strategy Effectiveness

```python
def test_chunk_size_and_overlap():
    """Test that chunks have appropriate size and overlap"""
    text = "A" * 1000  # Long text
    chunks = split_text(text, chunk_size=500, overlap=50)
    
    # Test chunk sizes
    for chunk in chunks:
        assert len(chunk.page_content) <= 550  # Allow some variance
    
    # Test overlap
    if len(chunks) > 1:
        overlap_text = chunks[0].page_content[-50:]
        assert overlap_text in chunks[1].page_content
```

---

## LLM Integration Testing

### 1. Mock LLM Responses

```python
# backend/tests/conftest.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_llm():
    """Mock LLM API calls"""
    with patch('langchain.llms.OpenAI') as mock:
        mock.return_value.predict.return_value = "Mocked LLM response"
        yield mock

def test_chat_with_mock_llm(mock_llm):
    """Test chat flow with mocked LLM"""
    response = send_message("What are good CS programs?")
    assert response is not None
    mock_llm.return_value.predict.assert_called_once()
```

### 2. Prompt Engineering Validation

```python
def test_system_prompt_includes_context():
    """Test that prompts include retrieved context"""
    question = "What is MIT's tuition?"
    context = [{"content": "MIT tuition is $55,000"}]
    
    prompt = build_prompt(question, context)
    
    assert "MIT tuition is $55,000" in prompt
    assert question in prompt
    assert "Based on the following context" in prompt
```

### 3. Answer Quality Metrics

```python
@pytest.mark.slow
def test_answer_quality_with_real_llm():
    """Test answer quality with real LLM (run in CI only)"""
    test_cases = [
        {
            "question": "What GPA is required for MIT?",
            "expected_contains": ["3.5", "GPA", "requirement"]
        }
    ]
    
    for case in test_cases:
        answer = generate_answer(case["question"])
        for expected in case["expected_contains"]:
            assert expected.lower() in answer.lower()
```

### 4. Rate Limiting and Error Handling

```python
def test_rate_limit_handling():
    """Test graceful handling of rate limits"""
    with patch('openai.ChatCompletion.create') as mock:
        mock.side_effect = RateLimitError("Rate limit exceeded")
        
        with pytest.raises(HTTPException) as exc_info:
            generate_answer("Test question")
        
        assert exc_info.value.status_code == 429
```

### 5. Token Usage Monitoring

```python
def test_token_usage_tracking():
    """Test that we track token usage"""
    with patch('tiktoken.encoding_for_model') as mock_encoder:
        mock_encoder.return_value.encode.return_value = [1] * 100
        
        usage = estimate_tokens("What are good universities?")
        
        assert usage > 0
        assert usage < 200  # Sanity check
```

---

## Quality Metrics

### 1. Test Execution Time Budgets

| Test Type | Max Duration | Target Duration |
|-----------|--------------|-----------------|
| Unit test (single) | 100ms | 10ms |
| Integration test | 5s | 1s |
| E2E test (single) | 30s | 10s |
| Full unit suite | 2min | 30s |
| Full E2E suite | 10min | 5min |

**Enforcement**: Tests exceeding budget get `@pytest.mark.slow` tag

### 2. Flakiness Tolerance

- **Max flaky test rate**: 2% (tests failing intermittently)
- **Flaky test action**: Quarantine → investigate → fix or remove
- **CI retry policy**: Max 2 retries for E2E tests

### 3. Code Coverage Thresholds

```ini
# pytest.ini
[coverage:report]
fail_under = 80
skip_empty = True

[coverage:run]
omit = 
    */tests/*
    */migrations/*
    */__init__.py
```

### 4. Performance Benchmarks

| Metric | Target | Max Acceptable |
|--------|--------|----------------|
| API response (p95) | 200ms | 500ms |
| RAG retrieval (p95) | 500ms | 1500ms |
| PDF conversion | 2s/page | 5s/page |
| Vector search | 100ms | 300ms |
| Chat response (p95) | 3s | 8s |

**Monitoring**: Track in CI, alert on regression > 20%

---

## Test Environment Setup

### Local Development Testing

#### 1. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install Vitest
npm install -D vitest @vitest/ui @testing-library/react @testing-library/jest-dom

# Run tests
npm run test          # Watch mode
npm run test:ui       # UI mode
npm run test:coverage # With coverage
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio httpx responses

# Run tests
pytest                           # All tests
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest -m "not slow"            # Skip slow tests
pytest -v --cov=src --cov-report=html
```

#### 3. E2E Setup

```bash
cd frontend

# Install Playwright
npm install -D @playwright/test
npx playwright install

# Run E2E tests
npx playwright test
npx playwright test --ui        # UI mode
npx playwright show-report      # View report
```

### Docker Compose Test Environment

**File**: `docker-compose.test.yml`

```yaml
version: '3.8'

services:
  postgres-test:
    image: postgres:15
    environment:
      POSTGRES_DB: teduco_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data  # In-memory for speed

  backend-test:
    build:
      context: ./backend
      dockerfile: dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres-test:5432/teduco_test
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_KEY: ${SUPABASE_ANON_KEY}
      MOCK_LLM: "true"
    depends_on:
      - postgres-test
    ports:
      - "8001:8000"

  frontend-test:
    build:
      context: ./frontend
      dockerfile: dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://backend-test:8000
      NEXT_PUBLIC_SUPABASE_URL: ${SUPABASE_URL}
      NEXT_PUBLIC_SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
    ports:
      - "3001:3000"
    depends_on:
      - backend-test
```

**Usage**:
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run tests against Docker services
NEXT_PUBLIC_API_URL=http://localhost:8001 npm run test:e2e

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

### Supabase Local Instance

```bash
# Install Supabase CLI
brew install supabase/tap/supabase  # macOS
# Or: npm install -g supabase

# Start local Supabase
cd supabase
supabase start

# Apply migrations
supabase db push

# Seed test data
supabase db seed

# Reset database
supabase db reset
```

### Environment Variables for Tests

**File**: `backend/.env.test`

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/teduco_test

# Supabase
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=test-anon-key
SUPABASE_SERVICE_KEY=test-service-key

# Testing
MOCK_LLM=true
MOCK_EMBEDDINGS=true
SKIP_AUTH=false  # Set to true for non-auth tests

# LLM (if testing with real API)
OPENAI_API_KEY=sk-test-key
```

### Test Isolation Strategies

#### 1. Database Isolation
```python
@pytest.fixture(scope="function")
async def db_session():
    """Each test gets a fresh transaction"""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        yield connection
        await connection.run_sync(Base.metadata.drop_all)
```

#### 2. File System Isolation
```python
@pytest.fixture
def temp_upload_dir(tmp_path):
    """Temporary directory for file uploads"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    yield upload_dir
    # Auto-cleanup by pytest
```

#### 3. Cache Isolation
```typescript
// Frontend: Clear React Query cache between tests
afterEach(() => {
  queryClient.clear()
})
```

---

## Documentation & Maintenance

### Test Documentation Standards

#### 1. Test Naming Convention

```python
# ✅ Good: Descriptive, specific
def test_user_cannot_access_other_users_documents():
    """Test that document access is properly restricted"""
    pass

def test_pdf_with_turkish_characters_parses_correctly():
    """Regression test for issue #123"""
    pass

# ❌ Bad: Vague, unclear
def test_documents():
    pass

def test_feature_works():
    pass
```

#### 2. Test Structure (AAA Pattern)

```python
def test_create_chat_message():
    # Arrange: Setup test data
    user_id = create_test_user()
    chat_id = create_test_chat(user_id)
    message = "What are good CS programs?"
    
    # Act: Perform the action
    response = client.post(
        f"/chats/{chat_id}/messages",
        json={"message": message},
        headers={"Authorization": f"Bearer {get_token(user_id)}"}
    )
    
    # Assert: Verify the outcome
    assert response.status_code == 200
    assert response.json()["message"] == message
    assert response.json()["chatId"] == chat_id
```

#### 3. Test Comments

```python
def test_chunking_with_large_overlap():
    """
    Test text chunking with 50% overlap.
    
    This ensures that:
    1. Context is preserved across chunks
    2. Semantic boundaries are respected
    3. Retrieval quality is improved
    
    Related: RAG-123 (chunking strategy optimization)
    """
    pass
```

### How to Run Tests

**Documentation**: Update `README.md`

```markdown
## Running Tests

### Frontend Tests

```bash
cd frontend

# Unit tests
npm run test              # Watch mode
npm run test:coverage     # With coverage report

# E2E tests
npm run test:e2e          # Headless
npm run test:e2e:ui       # With UI

# Specific tests
npm run test -- ComponentName.test.tsx
```

### Backend Tests

```bash
cd backend

# All tests
pytest

# Specific test types
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest -m rag               # RAG-specific tests
pytest -m "not slow"        # Skip slow tests

# With coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html     # View coverage report

# Specific tests
pytest tests/unit/test_user.py
pytest tests/unit/test_user.py::test_create_user
```

### E2E Tests (Full Stack)

```bash
# Start services
docker-compose up -d

# Wait for services
npx wait-on http://localhost:3000 http://localhost:8000

# Run tests
cd frontend
npx playwright test

# View report
npx playwright show-report
```

### CI Tests

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request
- Nightly (full suite including slow tests)

View results: GitHub Actions → Test Suite workflow
```

### Debugging Failed Tests

**Documentation**: `docs/DEBUGGING_TESTS.md`

```markdown
## Debugging Failed Tests

### Frontend Tests

1. **Run in UI mode**:
   ```bash
   npm run test:ui
   ```

2. **Run single test**:
   ```bash
   npm run test -- -t "test name pattern"
   ```

3. **Debug in VS Code**:
   - Add breakpoint
   - Run "Debug Current Test" from command palette

### Backend Tests

1. **Verbose output**:
   ```bash
   pytest -vv --tb=short
   ```

2. **Debug with pdb**:
   ```python
   def test_something():
       import pdb; pdb.set_trace()
       # test code
   ```

3. **Show print statements**:
   ```bash
   pytest -s
   ```

### E2E Tests

1. **Headed mode** (see browser):
   ```bash
   npx playwright test --headed
   ```

2. **Debug mode** (step through):
   ```bash
   npx playwright test --debug
   ```

3. **Trace viewer** (after failure):
   ```bash
   npx playwright show-trace trace.zip
   ```

4. **Screenshots on failure**: Automatically saved to `test-results/`

### Common Issues

**Issue**: Tests pass locally, fail in CI
- **Cause**: Timing issues, environment differences
- **Solution**: Add explicit waits, check env vars

**Issue**: Flaky E2E tests
- **Cause**: Race conditions, network timing
- **Solution**: Use Playwright auto-wait, increase timeout

**Issue**: Database tests fail
- **Cause**: Dirty state from previous test
- **Solution**: Ensure proper cleanup in fixtures
```

### Test Maintenance Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Review and update test coverage | Weekly | Dev Team |
| Remove/fix flaky tests | Immediately | Test author |
| Update test fixtures | As needed | Dev Team |
| Performance benchmark review | Monthly | Tech Lead |
| E2E test suite optimization | Quarterly | QA/Dev |
| Test documentation update | With features | Feature dev |
| Dependency updates (testing libs) | Monthly | DevOps |

---

## Appendix

### Recommended VS Code Extensions

- **Test Explorer UI**: Visualize and run tests
- **Vitest**: Vitest integration
- **Playwright Test**: Playwright integration
- **Coverage Gutters**: Show coverage in editor

### Useful Commands Reference

```bash
# Frontend
npm run test                    # Run tests
npm run test:coverage          # With coverage
npm run test:ui                # UI mode
npm run test:e2e              # E2E tests
npm run test:e2e:ui           # E2E with UI

# Backend
pytest                         # All tests
pytest -m unit                # Unit tests
pytest -m integration         # Integration tests
pytest -m rag                 # RAG tests
pytest --cov=src              # With coverage
pytest -x                     # Stop on first failure
pytest --lf                   # Run last failed

# Docker
docker-compose -f docker-compose.test.yml up
docker-compose -f docker-compose.test.yml down -v

# Supabase
supabase start                # Start local instance
supabase db reset             # Reset database
supabase db seed              # Seed data
```

### Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [LangChain Testing Guide](https://python.langchain.com/docs/guides/debugging)

---

**Document Status**: Living document - update as testing practices evolve  
**Feedback**: Open issues or PRs to improve this strategy  
**Questions**: Contact the development team
