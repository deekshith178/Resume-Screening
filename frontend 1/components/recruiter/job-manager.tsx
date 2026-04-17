"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Plus, Edit2, Trash2 } from "lucide-react"

interface Job {
  id: string
  title: string
  department: string
  candidates: number
  status: "active" | "closed"
}

export default function JobManager() {
  const [jobs, setJobs] = useState<Job[]>([
    { id: "1", title: "Senior React Developer", department: "Engineering", candidates: 12, status: "active" },
    { id: "2", title: "Product Manager", department: "Product", candidates: 8, status: "active" },
    { id: "3", title: "Data Analyst", department: "Analytics", candidates: 0, status: "closed" },
  ])

  const [isOpen, setIsOpen] = useState(false)
  const [newJob, setNewJob] = useState({ title: "", department: "", description: "" })

  const handleAddJob = () => {
    if (newJob.title && newJob.department) {
      setJobs([
        ...jobs,
        {
          id: Date.now().toString(),
          title: newJob.title,
          department: newJob.department,
          candidates: 0,
          status: "active",
        },
      ])
      setNewJob({ title: "", department: "", description: "" })
      setIsOpen(false)
    }
  }

  const deleteJob = (id: string) => {
    setJobs(jobs.filter((j) => j.id !== id))
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Job Positions</CardTitle>
          <CardDescription>Manage open and closed positions</CardDescription>
        </div>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button size="sm" gap-2>
              <Plus className="w-4 h-4" />
              New Job
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Job Position</DialogTitle>
              <DialogDescription>Add a new job opening to your system</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <Input
                placeholder="Job Title"
                value={newJob.title}
                onChange={(e) => setNewJob({ ...newJob, title: e.target.value })}
              />
              <Input
                placeholder="Department"
                value={newJob.department}
                onChange={(e) => setNewJob({ ...newJob, department: e.target.value })}
              />
              <Textarea
                placeholder="Job Description"
                value={newJob.description}
                onChange={(e) => setNewJob({ ...newJob, description: e.target.value })}
              />
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setIsOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddJob} className="flex-1">
                  Create Job
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted transition"
            >
              <div className="flex-1">
                <p className="font-medium">{job.title}</p>
                <p className="text-sm text-muted-foreground">{job.department}</p>
                <p className="text-xs text-muted-foreground mt-1">{job.candidates} candidates</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={job.status === "active" ? "default" : "secondary"}>{job.status}</Badge>
                <Button variant="ghost" size="sm">
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => deleteJob(job.id)}>
                  <Trash2 className="w-4 h-4 text-destructive" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
