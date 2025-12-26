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
- [User-Submitted Jobs](#user-submitted-jobs)
- [Matches](#matches)
- [Generation](#generation)
- [Insights](#insights)
- [Skills](#skills)
- [Admin](#admin)
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
- Token expires in 24 hours
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
    "remote_types": ["full", "hybrid"],
    "min_salary": 120000,
    "job_types": ["permanent"],
    "preferred_countries": ["United States", "Canada", "Remote"],
    "eligible_regions": ["US", "Canada", "Worldwide"],
    "needs_visa_sponsorship": false
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

**Preference Fields:**
- `target_roles` (array): Target job titles
- `remote_types` (array): "full", "hybrid", "onsite"
- `min_salary` (number): Minimum acceptable salary
- `job_types` (array): "permanent", "contract", "freelance", "part-time"
- `preferred_countries` (array): Preferred work locations
- `eligible_regions` (array): Regions where you can legally work (e.g., ["US", "EU", "Worldwide"])
- `needs_visa_sponsorship` (boolean): Whether you need visa sponsorship

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
      "eligible_regions": ["Worldwide"],
      "visa_sponsorship": null,
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

**Employment Eligibility Fields:**
- `eligible_regions` (array): Geographic regions where candidates can apply (e.g., ["US", "EU", "Worldwide"])
- `visa_sponsorship` (integer): Visa sponsorship availability (0 = no, 1 = yes, null = not specified)
- These fields are extracted from job descriptions using AI during matching

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

## User-Submitted Jobs

User-submitted jobs allow users to paste job postings they found elsewhere and add them to their profile for matching and tracking.

### Parse Job Text

Parse pasted job text using AI to extract structured information.

**Endpoint:** `POST /api/user-jobs/parse`
**Authentication:** Required

**Request Body:**
```json
{
  "job_text": "Senior Python Developer\nTechCorp Inc. - Remote\n\nWe're looking for an experienced Python developer...\n\nRequirements:\n- 5+ years of Python experience\n- Django and FastAPI\n- PostgreSQL\n\nSalary: $120,000 - $160,000 USD\nLocation: Remote (US only)\n\nApply at: https://techcorp.com/careers/123"
}
```

**Response:** `200 OK`
```json
{
  "title": "Senior Python Developer",
  "company": "TechCorp Inc.",
  "description": "We're looking for an experienced Python developer to join our team.",
  "url": "https://techcorp.com/careers/123",
  "location": "Remote (US only)",
  "remote_type": "full",
  "job_type": "permanent",
  "salary_min": 120000,
  "salary_max": 160000,
  "salary_currency": "USD",
  "tags": ["Python", "Django", "FastAPI", "PostgreSQL"]
}
```

**Errors:**
- `400 Bad Request` - Job text too short (minimum 50 characters)
- `500 Internal Server Error` - AI parsing failed

**Notes:**
- Uses Claude Haiku for extraction
- User can review and edit extracted data before saving
- Automatically extracts URL if present in text

---

### Create User Job

Create a new user-submitted job posting.

**Endpoint:** `POST /api/user-jobs`
**Authentication:** Required

**Request Body:**
```json
{
  "title": "Senior Python Developer",
  "company": "TechCorp Inc.",
  "description": "We're looking for an experienced Python developer...",
  "url": "https://techcorp.com/careers/123",
  "location": "Remote (US only)",
  "remote_type": "full",
  "job_type": "permanent",
  "salary_min": 120000,
  "salary_max": 160000,
  "salary_currency": "USD",
  "tags": ["Python", "Django", "FastAPI", "PostgreSQL"]
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Senior Python Developer",
  "company": "TechCorp Inc.",
  "description": "We're looking for an experienced Python developer...",
  "url": "https://techcorp.com/careers/123",
  "source": "user_submitted",
  "tags": ["Python", "Django", "FastAPI", "PostgreSQL"],
  "salary_min": 120000,
  "salary_max": 160000,
  "salary_currency": "USD",
  "location": "Remote (US only)",
  "remote_type": "full",
  "job_type": "permanent",
  "created_at": "2024-12-18T12:00:00Z",
  "updated_at": "2024-12-18T12:00:00Z"
}
```

**Errors:**
- `400 Bad Request` - Duplicate job (same user, company, title)
- `422 Unprocessable Entity` - Missing required fields (title, description)

**Notes:**
- Automatically creates a match for the user with min_score=0
- Only required fields: `title` and `description`
- Company can be null for unknown employers

---

### List User Jobs

Get all jobs submitted by the current user.

**Endpoint:** `GET /api/user-jobs`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "jobs": [
    {
      "id": 1,
      "user_id": 1,
      "title": "Senior Python Developer",
      "company": "TechCorp Inc.",
      "description": "We're looking for...",
      "url": "https://techcorp.com/careers/123",
      "source": "user_submitted",
      "tags": ["Python", "Django", "FastAPI"],
      "salary_min": 120000,
      "salary_max": 160000,
      "salary_currency": "USD",
      "location": "Remote (US only)",
      "remote_type": "full",
      "job_type": "permanent",
      "created_at": "2024-12-18T12:00:00Z",
      "updated_at": "2024-12-18T12:00:00Z"
    }
  ],
  "total": 1
}
```

**Notes:**
- Returns jobs ordered by creation date (newest first)
- Only returns jobs belonging to the authenticated user

---

### Get User Job

Get details of a specific user-submitted job.

**Endpoint:** `GET /api/user-jobs/{job_id}`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Senior Python Developer",
  "company": "TechCorp Inc.",
  "description": "We're looking for an experienced Python developer...",
  "url": "https://techcorp.com/careers/123",
  "source": "user_submitted",
  "tags": ["Python", "Django", "FastAPI", "PostgreSQL"],
  "salary_min": 120000,
  "salary_max": 160000,
  "salary_currency": "USD",
  "location": "Remote (US only)",
  "remote_type": "full",
  "job_type": "permanent",
  "created_at": "2024-12-18T12:00:00Z",
  "updated_at": "2024-12-18T12:00:00Z"
}
```

**Errors:**
- `404 Not Found` - Job not found or belongs to another user

---

### Update User Job

Update a user-submitted job.

**Endpoint:** `PUT /api/user-jobs/{job_id}`
**Authentication:** Required

**Request Body:**
```json
{
  "title": "Updated Title",
  "salary_min": 130000,
  "tags": ["Python", "FastAPI", "PostgreSQL", "Docker"]
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Updated Title",
  "company": "TechCorp Inc.",
  "description": "We're looking for...",
  "url": "https://techcorp.com/careers/123",
  "source": "user_submitted",
  "tags": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "salary_min": 130000,
  "salary_max": 160000,
  "salary_currency": "USD",
  "location": "Remote (US only)",
  "remote_type": "full",
  "job_type": "permanent",
  "created_at": "2024-12-18T12:00:00Z",
  "updated_at": "2024-12-18T13:00:00Z"
}
```

**Notes:**
- All fields are optional (partial updates supported)
- Only the owner can update their jobs

**Errors:**
- `404 Not Found` - Job not found or belongs to another user
- `400 Bad Request` - Duplicate title/company combination

---

### Delete User Job

Delete a user-submitted job.

**Endpoint:** `DELETE /api/user-jobs/{job_id}`
**Authentication:** Required

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Job not found or belongs to another user

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

### Refresh Matches (Async)

Trigger background match calculation against all jobs.

**Endpoint:** `POST /api/matches/refresh`
**Authentication:** Required (Admin only)
**Rate Limit:** 5 requests per hour

**Response:** `200 OK`
```json
{
  "status": "processing",
  "message": "Match refresh started. Poll /api/matches/refresh/status for updates."
}
```

**Alternative Response (if already running):**
```json
{
  "status": "already_processing",
  "message": "Match refresh is already in progress. Check status endpoint for updates."
}
```

**Notes:**
- This is an **asynchronous** operation - returns immediately
- Processing happens in background using FastAPI BackgroundTasks
- Poll `/api/matches/refresh/status` to check completion
- Status tracked in Redis with 1-hour TTL

---

### Get Refresh Status

Poll for match refresh completion status.

**Endpoint:** `GET /api/matches/refresh/status`
**Authentication:** Required

**Response:** `200 OK`

**When no refresh has been started:**
```json
{
  "status": "none",
  "message": "No match refresh in progress or recently completed."
}
```

**When processing:**
```json
{
  "status": "processing",
  "message": "Calculating matches against all jobs...",
  "updated_at": "2024-12-18T12:00:00Z"
}
```

**When completed:**
```json
{
  "status": "completed",
  "message": "Found 25 matches (10 new)",
  "result": {
    "matches_created": 10,
    "matches_updated": 15,
    "total_jobs_processed": 500
  },
  "updated_at": "2024-12-18T12:05:00Z"
}
```

**When failed:**
```json
{
  "status": "failed",
  "message": "Match refresh failed: Database connection error",
  "updated_at": "2024-12-18T12:01:00Z"
}
```

**Status Values:**
- `none` - No refresh started or status expired (1-hour TTL)
- `pending` - Refresh queued
- `processing` - Refresh in progress
- `completed` - Refresh finished successfully
- `failed` - Refresh failed with error

**Frontend Integration:**
1. Call `POST /api/matches/refresh` to start
2. Poll `GET /api/matches/refresh/status` every 2-3 seconds
3. When `status === "completed"`, show toast and refresh matches list
4. When `status === "failed"`, show error message

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

## Admin

Admin endpoints require authentication as an admin user (currently user with id=1).

### Get Cache Statistics

Get Redis cache statistics and cost savings.

**Endpoint:** `GET /api/admin/cache/stats`
**Authentication:** Required (Admin only)

**Response:** `200 OK`
```json
{
  "available": true,
  "summary": {
    "total_hits": 1250,
    "total_misses": 150,
    "total_requests": 1400,
    "hit_rate_percent": 89.3,
    "total_savings_usd": 187.50
  },
  "breakdown": {
    "cover_letter": {
      "hits": 800,
      "misses": 50,
      "total_requests": 850,
      "hit_rate_percent": 94.1,
      "cost_per_miss_usd": 0.15,
      "savings_usd": 120.00
    },
    "cv_highlights": {
      "hits": 200,
      "misses": 30,
      "total_requests": 230,
      "hit_rate_percent": 87.0,
      "cost_per_miss_usd": 0.01,
      "savings_usd": 2.00
    },
    "cv_parse": {
      "hits": 150,
      "misses": 40,
      "total_requests": 190,
      "hit_rate_percent": 78.9,
      "cost_per_miss_usd": 0.01,
      "savings_usd": 1.50
    },
    "job_extract": {
      "hits": 100,
      "misses": 30,
      "total_requests": 130,
      "hit_rate_percent": 76.9,
      "cost_per_miss_usd": 0.005,
      "savings_usd": 0.50
    }
  },
  "storage": {
    "memory_used": "12.5M",
    "key_counts": {
      "cover_letters": 850,
      "cv_highlights": 230,
      "cv_parses": 190,
      "job_extracts": 500
    },
    "total_keys": 1770
  }
}
```

**Errors:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin user
- `503 Service Unavailable` - Redis not available

**Notes:**
- Tracks metrics by category (cover_letter, cv_highlights, cv_parse, job_extract)
- Cost savings calculated based on estimated LLM API costs per operation
- Memory usage shows actual Redis memory consumption

---

### Reset Cache Metrics

Reset cache hit/miss counters (does NOT clear cached data).

**Endpoint:** `POST /api/admin/cache/reset-metrics`
**Authentication:** Required (Admin only)

**Response:** `200 OK`
```json
{
  "message": "Cache metrics reset successfully"
}
```

**Errors:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin user
- `503 Service Unavailable` - Redis not available

**Notes:**
- Only resets metric counters (hits, misses, sets)
- Does NOT clear cached cover letters, CV parses, etc.
- Useful for starting fresh metrics tracking

---

### List Users

Get all registered users (newest first).

**Endpoint:** `GET /api/admin/users`
**Authentication:** Required (Admin only)

**Response:** `200 OK`
```json
{
  "users": [
    {
      "id": 3,
      "email": "newuser@example.com",
      "full_name": "New User",
      "is_active": true,
      "is_admin": false,
      "created_at": "2024-12-20T10:00:00Z"
    },
    {
      "id": 2,
      "email": "user2@example.com",
      "full_name": "User Two",
      "is_active": true,
      "is_admin": false,
      "created_at": "2024-12-18T10:00:00Z"
    },
    {
      "id": 1,
      "email": "admin@example.com",
      "full_name": "Admin User",
      "is_active": true,
      "is_admin": true,
      "created_at": "2024-12-15T10:00:00Z"
    }
  ],
  "total": 3
}
```

**Errors:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin user

---

### Update User

Update user properties (activate/deactivate, grant/revoke admin).

**Endpoint:** `PUT /api/admin/users/{user_id}`
**Authentication:** Required (Admin only)

**Request Body:**
```json
{
  "is_active": false,
  "is_admin": true
}
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "email": "user2@example.com",
  "full_name": "User Two",
  "is_active": false,
  "is_admin": true,
  "created_at": "2024-12-18T10:00:00Z"
}
```

**Errors:**
- `400 Bad Request` - Cannot modify your own account
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin user
- `404 Not Found` - User not found

**Notes:**
- All fields are optional (partial updates supported)
- Admin cannot modify their own account via this endpoint
- User cache is invalidated immediately after update

---

### Add Email to Allowlist

Add an email to the registration allowlist (when REGISTRATION_MODE=allowlist).

**Endpoint:** `POST /api/admin/allowlist`
**Authentication:** Required (Admin only)

**Request Body:**
```json
{
  "email": "newuser@example.com"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "added_by": 1,
  "created_at": "2024-12-18T12:00:00Z"
}
```

**Errors:**
- `400 Bad Request` - Email already on allowlist
- `403 Forbidden` - Not an admin user
- `422 Unprocessable Entity` - Invalid email format

---

### List Allowed Emails

Get all emails on the registration allowlist.

**Endpoint:** `GET /api/admin/allowlist`
**Authentication:** Required (Admin only)

**Response:** `200 OK`
```json
{
  "allowed_emails": [
    {
      "id": 1,
      "email": "user1@example.com",
      "added_by": 1,
      "created_at": "2024-12-18T10:00:00Z"
    },
    {
      "id": 2,
      "email": "user2@example.com",
      "added_by": 1,
      "created_at": "2024-12-18T11:00:00Z"
    }
  ],
  "total": 2
}
```

---

### Remove Email from Allowlist

Remove an email from the registration allowlist.

**Endpoint:** `DELETE /api/admin/allowlist/{email}`
**Authentication:** Required (Admin only)

**Response:** `204 No Content`

**Errors:**
- `403 Forbidden` - Not an admin user
- `404 Not Found` - Email not on allowlist

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
| `POST /auth/register` | 5 requests/hour per IP |
| `POST /auth/login` | 10 requests/minute per IP |
| `POST /api/profile/cv` | 10 requests/hour per IP |
| `POST /api/matches/refresh` | 5 requests/hour per IP |
| `POST /api/user-jobs/parse` | 10 requests/hour per IP |

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
