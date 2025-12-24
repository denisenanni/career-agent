

#DONE

# Task: Profile Page UX Improvements

## Goal

Improve the Profile page UX by reducing visual clutter and making important information more visible.

---

## Issues to Fix

1. **Auto-save indicator is hard to spot** - Can appear off-screen when user scrolls
2. **Upload CV section takes too much space** - Even when CV is already uploaded
3. **Checkbox lists are overwhelming** - Too many options visible at once
4. **Parsed CV Data section is buried** - Most important info is at the bottom, easy to miss

---

## Changes

### 1. Global Toast Notification System (Reusable)

Create a reusable toast notification system for use throughout the app - auto-save, API responses, user actions, errors, etc.

**Requirements:**
- Fixed position (bottom-right corner), always visible regardless of scroll
- Multiple toast types: success, error, warning, info
- Auto-dismiss after 3 seconds (configurable)
- Stack multiple toasts if needed
- Accessible from anywhere in the app via hook or context

**Example usage:**
```tsx
// Auto-save
toast.success('Changes saved')

// API responses
toast.success('Cover letter generated')
toast.error('Failed to fetch jobs')

// User actions
toast.info('Job added to matches')
toast.warning('You have unsaved changes')
```

**Implementation options:**
1. `react-hot-toast` - lightweight, easy to use (recommended)
2. Custom implementation with Context + Portal

**Setup with react-hot-toast:**
```tsx
// App.tsx
import { Toaster } from 'react-hot-toast'

function App() {
  return (
    <>
      <Toaster position="bottom-right" />
      {/* rest of app */}
    </>
  )
}

// Anywhere in the app
import toast from 'react-hot-toast'
toast.success('It works!')
```

**Use for:**
- Auto-save confirmations
- API success/error responses
- Form submissions
- Job scraping status
- Cover letter generation
- Any user feedback

---

### 2. Collapse Upload CV Section When CV Exists

**Current:** Large dropzone always visible, even when CV uploaded

**New behavior:**
- If CV is uploaded, show compact version:
  ```
  📄 CV-Nanni-Software-Dev.pdf (uploaded 21/12/2025)  [Replace]
  ```
- "Replace" button opens file picker
- Only show full dropzone when no CV is uploaded

**Component structure:**
```tsx
{hasCV ? (
  <CompactCVDisplay filename={cv.filename} date={cv.uploadedAt} onReplace={handleReplace} />
) : (
  <CVDropzone onUpload={handleUpload} />
)}
```

---

### 3. Collapsible Checkbox Groups

Convert all checkbox lists to expandable/collapsible sections.

**Current:** All checkboxes visible, overwhelming

**New:**
```
▶ Job Types (2 selected)
▶ Remote Work Preference (1 selected)  
▶ Preferred Countries (2 selected)
▶ Employment Eligibility (1 selected)
```

**Behavior:**
- Show selected count in header
- Collapsed by default
- Click header to expand/collapse
- Optionally remember expand/collapse state in localStorage

**Apply to:**
- Job Types
- Remote Work Preference
- Preferred Countries/Locations
- Employment Eligibility

---

### 4. Reorder Page Layout

**Current order:**
1. Profile Information
2. Upload CV + Job Preferences (side by side)
3. Parsed CV Data (bottom, easy to miss)

**New order:**
1. Profile Information (compact: name, experience, CV file status)
2. Parsed CV Data (skills, experience, education) - THE MAIN CONTENT
3. Job Preferences (collapsible sections)

