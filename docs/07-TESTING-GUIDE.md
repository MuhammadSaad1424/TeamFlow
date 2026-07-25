# Testing Guide & Quality Assurance

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [E2E Testing](#e2e-testing)
5. [Performance Testing](#performance-testing)
6. [Security Testing](#security-testing)
7. [Coverage & Metrics](#coverage--metrics)

## Testing Strategy

### Test Pyramid

```
    /\
   /E2E\ (10%)
  /------\
 /Integration\ (30%)
/-----------\
/  Unit Tests \ (60%)
/-----------\
```

### Testing Framework

```
Backend (Python):
- pytest: Main test framework
- pytest-asyncio: Async support
- pytest-cov: Coverage reporting
- factory-boy: Test data generation
- faker: Random data generation
- responses: HTTP mocking

Frontend (TypeScript):
- Jest: Test runner
- React Testing Library: Component testing
- Playwright: E2E testing
- MSW: API mocking
```

## Unit Testing

### Backend Unit Tests

#### Test Structure

```
tests/
├── unit/
│   ├── test_validators.py
│   ├── test_security.py
│   ├── test_embeddings.py
│   ├── test_retrieval.py
│   └── test_response_generation.py
├── fixtures/
│   └── conftest.py
└── factories/
    └── test_factories.py
```

#### Example Test Cases

**Test Input Validators** (app/utils/validators.py)

```python
import pytest
from app.utils.validators import (
    sanitize_input,
    validate_github_url,
    extract_github_info,
    is_code_file,
    get_file_language,
)

class TestValidators:
    def test_sanitize_input_removes_xss(self):
        malicious = "<script>alert('xss')</script>"
        result = sanitize_input(malicious)
        assert "<script>" not in result
        assert "alert" in result  # Text preserved, tags removed
    
    def test_validate_github_url_valid(self):
        url = "https://github.com/user/repo"
        assert validate_github_url(url) is True
    
    def test_validate_github_url_invalid(self):
        url = "https://example.com/repo"
        assert validate_github_url(url) is False
    
    def test_extract_github_info_success(self):
        url = "https://github.com/torvalds/linux"
        owner, repo = extract_github_info(url)
        assert owner == "torvalds"
        assert repo == "linux"
    
    def test_is_code_file_python(self):
        assert is_code_file("script.py") is True
        assert is_code_file("readme.md") is False
    
    def test_get_file_language_detection(self):
        assert get_file_language("main.js") == "javascript"
        assert get_file_language("main.py") == "python"
        assert get_file_language("main.rs") == "rust"
```

**Test Security Functions** (app/core/security.py)

```python
import pytest
from datetime import timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

class TestSecurity:
    def test_password_hashing_consistency(self):
        password = "secure_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Different hashes for same password (salt difference)
        assert hash1 != hash2
        # Both verify successfully
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_password_verification_fails_wrong_password(self):
        password = "correct_password"
        hashed = hash_password(password)
        
        assert verify_password("wrong_password", hashed) is False
    
    def test_access_token_creation(self):
        user_id = "test-user-123"
        token = create_access_token(user_id)
        
        assert token is not None
        decoded = decode_token(token)
        assert decoded["sub"] == user_id
        assert "exp" in decoded
    
    def test_refresh_token_creation(self):
        user_id = "test-user-123"
        token = create_refresh_token(user_id)
        
        decoded = decode_token(token, token_type="refresh")
        assert decoded["sub"] == user_id
    
    def test_token_expiration(self):
        user_id = "test-user-123"
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(user_id, expires_delta)
        
        with pytest.raises(Exception):  # Expired token
            decode_token(token)
```

**Test Embedding Service**

```python
import pytest
from app.rag.embeddings.embedding_service import (
    EmbeddingProcessor,
    SemanticSimilarity,
)

@pytest.mark.asyncio
class TestEmbeddingService:
    @pytest.fixture
    async def processor(self):
        processor = EmbeddingProcessor(
            model_type="openai",
            model_name="text-embedding-3-large"
        )
        await processor.initialize()
        yield processor
        await processor.close()
    
    @pytest.mark.asyncio
    async def test_embed_single_text(self, processor):
        text = "def hello_world(): print('Hello World')"
        embedding = await processor.embed_text(text)
        
        assert len(embedding) == 3072  # OpenAI embedding dimension
        assert isinstance(embedding, list)
    
    @pytest.mark.asyncio
    async def test_embed_multiple_texts(self, processor):
        texts = [
            "function one() { return 1; }",
            "function two() { return 2; }",
            "function three() { return 3; }"
        ]
        embeddings = await processor.embed_texts(texts)
        
        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 3072
    
    def test_cosine_similarity(self):
        similarity = SemanticSimilarity()
        
        # Identical vectors
        vec1 = [1, 0, 0]
        vec2 = [1, 0, 0]
        assert similarity.cosine_similarity(vec1, vec2) == pytest.approx(1.0)
        
        # Orthogonal vectors
        vec1 = [1, 0, 0]
        vec2 = [0, 1, 0]
        assert similarity.cosine_similarity(vec1, vec2) == pytest.approx(0.0)
```

## Integration Testing

### Backend Integration Tests

```
tests/
├── integration/
│   ├── test_auth_flow.py
│   ├── test_repository_workflow.py
│   ├── test_chat_pipeline.py
│   └── test_rag_pipeline.py
```

**Test Authentication Flow**

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
class TestAuthenticationFlow:
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_github_login_redirect(self, client):
        response = await client.get("/api/v1/auth/github/login")
        
        assert response.status_code == 302
        assert "github.com" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_github_callback_creates_user(self, client, mock_github):
        # Mock GitHub API response
        with mock_github():
            response = await client.get(
                "/api/v1/auth/github/callback",
                params={"code": "test-code"}
            )
        
        assert response.status_code == 302
        assert "token" in response.cookies
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client, authenticated_user):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": authenticated_user.refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
```

**Test Repository Workflow**

```python
@pytest.mark.asyncio
class TestRepositoryWorkflow:
    @pytest.mark.asyncio
    async def test_complete_repository_indexing(self, client, authenticated_user):
        # 1. Create repository
        create_response = await client.post(
            "/api/v1/repositories",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
            json={
                "repo_url": "https://github.com/example/repo",
                "repo_name": "example-repo"
            }
        )
        assert create_response.status_code == 201
        repo_id = create_response.json()["id"]
        
        # 2. Start indexing
        index_response = await client.post(
            f"/api/v1/repositories/{repo_id}/index",
            headers={"Authorization": f"Bearer {authenticated_user.token}"}
        )
        assert index_response.status_code == 202
        
        # 3. Check status
        status_response = await client.get(
            f"/api/v1/repositories/{repo_id}/status",
            headers={"Authorization": f"Bearer {authenticated_user.token}"}
        )
        status = status_response.json()
        assert status["indexing_status"] in ["pending", "in_progress", "completed"]
```

## E2E Testing

### Frontend E2E Tests (Playwright)

```python
import pytest
from playwright.async_api import Browser

@pytest.mark.asyncio
class TestFrontendE2E:
    @pytest.fixture
    async def browser(self):
        browser = await Browser()
        yield browser
        await browser.close()
    
    @pytest.mark.asyncio
    async def test_complete_user_flow(self, browser):
        page = await browser.new_page()
        
        # 1. Navigate to app
        await page.goto("http://localhost:3000")
        assert await page.title() == "TeamFlow AI"
        
        # 2. Login with GitHub
        await page.click("button:has-text('Login with GitHub')")
        await page.wait_for_url("https://github.com/login/oauth/**")
        
        # Mock GitHub login
        await page.fill("#login_field", "testuser@example.com")
        await page.fill("#password", "testpass")
        await page.click("input[type='submit']")
        
        # 3. Should be on dashboard
        await page.wait_for_url("http://localhost:3000/dashboard")
        
        # 4. Add repository
        await page.click("button:has-text('Add Repository')")
        await page.fill("input[name='repo_url']", "https://github.com/example/repo")
        await page.click("button:has-text('Index')")
        
        # 5. Wait for indexing
        await page.wait_for_selector("text=Indexing complete")
        
        # 6. Chat with codebase
        await page.fill("input[placeholder='Ask about the code...']", "What does this project do?")
        await page.press("input", "Enter")
        
        # 7. Wait for response
        await page.wait_for_selector(".ai-response")
        response = await page.text_content(".ai-response")
        assert len(response) > 0
        
        # 8. Check citations
        citations = await page.query_selector_all(".citation")
        assert len(citations) > 0
```

## Performance Testing

### Load Testing with K6

```javascript
// tests/performance/load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(99)<500'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function() {
  let response = http.get('http://localhost:8000/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
  
  sleep(1);
}
```

### Latency Benchmarking

```python
import time
import statistics
from app.rag.retrieval.retrieval_engine import RetrievalEngine

class TestPerformance:
    def test_retrieval_latency(self, sample_embeddings):
        engine = RetrievalEngine()
        query = "How does authentication work?"
        
        latencies = []
        for _ in range(100):
            start = time.time()
            results = engine.hybrid_search(query, top_k=5)
            latency = time.time() - start
            latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[95]
        
        print(f"Average: {avg_latency*1000:.2f}ms")
        print(f"P95: {p95_latency*1000:.2f}ms")
        
        assert avg_latency < 3.0  # < 3 seconds
        assert p95_latency < 5.0  # < 5 seconds
```

## Security Testing

### OWASP Top 10 Testing

**SQL Injection**

```python
@pytest.mark.asyncio
async def test_sql_injection_prevention(client, authenticated_user):
    malicious_input = "'; DROP TABLE users; --"
    
    response = await client.post(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {authenticated_user.token}"},
        json={"query": malicious_input}
    )
    
    assert response.status_code == 200
    # Database should still exist
    assert "error" not in response.json()
```

**XSS Prevention**

```python
@pytest.mark.asyncio
async def test_xss_prevention(client, authenticated_user):
    xss_payload = "<script>alert('xss')</script>"
    
    response = await client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {authenticated_user.token}"},
        json={"message": xss_payload}
    )
    
    assert response.status_code == 200
    # Response should escape or sanitize
    data = response.json()
    assert "<script>" not in data["response"]
```

**Authentication & Authorization**

```python
@pytest.mark.asyncio
async def test_unauthorized_access(client):
    response = await client.get("/api/v1/conversations")
    
    assert response.status_code == 401
```

## Coverage & Metrics

### Running Tests with Coverage

```bash
# Python backend
pytest --cov=app --cov-report=html --cov-report=term-missing tests/

# JavaScript frontend
npm test -- --coverage
```

### Coverage Goals

```
Target Coverage:
- Unit Tests: >80%
- Integration Tests: >70%
- E2E Tests: >60% (critical paths)
- Overall: >75%

Coverage by Component:
- Core Logic: >90%
- API Endpoints: >85%
- RAG Pipeline: >80%
- Utils: >75%
```

### Metrics to Track

1. **Test Execution**:
   - Time per test
   - Total execution time
   - Parallel execution efficiency

2. **Code Quality**:
   - Code coverage percentage
   - Cyclomatic complexity
   - Code duplication

3. **Performance**:
   - API response latency (p50, p95, p99)
   - Database query time
   - Memory usage
   - CPU usage

4. **Reliability**:
   - Test pass rate
   - Flaky tests
   - Test stability

---

## Continuous Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest --cov

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm test -- --coverage
```

---

## Conclusion

This comprehensive testing guide covers:
- Unit test examples
- Integration tests
- E2E testing with Playwright
- Performance testing with K6
- Security testing
- Coverage metrics and tracking
- CI/CD integration

Target: >75% overall code coverage with focus on critical paths.
