# Code Review & Improvement Suggestions

This document contains additional code quality improvements and best practices identified during the performance optimization review.

## Critical Issues (Should Fix Soon)

### 1. Missing Database Indexes

**Impact:** High - Affects query performance as data grows

**Location:** Database schema

**Issue:** No indexes on foreign key columns and frequently queried fields.

**Recommendation:**
```sql
-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_id_user_id ON documents(document_id, user_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chats_user_id_last_message ON chats(user_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_high_school_education_user_id ON high_school_education(user_id);
CREATE INDEX IF NOT EXISTS idx_university_education_user_id ON university_education(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_preferences_user_id ON onboarding_preferences(user_id);
```

**Benefit:** 5-10x faster queries on tables with >1000 rows

### 2. No Rate Limiting

**Impact:** High - Security and resource vulnerability

**Location:** `backend/src/main.py`

**Issue:** Expensive endpoints (file upload, AI chat) have no rate limiting.

**Recommendation:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/documents")
@limiter.limit("10/minute")  # Max 10 uploads per minute
def add_document(...):
    ...

@app.post("/chats/{chat_id}/messages")
@limiter.limit("30/minute")  # Max 30 messages per minute
def send_message(...):
    ...
```

### 3. Sensitive Error Messages

**Impact:** Medium - Security concern

**Location:** `backend/src/main.py` - Error handling

**Issue:** Error messages expose internal details in production.

**Current:**
```python
except Exception as e:
    raise HTTPException(500, f"Failed to create chat: {str(e)}")
```

**Recommendation:**
```python
import logging

except Exception as e:
    logging.error(f"Failed to create chat: {str(e)}", exc_info=True)
    # Don't expose internal error details in production
    if settings.environment == "production":
        raise HTTPException(500, "An error occurred")
    else:
        raise HTTPException(500, f"Failed to create chat: {str(e)}")
```

## Important Improvements (Should Consider)

### 4. No Request Validation for Pagination

**Impact:** Medium - Potential for abuse

**Location:** `backend/src/main.py` - `get_messages()`

**Issue:** Negative offsets and very large limits not validated.

**Recommendation:**
```python
@app.get("/chats/{chat_id}/messages")
def get_messages(
    chat_id: str, 
    limit: int = Query(default=50, ge=1, le=100),  # Between 1-100
    offset: int = Query(default=0, ge=0),           # Non-negative
    user_id: str = Depends(get_current_user)
):
    ...
```

### 5. Missing Input Sanitization

**Impact:** Medium - XSS vulnerability

**Location:** `backend/src/main.py` - All text input endpoints

**Issue:** User-generated content not sanitized before storage.

**Recommendation:**
```python
import bleach

