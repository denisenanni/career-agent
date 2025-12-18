# API Documentation

Complete API reference for the Career Agent backend.

**Base URL (Production):** `https://career-agent.railway.app` (example)
**Base URL (Local):** `http://localhost:8000`

**Authentication:** JWT Bearer token (unless marked as public)

---

## Table of Contents

- [Authentication](#authentication)
- [Profile](#profile)
- [Jobs](#jobs)
- [Matches](#matches)
- [Generation](#generation)
- [Insights](#insights)
- [Skills](#skills)
- [Health](#health)

---

## Authentication

### Register

Create a new user account.

**Endpoint:** `POST /auth/register`
**Authentication:** None (public)

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-12-18T10:00:00Z"
}
```

**Errors:**
- `400 Bad Request` - Email already exists
- `422 Unprocessable Entity` - Invalid email format or password too short

---

### Login

Authenticate and receive JWT token.

**Endpoint:** `POST /auth/login`
**Authentication:** None (public)

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Errors:**
- `401 Unauthorized` - Invalid credentials
- `422 Unprocessable Entity` - Missing required fields

**Notes:**
- Token expires in 7 days (604800 seconds)
- Include token in subsequent requests: `Authorization: Bearer <token>`

---

### Logout

Logout user (client-side token removal).

**Endpoint:** `POST /auth/logout`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

**Notes:**
- Backend doesn't maintain token state
- Client should remove token from localStorage

---

### Get Current User

Get authenticated user details.

**Endpoint:** `GET /auth/me`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "bio": "Software Engineer",
  "skills": ["Python", "React", "PostgreSQL"],
  "experience_years": 5,
  "preferences": {
    "target_roles": ["Software Engineer", "Full Stack Developer"],
    "remote_only": true,
    "min_salary": 80000
  },
  "cv_uploaded_at": "2024-12-18T10:00:00Z",
  "created_at": "2024-12-18T10:00:00Z"
}
```

**Errors:**
- `401 Unauthorized` - Invalid or expired token

---

## Profile

### Get Profile

Get user profile and preferences.

**Endpoint:** `GET /api/profile`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "bio": "Experienced software engineer",
  "skills": ["Python", "React", "TypeScript", "PostgreSQL"],
  "experience_years": 5,
  "preferences": {
    "target_roles": ["Software Engineer", "Backend Developer"],
    "remote_only": true,
    "min_salary": 100000,
    "max_salary": 150000,
    "job_types": ["permanent", "contract"],
    "parsed_cv": {
      "name": "John Doe",
      "email": "user@example.com",
      "skills": ["Python", "React", "PostgreSQL"],
      "experience": [...],
      "education": [...]
    }
  },
  "cv_filename": "resume.pdf",
  "cv_uploaded_at": "2024-12-18T10:00:00Z"
}
```

---

### Update Profile

Update user profile and preferences.

**Endpoint:** `PUT /api/profile`
**Authentication:** Required

**Request Body:**
```json
{
  "full_name": "John Doe",
  "bio": "Senior Software Engineer",
  "skills": ["Python", "React", "TypeScript", "Docker", "Kubernetes"],
  "experience_years": 6,
  "preferences": {
    "target_roles": ["Senior Software Engineer", "Tech Lead"],
    "remote_only": true,
    "min_salary": 120000,
    "max_salary": 180000,
    "job_types": ["permanent"]
  }
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "bio": "Senior Software Engineer",
  "skills": ["Python", "React", "TypeScript", "Docker", "Kubernetes"],
  "experience_years": 6,
  "preferences": {
    "target_roles": ["Senior Software Engineer", "Tech Lead"],
    "remote_only": true,
    "min_salary": 120000,
    "max_salary": 180000,
    "job_types": ["permanent"]
  },
  "updated_at": "2024-12-18T11:00:00Z"
}
```

**Notes:**
- All fields are optional (partial updates supported)
- Skills must be an array of strings
- Preferences can include custom fields

---

### Upload CV

Upload and parse CV file (PDF, DOCX, or TXT).

**Endpoint:** `POST /api/profile/cv`
**Authentication:** Required
**Content-Type:** `multipart/form-data`
**Rate Limit:** 5 requests per hour per IP

**Request:**
```
POST /api/profile/cv
Content-Type: multipart/form-data

file: <binary data>
```

**Response:** `200 OK`
```json
{
  "message": "CV uploaded and parsed successfully",
  "filename": "resume.pdf",
  "parsed_cv": {
    "name": "John Doe",
    "email": "user@example.com",
    "phone": "+1234567890",
    "summary": "Experienced software engineer with 5 years...",
    "skills": ["Python", "React", "PostgreSQL", "Docker"],
    "experience": [
      {
        "company": "Tech Corp",
        "title": "Software Engineer",
        "start_date": "2020-01",
        "end_date": "present",
        "description": "Developed backend APIs..."
      }
    ],
    "education": [
      {
        "institution": "University XYZ",
        "degree": "Bachelor of Science",
        "field": "Computer Science",
        "end_date": "2019"
      }
    ],
    "years_of_experience": 5
  }
}
```

**Errors:**
- `400 Bad Request` - Invalid file format
- `413 Payload Too Large` - File exceeds size limit
- `422 Unprocessable Entity` - Failed to parse CV
- `429 Too Many Requests` - Rate limit exceeded

**Notes:**
- Supported formats: PDF, DOCX, TXT
- Max file size: 10MB
- Parsing uses Claude Haiku (cached for 30 days)
- Parsed data automatically updates user preferences

---

### Get Parsed CV

Retrieve parsed CV data.

**Endpoint:** `GET /api/profile/cv/parsed`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "name": "John Doe",
  "email": "user@example.com",
  "phone": "+1234567890",
  "summary": "Experienced software engineer...",
  "skills": ["Python", "React", "PostgreSQL"],
  "experience": [...],
  "education": [...],
  "years_of_experience": 5
}
```

**Errors:**
- `404 Not Found` - No CV uploaded yet

---

## Jobs

### List Jobs

Get paginated list of job postings with optional filters.

**Endpoint:** `GET /api/jobs`
**Authentication:** None (public)

**Query Parameters:**
- `limit` (int, default: 50) - Number of jobs per page
- `offset` (int, default: 0) - Pagination offset
- `search` (string) - Full-text search query
- `source` (string) - Filter by source (e.g., "remoteok")
- `remote_type` (string) - Filter by remote type ("full", "hybrid", "onsite")
- `job_type` (string) - Filter by job type ("permanent", "contract", "part-time")
- `min_salary` (int) - Minimum salary filter
- `max_salary` (int) - Maximum salary filter

**Example:**
```
GET /api/jobs?search=python&remote_type=full&limit=20&offset=0
```

**Response:** `200 OK`
```json
{
  "jobs": [
    {
      "id": 123,
      "source": "remoteok",
      "source_id": "12345",
      "url": "https://remoteok.com/remote-jobs/12345",
      "title": "Senior Python Developer",
      "company": "Tech Startup Inc",
      "description": "We are looking for an experienced Python developer...",
      "salary_min": 100000,
      "salary_max": 150000,
      "salary_currency": "USD",
      "location": "Remote",
      "remote_type": "full",
      "job_type": "permanent",
      "tags": ["Python", "Django", "PostgreSQL", "Docker"],
      "posted_at": "2024-12-15T09:00:00Z",
      "scraped_at": "2024-12-18T08:00:00Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

**Notes:**
- Uses full-text search on title, company, description
- Results sorted by `scraped_at DESC` (newest first)
- Efficient pagination with window functions

---

### Get Job Details

Get detailed information for a specific job.

**Endpoint:** `GET /api/jobs/{job_id}`
**Authentication:** None (public)

**Response:** `200 OK`
```json
{
  "id": 123,
  "source": "remoteok",
  "source_id": "12345",
  "url": "https://remoteok.com/remote-jobs/12345",
  "title": "Senior Python Developer",
  "company": "Tech Startup Inc",
  "description": "Full job description here...",
  "salary_min": 100000,
  "salary_max": 150000,
  "salary_currency": "USD",
  "location": "Remote",
  "remote_type": "full",
  "job_type": "permanent",
  "tags": ["Python", "Django", "PostgreSQL", "Docker"],
  "raw_data": {...},
  "posted_at": "2024-12-15T09:00:00Z",
  "scraped_at": "2024-12-18T08:00:00Z",
  "created_at": "2024-12-18T08:00:00Z"
}
```

**Errors:**
- `404 Not Found` - Job not found

---

### Refresh Jobs

Trigger job scraping from configured sources.

**Endpoint:** `POST /api/jobs/refresh`
**Authentication:** Required

**Response:** `202 Accepted`
```json
{
  "message": "Job scraping started",
  "sources": ["remoteok", "weworkremotely"],
  "scrape_log_id": 42
}
```

**Notes:**
- Asynchronous operation (jobs scraped in background)
- Creates scrape log entry for tracking
- Only authenticated users can trigger scraping

---

## Matches

### Get Matches

Get ranked job matches for authenticated user.

**Endpoint:** `GET /api/matches`
**Authentication:** Required

**Query Parameters:**
- `min_score` (float, default: 50.0) - Minimum match score (0-100)
- `status` (string) - Filter by status ("matched", "interested", "applied", "rejected", "hidden")
- `limit` (int, default: 50) - Number of matches
- `offset` (int, default: 0) - Pagination offset

**Example:**
```
GET /api/matches?min_score=70&status=matched&limit=10
```

**Response:** `200 OK`
```json
{
  "matches": [
    {
      "id": 456,
      "job_id": 123,
      "user_id": 1,
      "score": 85.5,
      "status": "matched",
      "reasoning": {
        "overall_score": 85.5,
        "skill_score": 90,
        "title_score": 85,
        "experience_score": 80,
        "work_type_score": 100,
        "location_score": 100,
        "salary_score": 75,
        "matching_skills": ["Python", "React", "PostgreSQL"],
        "missing_skills": ["Docker", "Kubernetes"],
        "weights": {
          "skills": 0.35,
          "title": 0.20,
          "experience": 0.15,
          "work_type": 0.10,
          "location": 0.10,
          "salary": 0.10
        }
      },
      "analysis": "You're a strong match for this role. Your Python and React experience aligns perfectly...",
      "job": {
        "id": 123,
        "title": "Senior Python Developer",
        "company": "Tech Startup Inc",
        "url": "https://remoteok.com/remote-jobs/12345",
        "salary_min": 100000,
        "salary_max": 150000,
        "location": "Remote",
        "tags": ["Python", "React", "PostgreSQL", "Docker"]
      },
      "cover_letter": "Dear Hiring Manager...",
      "cv_highlights": ["Built RESTful APIs...", "Led team of 3 developers..."],
      "created_at": "2024-12-18T10:00:00Z",
      "applied_at": null
    }
  ],
  "total": 15,
  "limit": 10,
  "offset": 0
}
```

**Notes:**
- Matches calculated based on skills, title, experience, preferences
- Jobs extracted with Claude Haiku (cached for 7 days)
- Results sorted by score DESC

---

### Update Match Status

Update application status for a match.

**Endpoint:** `PUT /api/matches/{match_id}/status`
**Authentication:** Required

**Request Body:**
```json
{
  "status": "applied"
}
```

**Valid statuses:** `"matched"`, `"interested"`, `"applied"`, `"rejected"`, `"hidden"`

**Response:** `200 OK`
```json
{
  "id": 456,
  "job_id": 123,
  "user_id": 1,
  "score": 85.5,
  "status": "applied",
  "applied_at": "2024-12-18T12:00:00Z",
  "updated_at": "2024-12-18T12:00:00Z"
}
```

**Errors:**
- `404 Not Found` - Match not found
- `403 Forbidden` - Match belongs to another user
- `422 Unprocessable Entity` - Invalid status value

---

## Generation

### Generate Cover Letter

Generate personalized cover letter for a job match.

**Endpoint:** `POST /api/matches/{match_id}/generate-cover-letter`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "cover_letter": "Dear Hiring Manager,\n\nI am excited to apply for the Senior Python Developer position...",
  "cached": false,
  "generated_at": "2024-12-18T12:00:00Z",
  "model": "claude-sonnet-4.5"
}
```

**Notes:**
- Uses Claude Sonnet 4.5 for quality generation
- Cached in Redis for 30 days (cache key: `cover_letter:{user_id}:{job_id}`)
- `cached: true` means instant response from Redis (<50ms)
- `cached: false` means new generation (~2-5 seconds)
- Cover letter stored in match record for future retrieval

**Errors:**
- `404 Not Found` - Match not found
- `403 Forbidden` - Match belongs to another user
- `500 Internal Server Error` - LLM generation failed

---

### Generate CV Highlights

Generate tailored CV bullet points for a job.

**Endpoint:** `POST /api/matches/{match_id}/generate-highlights`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "highlights": [
    "Developed RESTful APIs serving 1M+ requests/day using Python and FastAPI",
    "Led migration from monolithic architecture to microservices, reducing deployment time by 60%",
    "Implemented Redis caching layer, improving response times from 2s to <50ms"
  ],
  "cached": true,
  "generated_at": "2024-12-18T10:00:00Z",
  "model": "claude-haiku-4.5"
}
```

**Notes:**
- Uses Claude Haiku 4.5 for efficient extraction
- Cached in Redis for 30 days (cache key: `cv_highlights:{user_id}:{job_id}`)
- Returns 3-5 most relevant experience bullet points
- Tailored to job requirements with matching skills emphasized

---

### Regenerate Application Materials

Force regeneration of cover letter and CV highlights (clears cache).

**Endpoint:** `POST /api/matches/{match_id}/regenerate`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Application materials regenerated",
  "cover_letter": "Dear Hiring Manager...",
  "cv_highlights": ["...", "...", "..."],
  "cached": false,
  "generated_at": "2024-12-18T12:30:00Z"
}
```

**Notes:**
- Clears Redis cache for this match
- Generates fresh content with Claude API
- Useful when user updates their CV or profile
- Takes 3-7 seconds (both Haiku + Sonnet calls)

---

## Insights

### Get Skill Insights

Get market analysis and career recommendations based on skill gaps.

**Endpoint:** `GET /api/insights/skills`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "user_id": 1,
  "analysis_date": "2024-12-18T10:00:00Z",
  "jobs_analyzed": 500,
  "user_skills": ["Python", "React", "PostgreSQL", "FastAPI"],
  "skill_gaps": ["Docker", "Kubernetes", "AWS", "TypeScript"],
  "market_skills": {
    "Python": {
      "count": 350,
      "frequency": 0.70,
      "avg_salary": 120000,
      "jobs_with_salary": 250
    },
    "Docker": {
      "count": 300,
      "frequency": 0.60,
      "avg_salary": 125000,
      "jobs_with_salary": 220
    }
  },
  "recommendations": [
    {
      "skill": "Docker",
      "priority": "high",
      "reason": "Appears in 60% of matching jobs and complements your Python skills",
      "learning_effort": "low",
      "salary_impact": 15000,
      "frequency": 300
    },
    {
      "skill": "Kubernetes",
      "priority": "medium",
      "reason": "Common in senior roles, often paired with Docker",
      "learning_effort": "medium",
      "salary_impact": 20000,
      "frequency": 180
    }
  ]
}
```

**Notes:**
- Analysis based on all scraped jobs in database
- Recommendations prioritize high-frequency, high-impact skills
- Learning effort estimated based on skill relationships
- Salary impact calculated from job data with salary information

---

## Skills

### Get Popular Skills

Get list of popular skills from job market + custom user skills.

**Endpoint:** `GET /api/skills/popular`
**Authentication:** None (public)

**Query Parameters:**
- `limit` (int, default: 100) - Maximum number of skills to return

**Response:** `200 OK`
```json
{
  "skills": [
    "Python",
    "React",
    "TypeScript",
    "Docker",
    "Kubernetes",
    "PostgreSQL",
    "AWS",
    "Node.js",
    "GraphQL",
    "Redis"
  ],
  "source": "job_tags_and_custom_skills",
  "total": 250
}
```

**Notes:**
- Combines skills from job tags + custom_skills table
- Ordered by frequency (most common first)
- Deduplicated and normalized (case-insensitive)
- Used for autocomplete in Skills UI

---

### Add Custom Skill

Add a user-contributed skill (not in job market data).

**Endpoint:** `POST /api/skills/custom`
**Authentication:** Required

**Request Body:**
```json
{
  "skill": "Elixir"
}
```

**Response:** `201 Created`
```json
{
  "id": 42,
  "skill": "Elixir",
  "usage_count": 1,
  "created_at": "2024-12-18T12:00:00Z"
}
```

**Notes:**
- If skill already exists, increments `usage_count`
- Skill appears in `/api/skills/popular` for all users
- Case-insensitive matching
- Automatically added to user's profile skills

**Errors:**
- `422 Unprocessable Entity` - Skill name empty or too long

---

## Health

### Health Check

Check if backend is running.

**Endpoint:** `GET /health`
**Authentication:** None (public)

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-12-18T12:00:00Z"
}
```

---

### Database Health Check

Check database connectivity.

**Endpoint:** `GET /health/db`
**Authentication:** None (public)

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-12-18T12:00:00Z"
}
```

**Errors:**
- `503 Service Unavailable` - Database connection failed

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `400 Bad Request` - Invalid input or business logic error
- `401 Unauthorized` - Missing or invalid JWT token
- `403 Forbidden` - Authenticated but not authorized
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - External service unavailable

---

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `POST /api/profile/cv` | 5 requests/hour per IP |
| All other endpoints | No limit (planned: 100 req/min per user) |

---

## Authentication Flow

1. **Register:** `POST /auth/register` → Receive user object
2. **Login:** `POST /auth/login` → Receive JWT token
3. **Store token:** Save token in localStorage or secure cookie
4. **Include token:** Add `Authorization: Bearer <token>` header to all protected requests
5. **Logout:** `POST /auth/logout` + remove token from storage

**Example (JavaScript):**
```javascript
// Login
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { access_token } = await response.json();
localStorage.setItem('token', access_token);

// Authenticated request
const matches = await fetch('/api/matches', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

---

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Related Documentation

- **[ROADMAP.md](./ROADMAP.md)** - Project phases and implementation plan
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture and components
- **[SCHEMA.md](./SCHEMA.md)** - Database schema documentation
