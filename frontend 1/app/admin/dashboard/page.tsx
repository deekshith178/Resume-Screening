"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import AdminHeader from "@/components/admin/admin-header"
import { Users, Briefcase, TrendingUp, MoreHorizontal, Edit, Trash2, Plus } from "lucide-react"
import { toast } from "sonner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface Recruiter {
  id: number
  email: string
  name: string | null
  role: string
  jobs_count: number
  candidates_count: number
  created_at: string
}

interface Candidate {
  id: string
  name: string
  email: string
  category: string
  recruiter_id: number | null
  recruiter_email: string | null
  skills: string[] | null
  created_at: string
}

export default function AdminDashboard() {
  const router = useRouter()
  const [recruiters, setRecruiters] = useState<Recruiter[]>([])
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalRecruiters: 0,
    totalCandidates: 0,
    totalJobs: 0,
  })

  // Edit dialog states
  const [editRecruiterDialog, setEditRecruiterDialog] = useState(false)
  const [editCandidateDialog, setEditCandidateDialog] = useState(false)
  const [deleteRecruiterDialog, setDeleteRecruiterDialog] = useState(false)
  const [deleteCandidateDialog, setDeleteCandidateDialog] = useState(false)
  const [selectedRecruiter, setSelectedRecruiter] = useState<Recruiter | null>(null)
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [editForm, setEditForm] = useState({
    name: "",
    email: "",
    role: "recruiter",
    password: "",
  })

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem("recruiter_token")
    if (!token) {
      router.push("/auth?tab=recruiter")
      return
    }
    
    // Verify admin role by checking recruiter profile
    try {
      const response = await fetch("/api/recruiters/me", {
        headers: { Authorization: `Bearer ${token}` },
      })
      
      if (response.ok) {
        const profile = await response.json()
        if (profile.role !== "admin") {
          toast.error("Admin access required. Only users with admin role can access this page.")
          router.push("/recruiter/dashboard")
          return
        }
        // Admin verified - fetch data
        fetchData()
      } else {
        // Token invalid or expired
        router.push("/auth?tab=recruiter")
      }
    } catch (error) {
      console.error("Auth check failed:", error)
      router.push("/auth?tab=recruiter")
    }
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem("recruiter_token")
      if (!token) {
        router.push("/auth?tab=recruiter")
        return
      }

      // Fetch recruiters
      const recruitersRes = await fetch("/api/admin/recruiters", {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (recruitersRes.ok) {
        const recruitersData = await recruitersRes.json()
        setRecruiters(recruitersData.recruiters || [])
        setStats((prev) => ({
          ...prev,
          totalRecruiters: recruitersData.total || 0,
        }))
      }

      // Fetch candidates
      const candidatesRes = await fetch("/api/admin/candidates", {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (candidatesRes.ok) {
        const candidatesData = await candidatesRes.json()
        setCandidates(candidatesData.candidates || [])
        setStats((prev) => ({
          ...prev,
          totalCandidates: candidatesData.total || 0,
        }))
      }
    } catch (error) {
      console.error("Error fetching data:", error)
      toast.error("Failed to load admin data")
    } finally {
      setLoading(false)
    }
  }

  const handleEditRecruiter = (recruiter: Recruiter) => {
    setSelectedRecruiter(recruiter)
    setEditForm({
      name: recruiter.name || "",
      email: recruiter.email,
      role: recruiter.role,
      password: "",
    })
    setEditRecruiterDialog(true)
  }

  const handleSaveRecruiter = async () => {
    if (!selectedRecruiter) return

    try {
      const token = localStorage.getItem("recruiter_token")
      const updateData: any = {
        name: editForm.name || null,
        email: editForm.email,
        role: editForm.role,
      }
      if (editForm.password) {
        updateData.password = editForm.password
      }

      const response = await fetch(`/api/admin/recruiters/${selectedRecruiter.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      })

      if (response.ok) {
        toast.success("Recruiter updated successfully")
        setEditRecruiterDialog(false)
        fetchData()
      } else {
        const error = await response.json()
        toast.error(error.error || "Failed to update recruiter")
      }
    } catch (error) {
      toast.error("Failed to update recruiter")
    }
  }

  const handleDeleteRecruiter = async () => {
    if (!selectedRecruiter) return

    try {
      const token = localStorage.getItem("recruiter_token")
      const response = await fetch(`/api/admin/recruiters/${selectedRecruiter.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })

      if (response.ok) {
        toast.success("Recruiter deleted successfully")
        setDeleteRecruiterDialog(false)
        fetchData()
      } else {
        const error = await response.json()
        toast.error(error.error || "Failed to delete recruiter")
      }
    } catch (error) {
      toast.error("Failed to delete recruiter")
    }
  }

  const handleEditCandidate = (candidate: Candidate) => {
    setSelectedCandidate(candidate)
    setEditForm({
      name: candidate.name,
      email: candidate.email,
      role: "",
      password: "",
    })
    setEditCandidateDialog(true)
  }

  const handleSaveCandidate = async () => {
    if (!selectedCandidate) return

    try {
      const token = localStorage.getItem("recruiter_token")
      const updateData: any = {
        name: editForm.name,
        email: editForm.email,
        category: selectedCandidate.category,
        recruiter_id: selectedCandidate.recruiter_id,
      }

      const response = await fetch(`/api/admin/candidates/${selectedCandidate.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      })

      if (response.ok) {
        toast.success("Candidate updated successfully")
        setEditCandidateDialog(false)
        fetchData()
      } else {
        const error = await response.json()
        toast.error(error.error || "Failed to update candidate")
      }
    } catch (error) {
      toast.error("Failed to update candidate")
    }
  }

  const handleDeleteCandidate = async () => {
    if (!selectedCandidate) return

    try {
      const token = localStorage.getItem("recruiter_token")
      const response = await fetch(`/api/admin/candidates/${selectedCandidate.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })

      if (response.ok) {
        toast.success("Candidate deleted successfully")
        setDeleteCandidateDialog(false)
        fetchData()
      } else {
        const error = await response.json()
        toast.error(error.error || "Failed to delete candidate")
      }
    } catch (error) {
      toast.error("Failed to delete candidate")
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <AdminHeader />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-2">Manage recruiters, candidates, and system settings</p>
        </div>

        {/* Key Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Recruiters</p>
                  <p className="text-2xl font-bold mt-2">{stats.totalRecruiters}</p>
                </div>
                <Users className="w-8 h-8 text-muted-foreground opacity-40" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Candidates</p>
                  <p className="text-2xl font-bold mt-2">{stats.totalCandidates}</p>
                </div>
                <Users className="w-8 h-8 text-muted-foreground opacity-40" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">System Status</p>
                  <p className="text-lg font-semibold flex items-center gap-2 mt-2">
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                    Operational
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-muted-foreground opacity-40" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Management Tabs */}
        <Tabs defaultValue="recruiters" className="space-y-6">
          <TabsList>
            <TabsTrigger value="recruiters">Recruiters</TabsTrigger>
            <TabsTrigger value="candidates">Candidates</TabsTrigger>
          </TabsList>

          <TabsContent value="recruiters" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recruiter Management</CardTitle>
                <CardDescription>View and manage all recruiters in the system</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8">Loading recruiters...</div>
                ) : recruiters.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">No recruiters found</div>
                ) : (
                  <div className="space-y-3">
                    {recruiters.map((recruiter) => (
                      <div
                        key={recruiter.id}
                        className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <p className="font-medium">{recruiter.name || "No name"}</p>
                            <Badge variant={recruiter.role === "admin" ? "default" : "secondary"}>
                              {recruiter.role}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{recruiter.email}</p>
                          <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                            <span>{recruiter.jobs_count} jobs</span>
                            <span>{recruiter.candidates_count} candidates</span>
                            <span>Joined {new Date(recruiter.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEditRecruiter(recruiter)}>
                              <Edit className="w-4 h-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedRecruiter(recruiter)
                                setDeleteRecruiterDialog(true)
                              }}
                              className="text-destructive"
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="candidates" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Candidate Management</CardTitle>
                <CardDescription>View and manage all candidates in the system</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8">Loading candidates...</div>
                ) : candidates.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">No candidates found</div>
                ) : (
                  <div className="space-y-3">
                    {candidates.map((candidate) => (
                      <div
                        key={candidate.id}
                        className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <p className="font-medium">{candidate.name}</p>
                            <Badge variant="outline">{candidate.category}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{candidate.email}</p>
                          {candidate.recruiter_email && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Recruiter: {candidate.recruiter_email}
                            </p>
                          )}
                          {candidate.skills && candidate.skills.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {candidate.skills.slice(0, 5).map((skill, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {skill}
                                </Badge>
                              ))}
                              {candidate.skills.length > 5 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{candidate.skills.length - 5} more
                                </Badge>
                              )}
                            </div>
                          )}
                          <p className="text-xs text-muted-foreground mt-2">
                            Joined {new Date(candidate.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEditCandidate(candidate)}>
                              <Edit className="w-4 h-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedCandidate(candidate)
                                setDeleteCandidateDialog(true)
                              }}
                              className="text-destructive"
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Edit Recruiter Dialog */}
        <Dialog open={editRecruiterDialog} onOpenChange={setEditRecruiterDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Recruiter</DialogTitle>
              <DialogDescription>Update recruiter information</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Role</Label>
                <Select value={editForm.role} onValueChange={(value) => setEditForm({ ...editForm, role: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="recruiter">Recruiter</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">New Password (leave blank to keep current)</Label>
                <Input
                  id="password"
                  type="password"
                  value={editForm.password}
                  onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                  placeholder="Enter new password"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditRecruiterDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveRecruiter}>Save Changes</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Candidate Dialog */}
        <Dialog open={editCandidateDialog} onOpenChange={setEditCandidateDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Candidate</DialogTitle>
              <DialogDescription>Update candidate information</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="candidate-name">Name</Label>
                <Input
                  id="candidate-name"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="candidate-email">Email</Label>
                <Input
                  id="candidate-email"
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditCandidateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveCandidate}>Save Changes</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Recruiter Dialog */}
        <AlertDialog open={deleteRecruiterDialog} onOpenChange={setDeleteRecruiterDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete recruiter {selectedRecruiter?.email}. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleDeleteRecruiter} className="bg-destructive text-destructive-foreground">
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Delete Candidate Dialog */}
        <AlertDialog open={deleteCandidateDialog} onOpenChange={setDeleteCandidateDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete candidate {selectedCandidate?.name} ({selectedCandidate?.email}). This
                action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleDeleteCandidate} className="bg-destructive text-destructive-foreground">
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </main>
    </div>
  )
}
