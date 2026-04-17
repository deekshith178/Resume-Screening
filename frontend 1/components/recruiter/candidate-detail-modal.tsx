"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Download, Mail, FileText, Link2, Loader2, Check } from "lucide-react"
import { toast } from "sonner"

interface CandidateDetailModalProps {
  candidate: {
    id: string
    name: string
    email: string
    score: number
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
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function CandidateDetailModal({ candidate, open, onOpenChange }: CandidateDetailModalProps) {
  const [isGeneratingLink, setIsGeneratingLink] = useState(false)
  const [linkCopied, setLinkCopied] = useState(false)

  // Map backend components to chart data
  const scoreBreakdown = [
    { 
      category: "Skills Match", 
      value: candidate.components?.normalized_similarity !== undefined 
        ? Math.round(candidate.components.normalized_similarity * 100) 
        : 0 
    },
    { 
      category: "Experience", 
      value: candidate.components?.E_norm !== undefined 
        ? Math.round(candidate.components.E_norm * 100) 
        : 0 
    },
    { 
      category: "Projects", 
      value: candidate.components?.P_norm !== undefined 
        ? Math.round(candidate.components.P_norm * 100) 
        : 0 
    },
    { 
      category: "Certifications", 
      value: candidate.components?.C_norm !== undefined 
        ? Math.round(candidate.components.C_norm * 100) 
        : 0 
    },
  ]

  const handleCopyPortalLink = async () => {
    setIsGeneratingLink(true)
    setLinkCopied(false)

    try {
      const token = localStorage.getItem("recruiter_token")
      if (!token) {
        toast.error("Please log in again")
        return
      }

      const res = await fetch(`/api/candidates/${candidate.id}/portal-link`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.error || "Failed to generate link")
      }

      const data = await res.json()

      // Copy to clipboard
      await navigator.clipboard.writeText(data.portal_url)
      setLinkCopied(true)
      toast.success("Portal link copied to clipboard!")

      // Reset the copied state after 3 seconds
      setTimeout(() => setLinkCopied(false), 3000)
    } catch (error) {
      console.error("Failed to generate portal link:", error)
      toast.error(error instanceof Error ? error.message : "Failed to generate portal link")
    } finally {
      setIsGeneratingLink(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{candidate.name || "Unknown Candidate"}</DialogTitle>
          <DialogDescription>{candidate.email || "No email provided"}</DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="scores">Score Breakdown</TabsTrigger>
            <TabsTrigger value="resume">Resume</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Overall Score</p>
                <p className="text-3xl font-bold text-primary">
                  {candidate.score !== undefined && candidate.score !== null 
                    ? Math.round(candidate.score * 10) / 10 
                    : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Experience</p>
                <p className="text-3xl font-bold">
                  {candidate.experience !== undefined && candidate.experience !== null 
                    ? `${candidate.experience} years` 
                    : "N/A"}
                </p>
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Skills</CardTitle>
              </CardHeader>
              <CardContent>
                {candidate.skills && Array.isArray(candidate.skills) && candidate.skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {candidate.skills.map((skill, idx) => (
                      <Badge key={idx}>{skill}</Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No skills available</p>
                )}
              </CardContent>
            </Card>

            {candidate.hybrid && (
              <Badge className="w-full justify-center py-2" variant="outline">
                Hybrid Role Fit
              </Badge>
            )}
          </TabsContent>

          <TabsContent value="scores">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Detailed Score Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={scoreBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="resume">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Resume Preview</CardTitle>
                <CardDescription>Full resume document</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-muted/50 h-64 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">Resume preview</p>
                    <p className="text-xs text-muted-foreground">PDF document would render here</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex gap-2 flex-wrap">
          <Button
            variant="outline"
            className="flex-1 gap-2"
            onClick={handleCopyPortalLink}
            disabled={isGeneratingLink}
          >
            {isGeneratingLink ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : linkCopied ? (
              <Check className="w-4 h-4 text-green-500" />
            ) : (
              <Link2 className="w-4 h-4" />
            )}
            {isGeneratingLink ? "Generating..." : linkCopied ? "Link Copied!" : "Copy Portal Link"}
          </Button>
          <Button variant="outline" className="flex-1 gap-2">
            <Mail className="w-4 h-4" />
            Send Email
          </Button>
          <Button className="flex-1 gap-2">
            <Download className="w-4 h-4" />
            Download Resume
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