def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML/JS from user input"""
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a']
    allowed_attrs = {'a': ['href', 'title']}
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)

@app.post("/chats/{chat_id}/messages")
def send_message(chat_id: str, message: MessageCreate, ...):
    sanitized_content = sanitize_html(message.content)
    # Store sanitized content
```

### 6. No Connection Timeout Configuration

**Impact:** Medium - Resource leak potential

**Location:** `backend/src/db/lib/core.py`

**Issue:** Supabase client doesn't have explicit timeout configuration.

**Recommendation:**
```python
from supabase import create_client, ClientOptions

settings = get_settings()
supabase = create_client(
    settings.supabase_url, 
    settings.supabase_service_key,
    options=ClientOptions(
        postgrest_client_timeout=10,  # 10 second timeout
        storage_client_timeout=30,     # 30 second timeout for file ops
    )
)
```

### 7. Redundant Code - Endpoint Aliases

**Impact:** Low - Maintenance burden

**Location:** `backend/src/main.py`

**Issue:** Multiple endpoints serve identical functionality:
- `/profile` and `/settings` are aliases
- `/onboarding` and `/onboarding/profile` do similar things

**Recommendation:**
- Keep one canonical endpoint
- Deprecate aliases with warnings
- Update frontend to use canonical endpoints
- Remove aliases in next major version

```python
@app.get("/settings", response_model=UserProfileResponse, deprecated=True)
def get_settings(user_id: str = Depends(get_current_user)):
    """DEPRECATED: Use /profile instead. Will be removed in v1.0"""
    warnings.warn("This endpoint is deprecated. Use /profile instead.", DeprecationWarning)
    return get_profile(user_id)
```

## Code Quality Improvements

### 8. Missing Type Hints

**Impact:** Low - Developer experience

**Location:** `backend/src/db/lib/core.py`

**Issue:** Some function parameters lack type hints.

**Recommendation:**
```python
# Before
def upsert_user(auth_uid: str, first_name: str, last_name: str, **extras):
    ...

# After
from typing import Any, Dict

def upsert_user(
    auth_uid: str, 
    first_name: str, 
    last_name: str, 
    **extras: Any
) -> Dict[str, Any]:
    ...
```

### 9. Magic Numbers and Strings

**Impact:** Low - Maintainability

**Location:** Various files

**Issue:** Hardcoded values scattered throughout code.

**Recommendation:**
```python
# backend/src/core/config.py
class Settings(BaseSettings):
    # Existing settings...
    
    # Add constants
    MAX_MESSAGE_LIMIT: int = 100
    DEFAULT_MESSAGE_LIMIT: int = 50
    MAX_FILE_SIZE_MB: int = 10
    DEFAULT_SIGNED_URL_EXPIRY: int = 3600
    
# Use in endpoints
@app.get("/chats/{chat_id}/messages")
def get_messages(
    chat_id: str,
    limit: int = settings.DEFAULT_MESSAGE_LIMIT,
    ...
):
    limit = min(limit, settings.MAX_MESSAGE_LIMIT)
```

### 10. Inconsistent Error Handling

**Impact:** Low - User experience

**Location:** All mutation hooks in `frontend/hooks/api/`

**Issue:** Some errors show toast, some don't. Inconsistent error messages.

**Recommendation:**
```typescript
// Create a consistent error handler
// frontend/lib/error-handler.ts
export function handleMutationError(
  error: Error,
  operation: string,
  context?: { rollback?: () => void }
) {
  console.error(`${operation} failed:`, error)
  
  if (context?.rollback) {
    context.rollback()
  }
  
  const userMessage = isApiError(error)
    ? error.message
    : `Failed to ${operation}. Please try again.`
  
  toast.error(userMessage)
}

// Use consistently
export function useUpdateChat() {
  return useMutation({
    mutationFn: ...,
    onError: (error, variables, context) => {
      handleMutationError(error, 'update chat', {
        rollback: () => {
          if (context?.previousChat) {
            queryClient.setQueryData(...)
          }
        }
      })
    }
  })
}
```

## Performance Monitoring (Future Work)

### 11. Add Performance Metrics

**Impact:** High - Observability

**Recommendation:**
```python
# backend/src/middleware/metrics.py
import time
from starlette.middleware.base import BaseHTTPMiddleware

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > 1.0:  # 1 second threshold
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration:.2f}s"
            )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        return response

app.add_middleware(MetricsMiddleware)
```

### 12. Add Frontend Performance Tracking

**Recommendation:**
```typescript
// frontend/lib/performance.ts
export function trackApiCall(endpoint: string, duration: number) {
  if (duration > 1000) {  // > 1 second
    console.warn(`Slow API call: ${endpoint} took ${duration}ms`)
  }
  
  // Send to analytics service
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'api_call', {
      endpoint,
      duration,
      slow: duration > 1000
    })
  }
}

// Use in API client
private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const timer = createTimer(`${method} ${endpoint}`)
  try {
    // ... existing code
    const data = await response.json()
    const duration = timer.end()
    trackApiCall(endpoint, duration)
    return data
  } catch (error) {
    // ...
  }
}
```

## Security Recommendations

### 13. Add CORS Origin Validation

**Impact:** High - Security

**Location:** `backend/src/main.py`

**Issue:** CORS origins from environment variable not validated.

**Recommendation:**
```python
# Validate CORS origins
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
validated_origins = []

for origin in allowed_origins:
    origin = origin.strip()
    # Validate origin format
    if origin.startswith(('http://', 'https://')):
        validated_origins.append(origin)
    else:
        logger.warning(f"Invalid CORS origin rejected: {origin}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=validated_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 14. Add Request Size Limits

**Impact:** High - Security (DoS prevention)

**Recommendation:**
```python
# Add to main.py
from starlette.middleware.base import BaseHTTPMiddleware

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request, call_next):
        if request.method in ('POST', 'PUT', 'PATCH'):
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > self.max_request_size:
                raise HTTPException(413, "Request too large")
        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware)
```

## Testing Recommendations

### 15. Add Integration Tests

**Files to create:**
- `backend/tests/test_performance.py`
- `frontend/tests/hooks/api/performance.test.ts`

**Example:**
```python
# backend/tests/test_performance.py
import pytest
import time
from fastapi.testclient import TestClient

def test_get_user_profile_performance(client, auth_token):
    """Profile fetch should complete in under 200ms"""
    start = time.time()
    response = client.get(
        "/profile",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 0.2  # 200ms threshold

def test_parallel_queries_faster_than_sequential(client, auth_token):
    """Parallel queries should be faster than sequential"""
    # This would require mocking or actual database calls
    # to verify the optimization works
    pass
```

## Documentation Improvements

### 16. Add API Documentation

**Recommendation:**
- FastAPI auto-generates docs at `/docs`
- Add better descriptions to endpoints
- Document rate limits
- Add example responses

```python
@app.get(
    "/chats/{chat_id}/messages",
    response_model=List[MessageResponse],
    summary="Get chat messages",
    description="""
    Retrieve paginated messages for a specific chat.
    
    - **Rate limit**: 60 requests/minute
    - **Default limit**: 50 messages
    - **Max limit**: 100 messages
    - Messages are ordered by creation time (oldest first)
    """,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "msg_123",
                            "chatId": "chat_456",
                            "content": "Hello!",
                            "role": "user",
                            "createdAt": "2025-12-27T10:00:00Z"
                        }
                    ]
                }
            }
        },
        404: {"description": "Chat not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
def get_messages(...):
    ...
```

## Priority Summary

**Implement Immediately:**
1. Database indexes (#1)
2. Rate limiting (#2)
3. Error message sanitization (#3)
4. Input validation (#4)

**Implement Soon:**
5. XSS sanitization (#5)
6. Connection timeouts (#6)
7. Performance monitoring (#11, #12)
8. CORS validation (#13)
9. Request size limits (#14)

**Nice to Have:**
10. Remove redundant endpoints (#7)
11. Fix type hints (#8)
12. Extract magic numbers (#9)
13. Standardize error handling (#10)
14. Add integration tests (#15)
15. Improve API docs (#16)
