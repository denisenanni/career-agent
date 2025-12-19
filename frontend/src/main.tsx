import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { APIError } from './api/client'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      // Smart retry logic: retry on network errors, not on client errors
      retry: (failureCount, error) => {
        // Don't retry on client errors (4xx)
        if (error instanceof APIError && error.status && error.status >= 400 && error.status < 500) {
          return false
        }
        // Retry up to 2 times for network errors and server errors
        return failureCount < 2
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
    },
    mutations: {
      // Don't retry mutations by default (can be overridden per mutation)
      retry: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)
