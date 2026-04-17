"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, CheckCircle2, Zap } from "lucide-react"

export default function Home() {
  const [userType, setUserType] = useState<"recruiter" | "candidate" | null>(null)

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary via-background to-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold">H</span>
              </div>
              <span className="font-semibold text-lg">HireFlow</span>
            </div>
            <div className="flex gap-4">
              <Link href="/auth">
                <Button variant="ghost">Recruiter Login</Button>
              </Link>
              <Link href="/auth">
                <Button variant="outline">Candidate Login</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="max-w-3xl mx-auto text-center mb-20">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 text-balance">Intelligent Resume Screening in Minutes</h1>
          <p className="text-xl text-muted-foreground mb-8">
            AI-powered shortlisting with hybrid candidate detection. Help rejected candidates find their perfect fit
            with personalized guidance.
          </p>

          {!userType ? (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="gap-2" onClick={() => setUserType("recruiter")}>
                For Recruiters <ArrowRight className="w-4 h-4" />
              </Button>
              <Button size="lg" variant="secondary" className="gap-2" onClick={() => setUserType("candidate")}>
                For Candidates <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href={userType === "recruiter" ? "/auth?tab=recruiter" : "/auth?tab=candidate"}>
                <Button size="lg" className="gap-2">
                  Go to {userType === "recruiter" ? "Recruiter" : "Candidate"} Dashboard{" "}
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" onClick={() => setUserType(null)}>
                Back
              </Button>
            </div>
          )}
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 mt-20">
          <div className="bg-card border border-border rounded-xl p-6">
            <Zap className="w-8 h-8 text-accent mb-4" />
            <h3 className="text-lg font-semibold mb-2">Fast Processing</h3>
            <p className="text-muted-foreground">
              Process hundreds of resumes with NLP-powered extraction and intelligent scoring.
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-6">
            <CheckCircle2 className="w-8 h-8 text-accent mb-4" />
            <h3 className="text-lg font-semibold mb-2">Full Control</h3>
            <p className="text-muted-foreground">
              Adjust scoring weights, override decisions, and maintain complete visibility over the process.
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-6">
            <Zap className="w-8 h-8 text-accent mb-4" />
            <h3 className="text-lg font-semibold mb-2">Candidate Support</h3>
            <p className="text-muted-foreground">
              Provide rejected candidates with k-NN powered personalized guidance and learning paths.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
