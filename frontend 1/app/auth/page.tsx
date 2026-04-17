"use client"

import { useState, useEffect, Suspense } from "react"
import Link from "next/link"
import { useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CheckCircle2, AlertCircle } from "lucide-react"
import { toast } from "sonner"

function AuthContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [defaultTab, setDefaultTab] = useState<"candidate" | "recruiter">("candidate")

  useEffect(() => {
    const tab = searchParams.get("tab")
    if (tab === "recruiter" || tab === "candidate") {
      setDefaultTab(tab)
    }
  }, [searchParams])

  const [recruiterRole, setRecruiterRole] = useState("hr")

  // simulated magic link state
  const [email, setEmail] = useState("")
  const [tempToken, setTempToken] = useState<{ token: string, candidate_id: string } | null>(null)

  const [recruiterEmail, setRecruiterEmail] = useState("")
  const [recruiterPassword, setRecruiterPassword] = useState("")
  const [recruiterName, setRecruiterName] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isRegistering, setIsRegistering] = useState(false) // Toggle for registration mode

  // Handlers
  const handleRequestToken = async () => {
    setIsLoading(true)
    setTempToken(null)
    try {
      const response = await fetch("/api/auth/candidate-request-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })
      const data = await response.json()
      if (response.ok && data.token) {
        toast.success("Login link generated!")
        setTempToken({ token: data.token, candidate_id: data.candidate_id })
      } else {
        toast.error(data.detail || "Failed to find email.")
      }
    } catch (error) {
      toast.error("Network error")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCandidateLogin = async (token: string, candidateId: string) => {
    try {
      const res = await fetch("/api/auth/candidate-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_id: candidateId, token })
      })
      if (res.ok) {
        localStorage.setItem("candidate_token", token)
        localStorage.setItem("candidate_id", candidateId)
        toast.success("Login successful!")
        router.push("/candidate/portal")
      } else {
        toast.error("Invalid token")
      }
    } catch (e) {
      toast.error("Login failed")
    }
  }

  const handleRecruiterLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      const response = await fetch("/api/auth/recruiter-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: recruiterEmail,
          password: recruiterPassword,
          role: recruiterRole,
        }),
      })
      const data = await response.json()
      if (response.ok) {
        localStorage.setItem("recruiter_token", data.token)
        router.push("/recruiter/dashboard")
      } else {
        toast.error(data.detail || "Login failed")
      }
    } catch (error) {
      toast.error("An error occurred.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleRecruiterRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      const response = await fetch("/api/auth/recruiter/register", { // Proxy should handle this path if configured, else full URL or fix next.config
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: recruiterEmail,
          password: recruiterPassword,
          name: recruiterName || undefined,
        }),
      })
      const data = await response.json()
      if (response.ok) {
        localStorage.setItem("recruiter_token", data.access_token)
        toast.success("Registration successful!")
        router.push("/recruiter/dashboard")
      } else {
        toast.error(data.detail || "Registration failed")
      }
    } catch (error) {
      toast.error("An error occurred.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleRecruiterSubmit = (e: React.FormEvent) => {
    if (isRegistering) {
      handleRecruiterRegister(e)
    } else {
      handleRecruiterLogin(e)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Hire Smart</h1>
          <p className="text-slate-600 mt-2">Resume Shortlisting & Candidate Guidance</p>
        </div>

        <Tabs
          value={defaultTab}
          onValueChange={(v) => setDefaultTab(v as "candidate" | "recruiter")}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="candidate">Candidate</TabsTrigger>
            <TabsTrigger value="recruiter">Recruiter</TabsTrigger>
          </TabsList>

          <TabsContent value="candidate" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Candidate Login</CardTitle>
                <CardDescription>Enter your email to receive a login link.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    placeholder="alice@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>

                {tempToken && (
                  <div className="bg-green-50 border border-green-200 rounded-md p-4">
                    <div className="text-sm">
                      <p className="font-semibold text-green-800 mb-2">Simulated Email (Dev Mode)</p>
                      <Button
                        variant="link"
                        className="h-auto p-0 text-blue-600 underline"
                        onClick={() => handleCandidateLogin(tempToken.token, tempToken.candidate_id)}
                      >
                        Login as {email}
                      </Button>
                    </div>
                  </div>
                )}

                <Button className="w-full" onClick={handleRequestToken} disabled={isLoading}>
                  {isLoading ? "Sending..." : "Send Login Link"}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recruiter" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>{isRegistering ? "Recruiter Sign Up" : "Recruiter Login"}</CardTitle>
                <CardDescription>
                  {isRegistering ? "Create a new account" : "Sign in to dashboard"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleRecruiterSubmit} className="space-y-4">
                  {isRegistering && (
                    <div className="space-y-2">
                      <Label htmlFor="recruiter-name">Full Name</Label>
                      <Input
                        id="recruiter-name"
                        type="text"
                        placeholder="John Doe"
                        value={recruiterName}
                        onChange={(e) => setRecruiterName(e.target.value)}
                      />
                    </div>
                  )}
                  <div className="space-y-2">
                    <Label htmlFor="recruiter-email">Email</Label>
                    <Input
                      id="recruiter-email"
                      type="email"
                      placeholder="hr@company.com"
                      value={recruiterEmail}
                      onChange={(e) => setRecruiterEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="recruiter-password">Password</Label>
                    <Input
                      id="recruiter-password"
                      type="password"
                      value={recruiterPassword}
                      onChange={(e) => setRecruiterPassword(e.target.value)}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? "Processing..." : (isRegistering ? "Create Account" : "Sign In")}
                  </Button>
                </form>
                <div className="mt-4 text-center text-sm">
                  {isRegistering ? (
                    <p>Already have an account? <button onClick={() => setIsRegistering(false)} className="text-blue-600 underline">Sign In</button></p>
                  ) : (
                    <p>New to Hire Smart? <button onClick={() => setIsRegistering(true)} className="text-blue-600 underline">Sign Up</button></p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="mt-6 text-center text-sm text-slate-600">
          <Link href="/" className="text-blue-600 hover:text-blue-700 font-medium">← Back to Home</Link>
        </div>
      </div >
    </div >
  )
}

export default function AuthPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <AuthContent />
    </Suspense>
  )
}
