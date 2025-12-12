// Job types
export interface Job {
  id: string
  source: 'remoteok' | 'weworkremotely' | 'linkedin'
  sourceId: string
  url: string
  title: string
  company: string
  description: string
  salaryMin?: number
  salaryMax?: number
  salaryCurrency: string
  location: string
  remoteType: 'full' | 'hybrid' | 'onsite'
  jobType: 'permanent' | 'contract' | 'freelance' | 'part-time'
  contractDuration?: string
  requirements?: JobRequirements
  tags: string[]
  scrapedAt: string
  expiresAt?: string
}

export interface JobRequirements {
  skills: string[]
  experienceYears?: number
  education?: string
  languages?: string[]
  other?: string[]
}

// Profile types
export interface Profile {
  id: string
  userId: string
  rawCvText?: string
  parsedCv?: ParsedCV
  skills: string[]
  experienceYears?: number
  preferences: UserPreferences
}

export interface ParsedCV {
  name?: string
  email?: string
  phone?: string
  summary?: string
  skills: string[]
  experience: WorkExperience[]
  education: Education[]
}

export interface WorkExperience {
  company: string
  title: string
  startDate?: string
  endDate?: string
  description?: string
}

export interface Education {
  institution: string
  degree: string
  field?: string
  endDate?: string
}

export interface UserPreferences {
  minSalary?: number
  maxSalary?: number
  currency: string
  jobTypes: string[]
  remoteTypes: string[]
  locations?: string[]
  excludeCompanies?: string[]
}

// Match types
export interface JobMatch {
  id: string
  userId: string
  jobId: string
  job: Job
  matchScore: number
  skillMatches: string[]
  skillGaps: string[]
  analysis?: MatchAnalysis
  status: 'new' | 'interested' | 'applied' | 'rejected' | 'hidden'
  coverLetter?: string
  cvHighlights?: string
  createdAt: string
  updatedAt: string
}

export interface MatchAnalysis {
  overallFit: string
  strengths: string[]
  concerns: string[]
  suggestions: string[]
}

// API response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface ApiError {
  error: string
  message: string
  details?: Record<string, unknown>
}
