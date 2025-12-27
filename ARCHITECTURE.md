# Teduco AI - System Architecture Documentation

**Version:** 1.0  
**Last Updated:** December 27, 2025  
**Team Reference:** Use this document as the single source of truth for architectural decisions

---

## Table of Contents

1. [Architectural Overview](#architectural-overview)
2. [Why This Architecture?](#why-this-architecture)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow](#data-flow)
6. [Naming Conventions](#naming-conventions)
7. [Adding New Features](#adding-new-features)
8. [Common Patterns](#common-patterns)
9. [Troubleshooting Guide](#troubleshooting-guide)

---

## Architectural Overview

### The Big Picture

Think of our application like a restaurant:

- **Frontend (Next.js)** = The dining room where customers interact
- **Backend (FastAPI)** = The kitchen where all the cooking happens
- **Database (Supabase)** = The pantry where all ingredients are stored
- **Authentication (Supabase Auth)** = The host who checks if customers have reservations

```
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │         Next.js Frontend (Port 3000)              │      │
│  │                                                     │      │
│  │  • React Components (UI)                          │      │
│  │  • React Query (Data Fetching)                    │      │
│  │  • Supabase Client (Auth Only)                    │      │
│  └──────────────────┬──────────────────────────────────┘      │
└─────────────────────┼──────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
  ┌──────────┐              ┌─────────────┐
  │ Supabase │              │   FastAPI   │
  │   Auth   │              │   Backend   │
  │          │              │ (Port 8000) │
  └──────────┘              └──────┬──────┘
                                   │
                                   │ All Business Logic
                                   │ All Database Queries
                                   │
                            ┌──────▼──────┐
                            │  Supabase   │
                            │  PostgreSQL │
                            │  + Storage  │
                            └─────────────┘
```

### Key Principle: **Unified Backend Architecture**

**Everything goes through FastAPI.** The frontend never talks directly to the database (except for auth tokens).

---

## Why This Architecture?

### The Problem We Solved

Initially, we had **three different ways** of accessing data:

1. Frontend → Supabase directly (for some settings)
2. Frontend → Next.js API routes → Supabase (for user profiles)
3. Frontend → FastAPI → Supabase (for chats and documents)

**Why was this bad?**

Imagine if in a restaurant:
- Some customers order directly from the pantry
- Some customers order through a waiter
- Some customers order through the chef

Chaos! You'd have:
- No single point where you can check "is this customer allowed to order this?"
- Duplicate rules in three different places
- Hard to know where a bug is hiding
- Team members confused about where to add new features

### The Solution: Unified Backend (Option 1)

**All business logic lives in one place: FastAPI**

**Benefits:**
1. **Single Source of Truth** - All rules in one place
2. **Easier Testing** - Test one codebase, not three
3. **Better Security** - One place to check permissions
4. **Easier Debugging** - Follow the flow: Frontend → Backend → Database
5. **Type Safety** - Python validates data before it reaches the database
6. **Automatic Data Transformation** - Backend handles snake_case ↔ camelCase

---

## Backend Architecture

### Technology Stack

- **Language:** Python 3.11
- **Framework:** FastAPI (modern, fast, auto-documented)
- **Validation:** Pydantic v2 (automatic data validation)
- **Database:** Supabase PostgreSQL
- **Container:** Docker

### Core Concepts Explained Simply

#### 1. The Magic of Pydantic Models

**Think of Pydantic like a strict bouncer at a club.**

Before any data enters our system, Pydantic checks:
- ✅ Is this actually a string? (not a number pretending to be text)
- ✅ Is this email format valid?
- ✅ Are required fields present?
- ❌ Reject anything that doesn't match the rules

**Example:**

```python
from pydantic import BaseModel

class UserProfile(BaseModel):
    first_name: str      # MUST be text
    email: EmailStr      # MUST be valid email format
    age: int            # MUST be a number
    
# This works:
user = UserProfile(
    first_name="John",
    email="john@example.com",
    age=25
)

# This fails (Pydantic rejects it):
user = UserProfile(
    first_name=123,        # ❌ Not text!
    email="not-an-email",  # ❌ Not valid email!
    age="twenty"          # ❌ Not a number!
)
```

#### 2. Automatic Case Conversion

**The Problem:**
- **Database** uses `snake_case` (PostgreSQL convention): `first_name`, `created_at`
- **Frontend** uses `camelCase` (JavaScript convention): `firstName`, `createdAt`

**Without conversion, we'd need to write:**
```javascript
// Frontend nightmare:
const firstName = userData.first_name  // Ugly!
const createdAt = userData.created_at  // Inconsistent with JS!
```

**Our Solution: CamelCaseModel**

```python
# backend/src/core/models.py
class CamelCaseModel(BaseModel):
    """Automatically converts snake_case to camelCase"""
    model_config = ConfigDict(
        alias_generator=to_camel,  # Magic happens here!
        populate_by_name=True      # Accept both formats as input
    )
```

**What this does:**

```python
# Database has: { "first_name": "John", "created_at": "2025-01-01" }
# Backend reads it as snake_case
# Frontend receives: { "firstName": "John", "createdAt": "2025-01-01" }
# ✨ Automatic conversion! ✨
```

**Real Example:**

```python
# backend/src/core/schemas.py
class UserProfileResponse(CamelCaseModel):
    first_name: str      # Database: first_name
    last_name: str       # Frontend receives: firstName, lastName
    created_at: str      # Frontend receives: createdAt
```

Frontend sees:
```typescript
{
  firstName: "John",    // ← Converted!
  lastName: "Doe",
  createdAt: "2025-01-01"
}
```

#### 3. Endpoint Structure

**Pattern:** Resource-based URLs (RESTful)

```
GET    /profile              # Get current user's profile
PUT    /profile              # Update profile
GET    /settings             # Alias for /profile
PATCH  /settings             # Partial update

GET    /documents            # List all documents
POST   /documents            # Upload new document
DELETE /documents/{id}       # Delete specific document

GET    /chats                # List all chats
POST   /chats                # Create new chat
GET    /chats/{id}/messages  # Get messages for chat
POST   /chats/{id}/messages  # Send message to chat
```

**Why this structure?**

Think of URLs like filing cabinets:
- `/profile` = Your personal file drawer
- `/documents` = Documents folder
- `/chats/{id}/messages` = Messages inside a specific chat folder

Easy to understand, easy to remember!

#### 4. Authentication Flow

```python
# Every protected endpoint:
@app.get("/profile")
def get_profile(user_id: str = Depends(get_current_user)):
    # FastAPI automatically:
    # 1. Checks Authorization header
    # 2. Validates JWT token with Supabase
    # 3. Extracts user_id
    # 4. Passes it to your function
    
    return get_user_profile(user_id)
```

**Security Simplified:**

1. Frontend gets token from Supabase Auth
2. Frontend sends token in every request: `Authorization: Bearer <token>`
3. Backend asks Supabase: "Is this token valid?"
4. If yes → proceed, if no → reject with 401

---

## Frontend Architecture

### Technology Stack

- **Framework:** Next.js 16 (React with routing)
- **State Management:** React Query (server state)
- **HTTP Client:** Custom API client wrapper
- **UI Library:** shadcn/ui + Tailwind CSS
- **Forms:** React Hook Form
- **Validation:** Zod schemas

### Core Concepts Explained Simply

#### 1. React Query: The Smart Data Manager

**Think of React Query like a smart assistant who:**
- Fetches data when you need it
- Remembers what it fetched (caching)
- Knows when data is stale and refetches
- Handles loading and error states
- Prevents duplicate requests

**Without React Query (bad):**
```typescript
const [data, setData] = useState(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)

useEffect(() => {
  setLoading(true)
  fetch('/api/profile')
    .then(res => res.json())
    .then(data => setData(data))
    .catch(err => setError(err))
    .finally(() => setLoading(false))
}, [])

// 😫 So much boilerplate!
// 😫 No caching
// 😫 Fetches every time component mounts
```

**With React Query (good):**
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['profile'],
  queryFn: () => apiClient.getUserProfile()
})

// ✨ Auto caching
// ✨ Auto refetch on window focus
// ✨ Deduplicates requests
// ✨ Clean!
```

#### 2. API Client Pattern

**Location:** `frontend/lib/api-client.ts`

**Purpose:** Single place for all HTTP requests

```typescript
class ApiClient {
  // Every request goes through here
  private async request(method, endpoint, data) {
    // 1. Get auth token
    // 2. Set headers
    // 3. Make request
    // 4. Handle errors
    // 5. Return data
  }
  
  // Convenient methods
  async getUserProfile() {
    return this.get('/profile')
  }
  
  async updateProfile(data) {
    return this.put('/profile', data)
  }
}
```

**Why centralize?**

Imagine every component calling `fetch()` directly:
- Different error handling in each component
- Different token handling
- Different base URLs
- Hard to change API structure

**With ApiClient:**
- Change base URL? Update one line
- Change auth? Update one function
- Add logging? One place
- Consistent errors everywhere

#### 3. Custom Hooks Pattern

**Location:** `frontend/hooks/api/`

**Purpose:** Reusable data fetching logic

```typescript
// hooks/api/use-user.ts
export function useUserProfile() {
  return useQuery({
    queryKey: ['user', 'profile'],
    queryFn: () => apiClient.getUserProfile()
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data) => apiClient.updateUserProfile(data),
    onSuccess: () => {
      // Invalidate cache → triggers refetch
      queryClient.invalidateQueries(['user', 'profile'])
      toast.success('Profile updated!')
    }
  })
}
```

**Usage in components:**
```typescript
function ProfilePage() {
  const { data: profile, isLoading } = useUserProfile()
  const updateProfile = useUpdateProfile()
  
  if (isLoading) return <Spinner />
  
  return (
    <form onSubmit={(data) => updateProfile.mutate(data)}>
      {/* form fields */}
    </form>
  )
}
```

**Benefits:**
- Components stay clean
- Logic is reusable
- Easy to test
- Consistent patterns

---

## Data Flow

### Example: User Updates Their Profile

**Step-by-step flow:**

```
1. User fills form and clicks "Save"
   └─> Form validates with Zod schema
   
2. Component calls: updateProfile.mutate(data)
   └─> React Query mutation starts
   
3. Custom hook: useUpdateProfile()
   └─> Calls apiClient.updateUserProfile(data)
   
4. API Client
   ├─> Gets auth token from Supabase
   ├─> Sends PUT /profile with data
   └─> Headers: { Authorization: "Bearer <token>" }
   
5. FastAPI Backend
   ├─> get_current_user() validates token
   ├─> Extracts user_id
   ├─> Converts camelCase → snake_case
   └─> Calls database function
   
6. Database Layer
   ├─> UPDATE users SET first_name = ...
   └─> Returns updated row
   
7. Backend Response
   ├─> Converts snake_case → camelCase
   └─> Returns: { firstName: "John", ... }
   
8. API Client
   └─> Receives response, returns data
   
9. React Query
   ├─> onSuccess callback fires
   ├─> Invalidates ['user', 'profile'] cache
   ├─> Automatically refetches profile
   └─> Shows success toast
   
10. UI Updates
    └─> Profile refreshes with new data
```

**Visual Diagram:**

```
┌──────────────┐
│   Browser    │
│              │
│  [Form] ────>│ onClick
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  React Query     │ updateProfile.mutate(data)
│  Mutation        │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  API Client      │ PUT /profile
│  + Auth Token    │
└──────┬───────────┘
       │
       │ HTTP Request
       ▼
┌──────────────────────┐
│  FastAPI Backend     │
│                      │
│  1. Validate token   │
│  2. Validate data    │
│  3. Transform case   │
│  4. Update database  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────┐
│  Supabase        │
│  PostgreSQL      │
│  UPDATE users... │
└──────┬───────────┘
       │
       │ Updated row
       ▼
┌──────────────────────┐
│  FastAPI Backend     │
│  Transform to        │
│  camelCase           │
└──────┬───────────────┘
       │
       │ { firstName: "..." }
       ▼
┌──────────────────┐
│  API Client      │ Response
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  React Query     │ onSuccess
│  Invalidate &    │ Refetch
│  Update UI       │
└──────────────────┘
```

---

## Naming Conventions

### The Golden Rules

| Layer | Convention | Example |
|-------|-----------|---------|
| **Database** | `snake_case` | `first_name`, `created_at` |
| **Backend (Python)** | `snake_case` | `def get_user_profile()` |
| **Backend (Models)** | `snake_case` fields | `first_name: str` |
| **API Response** | `camelCase` | `{ firstName: "..." }` |
| **Frontend (TypeScript)** | `camelCase` | `const firstName = ...` |
| **React Components** | `PascalCase` | `UserProfile.tsx` |

### Why Different Cases?

**Each ecosystem has its own conventions:**

- **PostgreSQL:** Historically uses `snake_case` (like `first_name`)
- **Python:** PEP 8 style guide says `snake_case` for variables
- **JavaScript/TypeScript:** Convention is `camelCase` for variables
- **React:** Components use `PascalCase`

**We respect each ecosystem's conventions** and handle conversion automatically!

### Conversion Examples

```python
# Database column
first_name = "John"

# Backend Python variable
user_data = {"first_name": "John"}

# API Response (automatic conversion)
{
  "firstName": "John"  # ← Pydantic converts this!
}

# Frontend TypeScript
const firstName = userData.firstName
```

**Key Point:** You never manually convert. The `CamelCaseModel` does it automatically!

---

## Adding New Features

### Step-by-Step Guide

Let's add a new feature: **User can add a bio to their profile**

#### Step 1: Update Database Schema

```sql
-- supabase/migrations/YYYYMMDDHHMMSS_add_user_bio.sql
ALTER TABLE users ADD COLUMN bio TEXT;
```

#### Step 2: Update Backend Schema

```python
# backend/src/core/schemas.py
class UserProfileResponse(CamelCaseModel):
    first_name: str
    last_name: str
    bio: Optional[str] = None  # ← Add this
```

**Pydantic automatically converts `bio` to `bio` (same in both cases)**

#### Step 3: Update Backend Endpoint

```python
# backend/src/main.py
@app.get("/profile", response_model=UserProfileResponse)
def get_profile(user_id: str = Depends(get_current_user)):
    raw_profile = get_user_profile(user_id)
    
    result = {
        "first_name": raw_profile["user"]["first_name"],
        "last_name": raw_profile["user"]["last_name"],
        "bio": raw_profile["user"].get("bio"),  # ← Add this
    }
    
    return UserProfileResponse(**result)

@app.put("/profile")
def update_profile(payload: dict, user_id: str = Depends(get_current_user)):
    upsert_user(
        user_id,
        payload.get("firstName", payload.get("first_name")),
        payload.get("lastName", payload.get("last_name")),
        bio=payload.get("bio")  # ← Add this
    )
    return {"message": "ok"}
```

#### Step 4: Update Database Function

```python
# backend/src/db/lib/core.py
def upsert_user(user_id, first_name, last_name, bio=None, **kwargs):
    supabase.table("users").upsert({
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "bio": bio,  # ← Add this
    }).execute()
```

#### Step 5: Update Frontend TypeScript Interface (Optional)

```typescript
// frontend/types/user.ts (if you create one)
interface UserProfile {
  firstName: string
  lastName: string
  bio?: string  // ← Add this
}
```

#### Step 6: Update Frontend Form

```tsx
// frontend/app/(auth)/settings/page.tsx
<Textarea
  {...register("bio")}
  placeholder="Tell us about yourself"
/>
```

**That's it!** The flow automatically works:

1. Form sends `{ bio: "I love coding" }`
2. API Client sends to `/profile`
3. Backend validates and saves to database
4. Response returns with `bio` field
5. Frontend displays updated profile

---

## Common Patterns

### Pattern 1: Query with Automatic Refetch

**Use when:** Displaying data that might change

```typescript
export function useUserProfile() {
  return useQuery({
    queryKey: ['user', 'profile'],
    queryFn: () => apiClient.getUserProfile(),
    staleTime: 5 * 60 * 1000,  // Data fresh for 5 minutes
    refetchOnWindowFocus: true  // Refetch when user returns to tab
  })
}
```

### Pattern 2: Mutation with Cache Invalidation

**Use when:** Updating data

```typescript
export function useUpdateProfile() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data) => apiClient.updateUserProfile(data),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['user', 'profile'] })
      toast.success('Profile updated!')
    },
    onError: (error) => {
      toast.error(`Failed: ${error.message}`)
    }
  })
}
```

### Pattern 3: Conditional Query

**Use when:** Query depends on some condition

```typescript
export function useMessages(chatId: string | undefined) {
  return useQuery({
    queryKey: ['chats', chatId, 'messages'],
    queryFn: () => apiClient.getMessages(chatId!),
    enabled: !!chatId && chatId !== 'undefined',  // Only run if chatId is valid
  })
}
```

### Pattern 4: Optimistic Updates

**Use when:** You want instant UI feedback

```typescript
export function useDeleteDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id) => apiClient.deleteDocument(id),
    
    // Before server responds
    onMutate: async (id) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['documents'] })
      
      // Snapshot current data
      const previous = queryClient.getQueryData(['documents'])
      
      // Optimistically update UI
      queryClient.setQueryData(['documents'], (old) =>
        old.filter(doc => doc.documentId !== id)
      )
      
      return { previous }
    },
    
    // If mutation fails, rollback
    onError: (err, id, context) => {
      queryClient.setQueryData(['documents'], context.previous)
      toast.error('Failed to delete')
    },
    
    // Always refetch after success or error
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    }
  })
}
```

---

## Troubleshooting Guide

### Problem: "Cannot read property 'charAt' of undefined"

**Cause:** Backend returns `docType` but frontend expects `doc_type`

**Solution:** Update frontend to use camelCase:
```typescript
// ❌ Wrong
doc.doc_type.charAt(0)