This puts the most important information (parsed CV) front and center.

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/pages/ProfilePage.tsx` | Reorder sections, integrate toast |
| `frontend/src/components/CVUpload.tsx` | Add compact mode when CV exists |
| `frontend/src/components/PreferencesForm.tsx` | Add collapsible checkbox groups |
| `frontend/src/components/Toast.tsx` | New component (or use react-hot-toast) |
| `frontend/src/hooks/useAutoSave.ts` | Trigger toast on save success/error |

---

## Implementation Notes

- Use `react-hot-toast` for quick implementation, or build custom if you want more control
- For collapsible sections, can use simple useState or a small component:
  ```tsx
  <CollapsibleSection title="Job Types" selectedCount={2}>
    {/* checkboxes */}
  </CollapsibleSection>
  ```
- Test on mobile - collapsible sections help a lot on small screens

---

## Acceptance Criteria

- [ ] Toast appears on save (visible regardless of scroll position)
- [ ] CV upload section is compact when CV exists
- [ ] All checkbox groups are collapsible
- [ ] Parsed CV Data is above  Job Preferences
- [ ] Page feels less cluttered and more scannable




#TODO
# Task: Add Creative & 3D Job Board Scrapers

## Goal

Expand job sources beyond tech/software to include creative, design, and 3D job boards. The existing matching algorithm will handle relevance - users with creative skills will match creative jobs.

---

## Job Boards to Add

### Priority 1 (Easiest)

| Site | Type | Notes |
|------|------|-------|
| **Dribbble Jobs** | API | Has public API, design/UI/UX focused |
| **Authentic Jobs** | RSS | Has RSS feed, design + dev |

### Priority 2 (Scraping Required)

| Site | Type | Notes |
|------|------|-------|
| **ArtStation Jobs** | Scrape | 3D, game art, VFX, concept art |
| **Behance Jobs** | Scrape | Adobe's creative job board |

### Priority 3 (Future)

- Motionographer (motion design)
- Creativepool
- Working Not Working
- Krop

---

## Implementation

### 1. Scraper Base Pattern

Follow existing RemoteOK scraper pattern in `backend/app/scrapers/`:

```python
# backend/app/scrapers/dribbble.py
async def scrape_dribbble() -> list[dict]:
    """
    Scrape Dribbble jobs API
    Returns normalized job format
    """
    # Fetch from API/RSS/HTML
    # Normalize to standard job format
    # Return list of jobs
```

### 2. Standard Job Format

All scrapers must return jobs in this format:

```python
{
    "source": "dribbble",  # unique source identifier
    "source_id": "123456",  # unique ID from source
    "title": "Senior 3D Artist",
    "company": "Studio Name",
    "description": "Full job description...",
    "url": "https://dribbble.com/jobs/123456",
    "location": "Remote",
    "salary_min": None,
    "salary_max": None,
    "tags": ["3D", "Blender", "Maya"],
    "remote_type": "full",  # full, hybrid, onsite
    "posted_at": datetime,
}
```

### 3. Add to Scraper Service

Update `backend/app/services/scraper.py`:

```python
from app.scrapers import remoteok, dribbble, artstation

async def scrape_all_sources():
    """Run all enabled scrapers"""
    jobs = []
    jobs.extend(await remoteok.scrape())
    jobs.extend(await dribbble.scrape())
    jobs.extend(await artstation.scrape())
    # ... dedupe and save to DB
```

### 4. Deduplication

Jobs are deduped by `(source, source_id)` composite key - already implemented.

---

## Scraper Details

### Dribbble Jobs

- URL: https://dribbble.com/jobs
- Check for API: https://dribbble.com/api or scrape HTML
- Categories: Product Design, UI/UX, Brand, Illustration, Animation

### Authentic Jobs

- URL: https://authenticjobs.com/
- Has RSS: https://authenticjobs.com/rss/index.xml
- Categories: Design, Development, Creative

### ArtStation Jobs

- URL: https://www.artstation.com/jobs
- Will need HTML scraping
- Categories: 3D, Concept Art, Game Art, VFX, Animation

### Behance Jobs

- URL: https://www.behance.net/joblist
- Adobe-owned, may need scraping
- Categories: Graphic Design, UI/UX, 3D, Motion

---

## Files to Create/Modify

**Create:**
- `backend/app/scrapers/dribbble.py`
- `backend/app/scrapers/authentic_jobs.py`
- `backend/app/scrapers/artstation.py`
- `backend/app/scrapers/behance.py`

**Modify:**
- `backend/app/services/scraper.py` - Add new sources
- `backend/app/routers/jobs.py` - Maybe add source filter param

---

## Testing

1. Run each scraper individually and verify job format
2. Check deduplication works (run twice, no duplicates)
3. Verify jobs appear in /jobs endpoint
4. Test that creative jobs match creative CVs (not dev CVs)

---

## Notes

- No UI changes needed - matching algorithm handles relevance
- No new database columns needed
- Start with Dribbble (has API), then add others
- Be respectful with scraping - add delays, respect robots.txt