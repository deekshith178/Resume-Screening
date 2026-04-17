"use client"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useState, useEffect } from "react"

interface Job {
  id: string
  title: string
  category: string
}

interface JobSelectorProps {
  onJobSelect?: (jobId: string) => void
  selectedJob?: string
}

export default function JobSelector({ onJobSelect, selectedJob }: JobSelectorProps) {
  const [jobs, setJobs] = useState<Job[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const token = localStorage.getItem("recruiter_token")
        if (!token) {
          setIsLoading(false)
          return
        }

        const response = await fetch("/api/jobs", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (response.ok) {
          const data = await response.json()
          setJobs(data.items || [])
        }
      } catch (error) {
        console.error("Failed to fetch jobs:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchJobs()
  }, [])

  const handleValueChange = (value: string) => {
    if (onJobSelect) {
      onJobSelect(value)
    }
  }

  return (
    <div className="space-y-3">
      <div>
        <label className="text-sm font-medium mb-2 block">Select Job or Paste JD</label>
        <Select value={selectedJob} onValueChange={handleValueChange}>
          <SelectTrigger>
            <SelectValue placeholder={isLoading ? "Loading jobs..." : "Choose existing job..."} />
          </SelectTrigger>
          <SelectContent>
            {jobs.length === 0 && !isLoading && (
              <SelectItem value="_no_jobs" disabled>
                No jobs available
              </SelectItem>
            )}
            {jobs.map((job) => (
              <SelectItem key={job.id} value={job.id}>
                {job.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="relative">
        <div className="absolute left-0 top-0 text-xs text-muted-foreground bg-background px-2 py-1 -translate-y-1/2">
          Or
        </div>
      </div>
      <Textarea placeholder="Paste job description here..." className="min-h-24 text-sm" />
    </div>
  )
}