// ✅ Correct
doc.docType?.charAt(0)  // Use optional chaining
```

### Problem: "GET /chats/undefined/messages 500 Error"

**Cause:** Passing literal string "undefined" instead of preventing query

**Solution:** Use conditional queries:
```typescript
// ❌ Wrong
useMessages(chatId || '')

// ✅ Correct
useMessages(chatId)  // Hook handles undefined

// In hook:
enabled: !!chatId && chatId !== 'undefined'
```

### Problem: "404 Not Found on /settings endpoint"

**Cause:** Old Docker container running without new endpoints

**Solution:**
```bash
# Stop old container
docker stop <container_id>

# Rebuild with latest code
cd backend
docker build -f dockerfile -t teduco-backend .

# Run new container
docker run -d -p 8000:8000 --env-file .env teduco-backend
```

### Problem: Data showing snake_case in frontend

**Cause:** Model doesn't inherit from `CamelCaseModel`

**Solution:**
```python
# ❌ Wrong
class MyResponse(BaseModel):
    first_name: str

# ✅ Correct
class MyResponse(CamelCaseModel):  # Use CamelCaseModel!
    first_name: str
```

### Problem: "Address already in use" when starting backend

**Solution:**
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process or use Docker
docker ps
docker stop <container_id>
```

---

