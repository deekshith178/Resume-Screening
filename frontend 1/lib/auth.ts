// Client-side auth utilities

export function getRecruiterToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("recruiter_token")
}

export function getCandidateToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("candidate_token")
}

export function setRecruiterToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("recruiter_token", token)
  }
}

export function setCandidateToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("candidate_token", token)
  }
}

export function clearRecruiterToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("recruiter_token")
  }
}

export function clearCandidateToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("candidate_token")
  }
}

export function isRecruiterLoggedIn(): boolean {
  return !!getRecruiterToken()
}

export function isCandidateLoggedIn(): boolean {
  return !!getCandidateToken()
}
