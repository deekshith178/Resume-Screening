"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Lightbulb, AlertCircle } from "lucide-react"
import { toast } from "sonner"

interface TestFitResult {
  score: number
  match_percentage: number
  best_category: string
  components: {
    job_description_similarity: number
    profession_match: number
    experience: number
    projects: number
    certifications: number
  }
  message: string
}

export default function TestFitTool() {
  const [jd, setJd] = useState("")
  const [result, setResult] = useState<TestFitResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleTestFit = async () => {
    if (!jd.trim()) {
      toast.error("Please paste a job description")
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const candidateId = localStorage.getItem("candidate_id")
      const token = localStorage.getItem("candidate_token")

      if (!candidateId || !token) {
        throw new Error("Please log in to use this feature")
      }

      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

      const response = await fetch(`${API_URL}/candidate/test-fit-job`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          token: token,
          job_description: jd,
        }),
      })

      if (!response.ok) {
        let errorMessage = "Failed to analyze job description"
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          // If response is not JSON, try to get text
          try {
            const errorText = await response.text()
            errorMessage = errorText || errorMessage
          } catch {
            errorMessage = `Server error: ${response.status} ${response.statusText}`
          }
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setResult(data)
      toast.success("Analysis complete!")
    } catch (err: any) {
      const errorMessage = err.message || "Failed to analyze job description"
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Test Your Fit</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Paste Job Description</label>
            <Textarea
              placeholder="Paste the job description you'd like to test yourself against..."
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              className="min-h-32"
            />
          </div>
          <Button onClick={handleTestFit} disabled={!jd || loading} className="w-full">
            {loading ? "Analyzing..." : "Analyze Match"}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="w-4 h-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Your Match Score</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <div className="text-5xl font-bold text-primary mb-2">
                  {Math.round(result.match_percentage)}
                </div>
                <p className="text-muted-foreground mb-2">{result.message}</p>
                <p className="text-sm text-muted-foreground">
                  Best match category: <span className="font-medium">{result.best_category}</span>
                </p>
              </div>
              <Progress value={result.match_percentage} className="h-3" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Score Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium">Job Description Match</span>
                    <span className="text-sm font-semibold text-primary">
                      {Math.round(result.components.job_description_similarity * 100)}%
                    </span>
                  </div>
                  <Progress value={result.components.job_description_similarity * 100} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium">Profession Match</span>
                    <span className="text-sm font-semibold text-primary">
                      {Math.round(result.components.profession_match * 100)}%
                    </span>
                  </div>
                  <Progress value={result.components.profession_match * 100} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium">Experience</span>
                    <span className="text-sm font-semibold text-primary">
                      {Math.round(result.components.experience * 100)}%
                    </span>
                  </div>
                  <Progress value={result.components.experience * 100} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium">Projects</span>
                    <span className="text-sm font-semibold text-primary">
                      {Math.round(result.components.projects * 100)}%
                    </span>
                  </div>
                  <Progress value={result.components.projects * 100} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium">Certifications</span>
                    <span className="text-sm font-semibold text-primary">
                      {Math.round(result.components.certifications * 100)}%
                    </span>
                  </div>
                  <Progress value={result.components.certifications * 100} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Alert>
            <Lightbulb className="w-4 h-4" />
            <AlertDescription>{result.message}</AlertDescription>
          </Alert>
        </>
      )}
    </div>
  )
}
