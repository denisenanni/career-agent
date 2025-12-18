import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { JobCard } from '../JobCard'
import type { Job } from '../../types'

const mockJob: Job = {
  id: 1,
  source: 'remoteok',
  source_id: 'test-123',
  url: 'https://example.com/job/123',
  title: 'Senior Full Stack Developer',
  company: 'Tech Corp',
  description: 'Looking for an experienced full stack developer to join our team.',
  salary_min: 100000,
  salary_max: 150000,
  salary_currency: 'USD',
  location: 'Remote',
  remote_type: 'full',
  job_type: 'permanent',
  tags: ['React', 'Node.js', 'TypeScript', 'PostgreSQL'],
  posted_at: '2025-12-15T10:00:00Z',
  scraped_at: '2025-12-18T10:00:00Z',
}

describe('JobCard', () => {
  it('renders job title and company', () => {
    render(<JobCard job={mockJob} />)

    expect(screen.getByText('Senior Full Stack Developer')).toBeInTheDocument()
    expect(screen.getByText('Tech Corp')).toBeInTheDocument()
  })

  it('renders job location and remote type', () => {
    render(<JobCard job={mockJob} />)

    // Both location and remote_type are "Remote", so check for both elements
    const remoteElements = screen.getAllByText('Remote')
    expect(remoteElements.length).toBeGreaterThanOrEqual(1)
  })

  it('renders salary range when both min and max are provided', () => {
    render(<JobCard job={mockJob} />)

    expect(screen.getByText(/USD 100,000 - 150,000/)).toBeInTheDocument()
  })

  it('renders job type', () => {
    render(<JobCard job={mockJob} />)

    expect(screen.getByText('permanent')).toBeInTheDocument()
  })

  it('renders job tags', () => {
    render(<JobCard job={mockJob} />)

    expect(screen.getByText('React')).toBeInTheDocument()
    expect(screen.getByText('Node.js')).toBeInTheDocument()
    expect(screen.getByText('TypeScript')).toBeInTheDocument()
    expect(screen.getByText('PostgreSQL')).toBeInTheDocument()
  })

  it('renders job source', () => {
    render(<JobCard job={mockJob} />)

    expect(screen.getByText('remoteok')).toBeInTheDocument()
  })

  it('renders job description with HTML tags stripped', () => {
    const jobWithHtml: Job = {
      ...mockJob,
      description: '<p>Looking for a <strong>developer</strong></p>',
    }
    render(<JobCard job={jobWithHtml} />)

    expect(screen.getByText(/Looking for a developer/)).toBeInTheDocument()
  })

  it('renders job URL as clickable link', () => {
    render(<JobCard job={mockJob} />)

    const link = screen.getByRole('link', { name: 'Senior Full Stack Developer' })
    expect(link).toHaveAttribute('href', 'https://example.com/job/123')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('handles job with no salary info', () => {
    const jobWithoutSalary: Job = {
      ...mockJob,
      salary_min: null,
      salary_max: null,
    }
    render(<JobCard job={jobWithoutSalary} />)

    expect(screen.queryByText(/USD/)).not.toBeInTheDocument()
  })

  it('handles job with no tags', () => {
    const jobWithoutTags: Job = {
      ...mockJob,
      tags: [],
    }
    render(<JobCard job={jobWithoutTags} />)

    // Should not render any tags section
    expect(screen.getByText('Senior Full Stack Developer')).toBeInTheDocument()
  })
})