## Best Practices for the Team

### ✅ DO

1. **Always use React Query** for server state
2. **Always go through FastAPI** for database operations
3. **Use TypeScript interfaces** for better type safety
4. **Inherit from CamelCaseModel** for all response schemas
5. **Use optional chaining** (`?.`) when accessing possibly undefined fields
6. **Invalidate queries** after mutations
7. **Handle loading and error states** in every component
8. **Use absolute imports** (`@/components` not `../../components`)

### ❌ DON'T

1. **Don't access Supabase directly** from frontend (except auth)
2. **Don't manually convert case** (Pydantic does this)
3. **Don't use `any` type** in TypeScript
4. **Don't forget `enabled` flag** in conditional queries
5. **Don't skip error handling**
6. **Don't duplicate logic** across frontend and backend
7. **Don't hardcode URLs** (use environment variables)

### Code Review Checklist

- [ ] Backend endpoint uses `CamelCaseModel` for responses
- [ ] Frontend hook uses React Query
- [ ] Mutations invalidate relevant cache keys
- [ ] Loading and error states handled
- [ ] TypeScript types defined (no `any`)
- [ ] Auth token validated on backend
- [ ] Input data validated with Pydantic
- [ ] Database queries use parameterized queries (no SQL injection)
- [ ] Errors logged appropriately
- [ ] Success/error toasts shown to user

