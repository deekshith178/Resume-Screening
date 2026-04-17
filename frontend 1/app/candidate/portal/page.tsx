

"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import CandidateHeader from "@/components/candidate/candidate-header"
import ApplicationStatus from "@/components/candidate/application-status"
import ScoreBreakdown from "@/components/candidate/score-breakdown"
import TestFitTool from "@/components/candidate/test-fit-tool"
import GuidanceDashboard from "@/components/candidate/guidance-dashboard"
import { Upload, TrendingUp, BookOpen, User } from "lucide-react"
import { toast } from "sonner"

export default function CandidatePortal() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState("status")
  const [hasGuidance, setHasGuidance] = useState(false)
  const [loading, setLoading] = useState(true)

  const [statusData, setStatusData] = useState<any>(null)
  const [guidanceData, setGuidanceData] = useState<any>(null)
  const [candidateInfo, setCandidateInfo] = useState<any>(null)
  
  // Extract candidate category and skills from status data
  const candidateCategory = statusData?.category || "General"
  const candidateSkills = statusData?.skills || []

  // Demo Job ID to link guidance to
  const DEMO_JOB_ID = "job-datascience"

  useEffect(() => {
    const init = async () => {
      // Check for URL parameters first (from shared portal link)
      const urlCandidateId = searchParams.get("candidate_id")
      const urlToken = searchParams.get("token")

      // If URL params provided, store them in localStorage
      if (urlCandidateId && urlToken) {
        localStorage.setItem("candidate_id", urlCandidateId)
        localStorage.setItem("candidate_token", urlToken)
        // Clean up URL by removing query params
        router.replace("/candidate/portal")
      }

      const candidateId = urlCandidateId || localStorage.getItem("candidate_id")
      const token = urlToken || localStorage.getItem("candidate_token")

      if (!candidateId || !token) {
        router.push("/auth?tab=candidate")
        return
      }

      setLoading(true)
      try {
        // Fetch Status
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

        // Note: Using fetch directly here because lib/api might rely on different auth headers
        // Ideally we update lib/api to support candidate auth, but direct fetch is safer for this specific flow
        const statusRes = await fetch(`${API_URL}/candidate/${candidateId}/status?token=${token}`)

        let sData: any = null
        if (statusRes.ok) {
          sData = await statusRes.json()
          setStatusData(sData)
        } else {
          if (statusRes.status === 401) {
            router.push("/auth?tab=candidate")
            return
          }
          console.error("Failed to fetch status")
        }

        // Try Fetch Guidance (to see if already opted in)
        // Use candidate's actual category from status data
        const candidateCategory = sData?.category || "General"
        const guidanceRes = await fetch(`${API_URL}/candidate/guidance/request`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidate_id: candidateId, token: token, category: candidateCategory })
        })

        if (guidanceRes.ok) {
          const gData = await guidanceRes.json()
          setGuidanceData(gData)
          setHasGuidance(true)
        }
      } catch (error) {
        console.error("Error loading portal data", error)
      } finally {
        setLoading(false)
      }
    }

    init()
  }, [searchParams, router])

  const handleOptIn = async () => {
    const candidateId = localStorage.getItem("candidate_id")
    if (!candidateId) return

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const token = localStorage.getItem("candidate_token") || "demo-token-bypass"

      // Use candidate's actual category from status data
      const candidateCategory = statusData?.category || "General"

      // Request Guidance Generation
      const guidanceRes = await fetch(`${API_URL}/candidate/guidance/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_id: candidateId, token: token, category: candidateCategory })
      })

      if (guidanceRes.ok) {
        const gData = await guidanceRes.json()
        setGuidanceData(gData)
        setHasGuidance(true)
        setActiveTab("guidance")
        toast.success("Guidance generated successfully!")
      } else {
        const err = await guidanceRes.json()
        throw new Error(err.detail || "Failed to generate")
      }
    } catch (e: any) {
      console.error(e)
      toast.error(e.message || "Failed to generate guidance")
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading portal...</div>
  }

  return (
    <div className="min-h-screen bg-background">
      <CandidateHeader />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Status Alert */}
        <Alert className="mb-6 bg-accent/10 border-accent/30">
          <TrendingUp className="w-4 h-4" />
          <AlertDescription>
            Your application is being evaluated. You'll receive an update within 48 hours.
          </AlertDescription>
        </Alert>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="status">Application Status</TabsTrigger>
            <TabsTrigger value="profile">My Profile</TabsTrigger>
            <TabsTrigger value="score">Score Breakdown</TabsTrigger>
            <TabsTrigger value="test-fit">Test-Fit Tool</TabsTrigger>
            {hasGuidance && <TabsTrigger value="guidance">Personalized Guidance</TabsTrigger>}
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5" />
                  My Profile
                </CardTitle>
                <CardDescription>Your candidate information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  {statusData && statusData.name && (
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Name</span>
                      <span className="font-semibold">{statusData.name}</span>
                    </div>
                  )}
                  {statusData && statusData.email && (
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Email</span>
                      <span className="font-medium">{statusData.email}</span>
                    </div>
                  )}
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-muted-foreground">Candidate ID</span>
                    <span className="font-mono text-sm">{localStorage.getItem("candidate_id") || "N/A"}</span>
                  </div>
                  {statusData && (
                    <>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-muted-foreground">Status</span>
                        <span className="font-medium capitalize">{statusData.status}</span>
                      </div>
                      {statusData.score !== null && statusData.score !== undefined && (
                        <div className="flex justify-between py-2 border-b">
                          <span className="text-muted-foreground">Score</span>
                          <span className="font-bold text-primary">{statusData.score?.toFixed(1) || "N/A"}</span>
                        </div>
                      )}
                      {statusData.category && (
                        <div className="flex justify-between py-2 border-b">
                          <span className="text-muted-foreground">Profession</span>
                          <span className="font-medium capitalize">{statusData.category}</span>
                        </div>
                      )}
                      {statusData.skills && Array.isArray(statusData.skills) && statusData.skills.length > 0 && (
                        <div className="py-2">
                          <span className="text-muted-foreground block mb-2">Skills</span>
                          <div className="flex flex-wrap gap-2">
                            {statusData.skills.slice(0, 8).map((skill: string, idx: number) => (
                              <span key={idx} className="text-xs px-2 py-1 bg-muted rounded-md">
                                {skill}
                              </span>
                            ))}
                            {statusData.skills.length > 8 && (
                              <span className="text-xs px-2 py-1 bg-muted rounded-md text-muted-foreground">
                                +{statusData.skills.length - 8} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Application Status Tab */}
          <TabsContent value="status" className="space-y-4">
            <ApplicationStatus status={statusData?.status} />
            <Card>
              <CardHeader>
                <CardTitle>Re-upload Resume</CardTitle>
                <CardDescription>Update your resume to improve your score</CardDescription>
              </CardHeader>
              <CardContent>
                <label className="flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-border rounded-lg cursor-pointer hover:border-primary/50 transition relative">
                  <div className="text-center">
                    <Upload className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
                    <span className="text-sm font-medium">Upload new resume</span>
                    <p className="text-xs text-muted-foreground mt-1">
                      (Click to select PDF/DOCX)
                    </p>
                  </div>
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.docx,.txt"
                    onChange={async (e) => {
                      const file = e.target.files?.[0]
                      if (!file) return

                      const candidateId = localStorage.getItem("candidate_id")
                      if (!candidateId) return

                      const formData = new FormData()
                      formData.append("file", file)
                      formData.append("candidate_id", candidateId)

                      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

                      toast.loading("Uploading and analyzing resume...")
                      setLoading(true)

                      try {
                        const res = await fetch(`${API_URL}/upload-resume`, {
                          method: "POST",
                          body: formData
                        })

                        if (!res.ok) throw new Error("Upload failed")

                        const data = await res.json()
                        toast.dismiss()
                        toast.success("Resume updated! Score refreshed.")

                        // Update local state with new score/status
                        setStatusData((prev: any) => ({
                          ...prev,
                          score: data.score,
                          status: "processed" // temporarily mark processed until refreshed
                        }))

                        // Reload window or fetch status again to be clean
                        window.location.reload()

                      } catch (err) {
                        console.error(err)
                        toast.dismiss()
                        toast.error("Upload failed")
                      } finally {
                        setLoading(false)
                      }
                    }}
                  />
                </label>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Score Breakdown Tab */}
          <TabsContent value="score">
            <ScoreBreakdown score={statusData?.score} components={statusData?.components} />
          </TabsContent>

          {/* Test-Fit Tool Tab */}
          <TabsContent value="test-fit">
            <TestFitTool />
          </TabsContent>

          {/* Guidance Tab */}
          {hasGuidance && (
            <TabsContent value="guidance">
              <GuidanceDashboard 
                onOptIn={() => { }} 
                data={guidanceData} 
                category={candidateCategory}
                skills={candidateSkills}
              />
            </TabsContent>
          )}
        </Tabs>

        {/* Guidance CTA */}
        {!hasGuidance && (
          <Card className="mt-6 bg-gradient-to-r from-primary/5 to-accent/5 border-primary/20">
            <CardHeader>
              <div className="flex items-start gap-4">
                <BookOpen className="w-8 h-8 text-primary flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <CardTitle>Get Personalized Guidance</CardTitle>
                  <CardDescription className="mt-2">
                    {candidateCategory !== "General" 
                      ? `As a ${candidateCategory} professional, we'll analyze successful candidates in your field and provide you with a personalized learning path to improve your skills.`
                      : "We'll analyze successful candidates in similar roles and provide you with a personalized learning path to improve your skills."}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button className="gap-2" onClick={handleOptIn}>
                <BookOpen className="w-4 h-4" />
                Opt-in for Guidance
              </Button>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
