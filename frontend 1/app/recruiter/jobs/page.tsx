"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import RecruiterHeader from "@/components/recruiter/recruiter-header"
import { Plus, Edit2, Trash2, Users } from "lucide-react"
import { api } from "@/lib/api"
import { toast } from "sonner" // Assuming sonner is installed as per package.json

interface Job {
  id: string
  title: string
  department: string
  description: string
  status: "active" | "closed" | "draft"
  candidates: number
  createdAt: string
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const [isOpen, setIsOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    title: "",
    department: "",
    description: "",
  })

  // Fetch jobs on mount
  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      setIsLoading(true)
      // Backend returns { items: JobResponse[], total, ... }
      const data = await api.get<{ items: any[] }>("/jobs")

      const mappedJobs: Job[] = data.items.map((j: any) => ({
        id: j.id,
        title: j.title,
        department: j.category, // Map category -> department
        description: j.description || "",
        status: "active", // Backend doesn't support status yet, default to active
        candidates: j.candidate_count || 0,
        createdAt: j.created_at.split("T")[0],
      }))

      setJobs(mappedJobs)
    } catch (error) {
      console.error("Failed to fetch jobs:", error)
      toast.error("Failed to load jobs")
    } finally {
      setIsLoading(false)
    }
  }

  const handleAdd = async () => {
    if (formData.title && formData.department) {
      try {
        if (editingId) {
          // Edit not implemented in MVP backend yet (PUT /jobs/{id})
          // For now, local update or show error
          toast.warning("Job editing not supported in MVP backend yet")
          // We could implement PUT if we wanted, but for now we skip
          // setJobs(jobs.map((j) => (j.id === editingId ? { ...j, ...formData } : j)))
        } else {
          // Create new job
          // ID generation: Backend expects ID. We can generate one or let backend do it?
          // Backend `create_job` expects `id` in body.
          // Let's generate a simple ID here or use UUID.
          const newId = `job-${Date.now()}`

          await api.post("/jobs", {
            id: newId,
            title: formData.title,
            category: formData.department, // Map department -> category
            description: formData.description,
            min_years_experience: 0, // Default
            required_skills: "", // Default
          })

          toast.success("Job created successfully")
          fetchJobs() // Reload
        }

        setFormData({ title: "", department: "", description: "" })
        setIsOpen(false)
        setEditingId(null)
      } catch (error: any) {
        toast.error("Failed to save job: " + error.message)
      }
    }
  }

  const deleteJob = async (id: string) => {
    if (!confirm("Are you sure you want to delete this job?")) return

    try {
      await api.delete(`/jobs/${id}`)
      toast.success("Job deleted")
      // Optimistic update or reload
      setJobs(jobs.filter((j) => j.id !== id))
    } catch (error: any) {
      toast.error("Failed to delete job")
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800"
      case "draft":
        return "bg-yellow-100 text-yellow-800"
      case "closed":
        return "bg-gray-100 text-gray-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <RecruiterHeader />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Job Positions</h1>
            <p className="text-muted-foreground mt-2">Manage and create job openings</p>
          </div>
          <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
              <Button gap-2 onClick={() => {
                setEditingId(null)
                setFormData({ title: "", department: "", description: "" })
              }}>
                <Plus className="w-4 h-4" />
                New Job
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingId ? "Edit Job" : "Create New Job"}</DialogTitle>
                <DialogDescription>Fill in the job details below</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Input
                  placeholder="Job Title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                />
                <Input
                  placeholder="Department (Category)"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                />
                <Textarea
                  placeholder="Job Description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={5}
                />
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setIsOpen(false)} className="flex-1">
                    Cancel
                  </Button>
                  <Button onClick={handleAdd} className="flex-1">
                    {editingId ? "Update" : "Create"}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <Tabs defaultValue="all" className="space-y-4">
          <TabsList>
            <TabsTrigger value="all">All Jobs</TabsTrigger>
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="draft">Drafts</TabsTrigger>
            <TabsTrigger value="closed">Closed</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            {isLoading ? (
              <div className="text-center py-8">Loading jobs...</div>
            ) : jobs.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <p className="text-muted-foreground">No jobs found. Create one to get started.</p>
                </CardContent>
              </Card>
            ) : (
              jobs.map((job) => (
                <Card key={job.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <CardTitle>{job.title}</CardTitle>
                        <CardDescription>{job.department}</CardDescription>
                      </div>
                      <Badge className={getStatusColor(job.status)}>{job.status}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">{job.description}</p>
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2 text-sm">
                        <Users className="w-4 h-4 text-muted-foreground" />
                        <span>{job.candidates} candidates</span>
                      </div>
                      <div className="flex gap-2">
                        {/* Edit button disabled for now/modified to warn */}
                        {/* 
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setFormData({ title: job.title, department: job.department, description: job.description })
                              setEditingId(job.id)
                              setIsOpen(true)
                            }}
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          */}
                        <Button variant="outline" size="sm" onClick={() => deleteJob(job.id)}>
                          <Trash2 className="w-4 h-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          <TabsContent value="active">
            {/* Reuse list for active since all are active basically */}
            {jobs.map((job) => (
              <Card key={job.id}>
                <CardHeader>
                  <CardTitle>{job.title}</CardTitle>
                  <CardDescription>{job.department}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{job.description}</p>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="draft">
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">Drafts not supported in MVP</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="closed">
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">Closed jobs not supported in MVP</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