---

## Quick Reference

### Common Commands

```bash
# Start backend (development)
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start backend (Docker)
cd backend
docker build -f dockerfile -t teduco-backend .
docker run -d -p 8000:8000 --env-file .env teduco-backend

# Start frontend
cd frontend
npm run dev

# Check TypeScript errors
cd frontend
npm run type-check

# Run database migrations
cd supabase
supabase db push

# View API documentation
# Visit: http://localhost:8000/docs
```

### File Locations

```
backend/
├── src/
│   ├── main.py                 # API endpoints
│   ├── core/
│   │   ├── models.py          # CamelCaseModel base
│   │   ├── schemas.py         # Response models
│   │   └── config.py          # Settings
│   └── db/
│       └── lib/
│           └── core.py        # Database functions

frontend/
├── app/                        # Next.js pages
├── components/                 # UI components
├── hooks/
│   └── api/                   # React Query hooks
├── lib/
│   ├── api-client.ts          # HTTP client
│   └── supabase.ts            # Supabase client
└── types/                     # TypeScript types
```

---

## Conclusion

This architecture is designed to be:

- **Simple:** One path for data (Frontend → Backend → Database)
- **Consistent:** Same patterns everywhere
- **Safe:** Type checking at every layer
- **Maintainable:** Easy to find and fix bugs
- **Scalable:** Add features without changing structure

**Remember:** When in doubt, follow the existing patterns. If you see code that doesn't match this documentation, it's probably old code that needs updating.

**Questions?** Discuss with the team or update this document!

---

**Document Maintainers:** Update this when making architectural changes  
**Team Members:** Read this before starting any new feature
