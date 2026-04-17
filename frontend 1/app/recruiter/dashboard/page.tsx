"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Upload, Search, Settings, MoreHorizontal } from "lucide-react"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { toast } from "sonner"
import RecruiterHeader from "@/components/recruiter/recruiter-header"
import ScoreWeights from "@/components/recruiter/score-weights"
import JobSelector from "@/components/recruiter/job-selector"
import AdvancedFilters from "@/components/recruiter/advanced-filters"
import BatchOperations from "@/components/recruiter/batch-operations"
import CandidateDetailModal from "@/components/recruiter/candidate-detail-modal"
import CandidateList from "@/components/recruiter/candidate-list"

interface Candidate {
  id: string
  name: string
  email: string
  score: number
  status: "shortlisted" | "rejected" | "pending"
  skills: string[]
  experience: number
  hybrid: boolean
  components?: {
    normalized_similarity?: number
    E_norm?: number
    P_norm?: number
    C_norm?: number
  }
}



export default function RecruiterDashboard() {
  const [selectedJob, setSelectedJob] = useState<string>("")
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [weights, setWeights] = useState<Record<string, number>>({
    skills: 50,
    experience: 25,
    projects: 15,
    certificates: 10,
  })
  const [filters, setFilters] = useState({
    scoreRange: [0, 100],
    skills: [] as string[],
    experienceRange: [0, 20],
    hybrid: false,
    status: [] as string[],
  })
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [isLoadingCandidates, setIsLoadingCandidates] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)

  // Fetch candidates function
  const fetchCandidates = useCallback(async () => {
    setFetchError(null)
    // Guard against "undefined" string which might come from select component issues
    if (!selectedJob || selectedJob === "_no_jobs" || selectedJob === "undefined") {
      setCandidates([])
      return
    }

    setIsLoadingCandidates(true)
    try {
      const token = localStorage.getItem("recruiter_token")
      if (!token) {
        setFetchError("No auth token found")
        return
      }

      const res = await fetch(`/api/jobs/${selectedJob}/shortlist`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (res.ok) {
        const data = await res.json()
        console.log("Fetched candidates:", data)
        // Map backend data to frontend Candidate interface
        const mappedCandidates: Candidate[] = data.candidates.map((item: any) => {
          let skills: string[] = []
          try {
            if (Array.isArray(item.skills)) {
              skills = item.skills
            } else if (typeof item.skills === 'string') {
              // Handle potential double encoding or plain string
              if (item.skills.startsWith('[')) {
                skills = JSON.parse(item.skills)
              } else {
                skills = [item.skills]
              }
            }
          } catch (e) {
            console.error("Error parsing skills for candidate", item.candidate_id, e)
            skills = []
          }

          // Map backend status to frontend status
          // is_selected: true → "shortlisted"
          // is_selected: false && is_override: true → "rejected" (explicitly rejected)
          // is_selected: false && is_override: false → "pending" (not yet decided)
          let status: Candidate["status"] = "pending"
          if (item.is_selected) {
            status = "shortlisted"
          } else if (item.is_override) {
            status = "rejected"
          }

          return {
            id: item.candidate_id,
            name: item.name || "Unknown Candidate",
            email: item.email,
            score: Math.round(item.score * 10) / 10,
            status: status,
            skills: skills,
            experience: 0,
            hybrid: false,
            components: item.components || {},
          }
        })
        setCandidates(mappedCandidates)
      } else {
        const errText = await res.text()
        setFetchError(`Fetch failed: ${res.status} ${errText}`)
      }
    } catch (err: any) {
      console.error("Failed to fetch candidates:", err)
      setFetchError(`Network error: ${err.message}`)
    } finally {
      setIsLoadingCandidates(false)
    }
  }, [selectedJob])

  // Fetch candidates when job changes
  useEffect(() => {
    fetchCandidates()
  }, [fetchCandidates])

  const handleJobSelect = (jobId: string) => {
    setSelectedJob(jobId)
  }

  // Filter and search candidates
  const filteredCandidates = candidates.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.email.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesScore = c.score >= filters.scoreRange[0] && c.score <= filters.scoreRange[1]
    const matchesExperience = c.experience >= filters.experienceRange[0] && c.experience <= filters.experienceRange[1]
    const matchesSkills = filters.skills.length === 0 || filters.skills.some((skill) => c.skills.includes(skill))
    const matchesStatus = filters.status.length === 0 || filters.status.includes(c.status)
    const matchesHybrid = !filters.hybrid || c.hybrid

    return matchesSearch && matchesScore && matchesExperience && matchesSkills && matchesStatus && matchesHybrid
  })

  const handleStatusChange = async (id: string, status: Candidate["status"]) => {
    if (!selectedJob || selectedJob === "_no_jobs" || selectedJob === "undefined") {
      toast.error("Please select a job first")
      return
    }

    // For "pending", just update local state (can't clear override via API currently)
    if (status === "pending") {
      setCandidates(candidates.map((c) => (c.id === id ? { ...c, status } : c)))
      toast.info("Status updated locally. Note: This won't persist after refresh.")
      return
    }

    // Map frontend status to backend is_selected boolean
    const isSelected = status === "shortlisted"

    try {
      const token = localStorage.getItem("recruiter_token")
      if (!token) {
        toast.error("Please log in again")
        window.location.href = "/auth?tab=recruiter"
        return
      }

      const response = await fetch(`/api/jobs/${selectedJob}/override`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          candidate_id: id,
          is_selected: isSelected,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        // Update local state optimistically
        setCandidates(candidates.map((c) => (c.id === id ? { ...c, status } : c)))
        
        // Show success message
        const statusMessage = status === "shortlisted" ? "shortlisted" : "rejected"
        toast.success(`Candidate ${statusMessage} successfully`)
        
        // Refresh the candidate list to ensure consistency with backend
        fetchCandidates()
      } else {
        let errorMessage = "Failed to update candidate status"
        try {
          const errorData = await response.json()
          errorMessage = errorData.error || errorData.detail || errorMessage
        } catch (e) {
          // If response is not JSON, try to get text
          try {
            const errorText = await response.text()
            if (errorText) errorMessage = errorText
          } catch (e2) {
            // Fallback to status text
            errorMessage = response.statusText || errorMessage
          }
        }
        console.error("Status update failed:", response.status, errorMessage)
        toast.error(errorMessage)
      }
    } catch (error: any) {
      console.error("Failed to update candidate status:", error)
      const errorMessage = error?.message || error?.error || "Network error. Please try again."
      toast.error(errorMessage)
    }
  }

  const toggleSelectCandidate = (id: string) => {
    setSelectedCandidates((prev) => (prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]))
  }

  const toggleSelectAll = () => {
    if (selectedCandidates.length === filteredCandidates.length) {
      setSelectedCandidates([])
    } else {
      setSelectedCandidates(filteredCandidates.map((c) => c.id))
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setUploadedFiles(Array.from(e.target.files))
    }
  }

  const handleProcessResumes = async () => {
    if (uploadedFiles.length === 0) {
      alert("Please upload at least one resume")
      return
    }
    if (!selectedJob) {
      alert("Please select a job position")
      return
    }

    setIsProcessing(true)

    try {
      // Get token from localStorage
      const token = localStorage.getItem("recruiter_token")

      if (!token) {
        alert("Please log in again")
        window.location.href = "/auth?tab=recruiter"
        return
      }

      // Create FormData with files and job_id
      const formData = new FormData()
      uploadedFiles.forEach(file => {
        formData.append('files', file)
      })
      formData.append('job_id', selectedJob)

      // Map frontend weights to backend weights (w_S, w_E, w_P, w_C)
      const backendWeights = {
        w_S: weights.skills,
        w_E: weights.experience,
        w_P: weights.projects,
        w_C: weights.certificates,
      }
      formData.append('weights', JSON.stringify(backendWeights))

      // Call backend API through frontend proxy
      const response = await fetch('/api/process-resumes', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.error || 'Failed to process resumes')
      }

      // Show success message with details
      const successCount = result.success || 0
      const failedCount = result.failed || 0

      let message = `Successfully processed ${successCount} resume(s)!`
      if (failedCount > 0) {
        message += `\n${failedCount} resume(s) failed to process.`
      }

      alert(message)

      // Clear uploaded files
      setUploadedFiles([])

      // Refresh the list to show new candidates
      await fetchCandidates()

    } catch (error) {
      console.error("Error processing resumes:", error)
      alert(`Failed to process resumes: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <RecruiterHeader />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Upload & Job Section */}
            <Card>
              <CardHeader>
                <CardTitle>New Screening Session</CardTitle>
                <CardDescription>Upload resumes and select a job position</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="flex-1">
                    <label className="flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-border rounded-lg cursor-pointer hover:border-primary/50 transition">
                      <div className="text-center">
                        <Upload className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
                        <span className="text-sm font-medium">Drop resumes or click to upload</span>
                        <span className="text-xs text-muted-foreground block mt-1">PDF, DOCX, TXT</span>
                        {uploadedFiles.length > 0 && (
                          <span className="text-xs text-primary font-medium block mt-2">
                            {uploadedFiles.length} file(s) selected
                          </span>
                        )}
                      </div>
                      <input
                        type="file"
                        className="hidden"
                        multiple
                        accept=".pdf,.docx,.txt"
                        onChange={handleFileChange}
                      />
                    </label>

                    {/* Display uploaded files */}
                    {uploadedFiles.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-sm font-medium">Selected Files:</p>
                        <div className="max-h-32 overflow-y-auto space-y-1">
                          {uploadedFiles.map((file, index) => (
                            <div key={index} className="text-xs bg-muted px-3 py-2 rounded flex items-center justify-between">
                              <span className="truncate">{file.name}</span>
                              <span className="text-muted-foreground ml-2">{(file.size / 1024).toFixed(1)} KB</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <JobSelector
                      selectedJob={selectedJob}
                      onJobSelect={setSelectedJob}
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <Button
                  onClick={handleProcessResumes}
                  disabled={uploadedFiles.length === 0 || isProcessing}
                  className="w-full"
                  size="lg"
                >
                  {isProcessing ? "Processing..." : `Process ${uploadedFiles.length} Resume${uploadedFiles.length !== 1 ? 's' : ''}`}
                </Button>
              </CardContent>
            </Card>

            {/* Batch Operations */}
            {selectedCandidates.length > 0 && (
              <BatchOperations
                selectedCount={selectedCandidates.length}
                onClearSelection={() => setSelectedCandidates([])}
              />
            )}

            {/* Search & Filter */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Search className="w-5 h-5 text-muted-foreground" />
                  <Input
                    placeholder="Search candidates..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="border-0 bg-transparent"
                  />
                </div>
              </CardHeader>
            </Card>

            {/* Candidates List */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Shortlist Results</CardTitle>
                    <CardDescription>{filteredCandidates.length} candidates found</CardDescription>
                  </div>
                  <Checkbox
                    checked={selectedCandidates.length === filteredCandidates.length && filteredCandidates.length > 0}
                    onCheckedChange={toggleSelectAll}
                    aria-label="Select all"
                  />
                </div>
                {fetchError && (
                  <div className="p-3 my-2 text-sm text-red-500 bg-red-100 border border-red-200 rounded">
                    Error loading candidates: {fetchError}
                  </div>
                )}
              </CardHeader>
              <CardContent>
                {isLoadingCandidates ? (
                  <div className="text-center py-8 text-muted-foreground">Loading candidates...</div>
                ) : filteredCandidates.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">No candidates found</div>
                ) : (
                  <div className="space-y-3">
                    {filteredCandidates.map((candidate) => (
                      <div
                        key={candidate.id}
                        className="flex items-center gap-3 p-4 border border-border rounded-lg hover:bg-muted/30 transition"
                      >
                        <Checkbox
                          checked={selectedCandidates.includes(candidate.id)}
                          onCheckedChange={() => toggleSelectCandidate(candidate.id)}
                          aria-label={`Select ${candidate.name}`}
                        />
                        <div
                          className="flex-1 cursor-pointer"
                          onClick={() => {
                            setSelectedCandidate(candidate)
                            setIsDetailOpen(true)
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-sm hover:text-primary">{candidate.name || "Unknown Candidate"}</h3>
                          </div>
                          <p className="text-xs text-muted-foreground">{candidate.email || "No email"}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-primary">{candidate.score}</div>
                          <div className="text-xs text-muted-foreground">{candidate.experience}y exp</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={candidate.status === "shortlisted" ? "bg-accent/20 text-accent" : candidate.status === "rejected" ? "bg-destructive/20 text-destructive" : "bg-primary/20 text-primary"}>
                            {candidate.status}
                          </Badge>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleStatusChange(candidate.id, "shortlisted")}>
                                Shortlist
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleStatusChange(candidate.id, "pending")}>
                                Mark as Pending
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleStatusChange(candidate.id, "rejected")}>
                                Reject
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => {
                                setSelectedCandidate(candidate)
                                setIsDetailOpen(true)
                              }}>
                                View Details
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Advanced Filters */}
            <AdvancedFilters onFilterChange={setFilters} />

            {/* Score Weights */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Score Weights</CardTitle>
                  <Settings className="w-4 h-4 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent>
                <ScoreWeights weights={weights} setWeights={setWeights} />
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Overview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Shortlisted</span>
                    <span className="font-semibold text-accent">
                      {candidates.filter((c) => c.status === "shortlisted").length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Pending</span>
                    <span className="font-semibold text-primary">
                      {candidates.filter((c) => c.status === "pending").length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Rejected</span>
                    <span className="font-semibold text-destructive">
                      {candidates.filter((c) => c.status === "rejected").length}
                    </span>
                  </div>
                </div>
                <Button className="w-full">Publish Results</Button>
              </CardContent>
            </Card>
          </div>
        </div >
      </main >

      {/* Candidate Detail Modal */}
      {
        selectedCandidate && (
          <CandidateDetailModal candidate={selectedCandidate} open={isDetailOpen} onOpenChange={setIsDetailOpen} />
        )
      }
    </div >
  )
}
