import { getRecruiterToken, getCandidateToken } from "./auth"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type RequestOptions = RequestInit & {
  token?: string
  isRecruiter?: boolean
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { token, isRecruiter, headers, ...customConfig } = options

    const defaultHeaders: HeadersInit = {
      "Content-Type": "application/json",
    }

    if (token) {
      defaultHeaders["Authorization"] = `Bearer ${token}`
    } else if (isRecruiter) {
      const recruiterToken = getRecruiterToken()
      if (recruiterToken) {
        defaultHeaders["Authorization"] = `Bearer ${recruiterToken}`
      }
    } else {
      // Default to candidate token if present and not specified otherwise
      const candidateToken = getCandidateToken()
      if (candidateToken) {
        // Candidate tokens are often passed as query params or custom headers depending on implementation
        // For this backend, let's assume Bearer for consistency or handle as needed
        // The backend uses HMAC token often in query param or body, but let's support Bearer if updated
        // For now, we'll just leave it to the caller to pass explicit token if needed for candidates
      }
    }

    const config: RequestInit = {
      ...customConfig,
      headers: {
        ...defaultHeaders,
        ...headers,
      },
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config)

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}))
      throw new Error(errorBody.detail || response.statusText)
    }

    return response.json()
  }

  get<T>(endpoint: string, options?: RequestOptions) {
    return this.request<T>(endpoint, { ...options, method: "GET" })
  }

  post<T>(endpoint: string, body: any, options?: RequestOptions) {
    return this.request<T>(endpoint, { ...options, method: "POST", body: JSON.stringify(body) })
  }

  put<T>(endpoint: string, body: any, options?: RequestOptions) {
    return this.request<T>(endpoint, { ...options, method: "PUT", body: JSON.stringify(body) })
  }

  delete<T>(endpoint: string, options?: RequestOptions) {
    return this.request<T>(endpoint, { ...options, method: "DELETE" })
  }
  
  // Helper for file uploads which need different headers
  async upload<T>(endpoint: string, formData: FormData, options: RequestOptions = {}): Promise<T> {
     const { token, isRecruiter, headers, ...customConfig } = options
     
     const defaultHeaders: Record<string, string> = {}
     if (isRecruiter) {
        const t = getRecruiterToken()
        if (t) defaultHeaders["Authorization"] = `Bearer ${t}`
     }

     const config: RequestInit = {
       ...customConfig,
       method: "POST",
       body: formData,
       headers: {
         ...defaultHeaders,
         ...headers,
         // Do NOT set Content-Type for FormData, browser does it with boundary
       }
     }
     
     const response = await fetch(`${this.baseUrl}${endpoint}`, config)
     
     if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody.detail || response.statusText)
     }
     
     return response.json()
  }
}

export const api = new ApiClient(API_BASE_URL)
