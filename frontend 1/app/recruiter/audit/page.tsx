"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import RecruiterHeader from "@/components/recruiter/recruiter-header"
import { format } from "date-fns"
import { Download, Search, Loader2 } from "lucide-react"
import { getRecruiterToken } from "@/lib/auth"
import { useRouter } from "next/navigation"

interface AuditLogEntry {
  id: string
  timestamp: string
  action: string
  candidateName: string // mapped from backend response
  candidate_id?: string
  job_id?: string
  recruiter_id?: string
  metadata_json?: string
  oldValue?: string
  newValue?: string
  changedBy: string
  reason?: string
  type: "shortlist" | "reject" | "override" | "publish" | "create_job" | "process_resume" | "weight_change" | "score_update" | "status_change" | "other"
}

export default function AuditPage() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedType, setSelectedType] = useState<string | null>(null)

  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchLogs = async () => {
      const token = getRecruiterToken()
      if (!token) {
        router.push("/auth?tab=recruiter")
        return
      }

      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${API_URL}/audit-logs?limit=100`, {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        })

        if (!res.ok) {
          if (res.status === 401) {
            router.push("/auth?tab=recruiter")
            return
          }
          throw new Error("Failed to fetch logs")
        }

        const data = await res.json()

        // Transform backend logs to frontend format
        const transformedLogs: AuditLogEntry[] = data.items.map((item: any) => {
          let metadata: any = {}
          try {
            metadata = JSON.parse(item.metadata_json || "{}")
          } catch (e) {
            // ignore json error
          }

          // Map known actions to types/styles
          let type: AuditLogEntry["type"] = "other"
          if (item.action.includes("shortlist")) type = "shortlist"
          else if (item.action.includes("reject")) type = "reject"
          else if (item.action.includes("override")) type = "override"
          else if (item.action.includes("publish")) type = "publish"
          else if (item.action.includes("weight")) type = "weight_change"
          else if (item.action === "create_job") type = "create_job"
          else if (item.action === "process_resume") type = "process_resume"

          return {
            id: item.id.toString(),
            timestamp: item.timestamp,
            action: item.action.replace("_", " ").replace(/\b\w/g, (l: string) => l.toUpperCase()), // Title Case
            candidateName: item.candidate_name || "N/A",
            changedBy: item.recruiter_id || "System", // We don't have recruiter name easily, use ID or System
            type: type,
            // Map metadata to old/new/reason if available
            reason: metadata.reason,
            oldValue: metadata.old_value,
            newValue: metadata.new_value || metadata.value,
            // Additional context
            candidate_id: item.candidate_id,
            job_id: item.job_id,
            metadata_json: item.metadata_json
          }
        })

        setLogs(transformedLogs)
      } catch (err) {
        console.error("Error fetching logs:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()
  }, [router])

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.candidateName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.changedBy.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesType = !selectedType || log.type === selectedType

    return matchesSearch && matchesType
  })

  const getTypeColor = (type: string) => {
    switch (type) {
      case "shortlist":
        return "bg-green-100 text-green-800"
      case "reject":
        return "bg-red-100 text-red-800"
      case "override":
        return "bg-orange-100 text-orange-800"
      case "weight_change":
        return "bg-blue-100 text-blue-800"
      case "publish":
        return "bg-teal-100 text-teal-800"
      case "create_job":
        return "bg-purple-100 text-purple-800"
      case "process_resume":
        return "bg-indigo-100 text-indigo-800"
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
            <h1 className="text-3xl font-bold">Audit Logs</h1>
            <p className="text-muted-foreground mt-2">Complete history of all decisions and changes</p>
          </div>
          <Button gap-2 variant="outline">
            <Download className="w-4 h-4" />
            Export
          </Button>
        </div>

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex gap-2">
              <Input
                placeholder="Search by candidate, recruiter, or action..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1"
              />
              <Button variant="outline" size="icon">
                <Search className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="all" className="space-y-6" onValueChange={(val) => setSelectedType(val === "all" ? null : val)}>
          <TabsList>
            <TabsTrigger value="all">All Events</TabsTrigger>
            <TabsTrigger value="process_resume">Resume Uploads</TabsTrigger>
            <TabsTrigger value="create_job">Job Changes</TabsTrigger>
            <TabsTrigger value="override">Overrides</TabsTrigger>
            <TabsTrigger value="publish">Publications</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-3">
            {loading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <>
                {filteredLogs.map((log) => (
                  <Card key={log.id}>
                    <CardContent className="pt-6">
                      <div className="flex gap-4">
                        <Badge className={getTypeColor(log.type)} variant="secondary">{log.type.replace("_", " ")}</Badge>
                        <div className="flex-1">
                          <div className="flex justify-between items-start mb-2">
                            <p className="font-medium">{log.action}</p>
                            <p className="text-xs text-muted-foreground">
                              {format(new Date(log.timestamp), "MMM d, yyyy HH:mm")}
                            </p>
                          </div>

                          <div className="space-y-1 text-sm">
                            <p className="text-muted-foreground">
                              <span className="font-medium">Candidate:</span> {log.candidateName}
                            </p>
                            <p className="text-muted-foreground">
                              <span className="font-medium">User:</span> {log.changedBy}
                            </p>

                            {log.oldValue && log.newValue && (
                              <p className="text-muted-foreground">
                                <span className="font-medium">Change:</span> {log.oldValue} → {log.newValue}
                              </p>
                            )}

                            {/* Generic metadata display if relevant fields missing */}
                            {!log.oldValue && !log.newValue && log.metadata_json && log.metadata_json !== "{}" && (
                              <p className="text-muted-foreground truncate max-w-2xl font-mono text-xs mt-1">
                                {log.metadata_json}
                              </p>
                            )}

                            {log.reason && (
                              <p className="text-muted-foreground">
                                <span className="font-medium">Reason:</span> {log.reason}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {filteredLogs.length === 0 && (
                  <Card>
                    <CardContent className="text-center py-8">
                      <p className="text-muted-foreground">No audit logs found</p>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </TabsContent>

          {/* We only render content for 'all' and rely on client-side filtering via selectedType state 
              which triggers re-render of the list above due to `filteredLogs`. 
              The other tabs are just triggers to set the filter. 
              But TabsContent usually hides content? 
              
              Fix: We used TabsContent value="all" for everything, but if we switch tabs, 
              TabsContent value="all" will hide. 
              We should use a single content area OR duplicate the list logic (which is verbose).
              Better approach: Use Tabs as a filter controller only, and put the list OUTSIDE TabsContent, 
              OR map through TabsContent.
              
              Let's accept the current structure but fix the TabsContent Logic.
              Actually, the original structure had duplicated logical blocks for each tab.
              To keep it simple and robust: I will put the list inside a function or just render it once 
              and remove TabsContent wrappers if I can, OR just make all TabsContent point to the same list.
              
              Actually, ShadCN Tabs will only show the content matching `value`.
              So we MUST implement TabsContent for each value or use a single "custom" tab implementation.
              
              Let's revert to the original pattern: TabsContent for each type. 
              But wait, I simplified the logic to use `filteredLogs`.
              
              Easiest fix: Just render the SAME `filteredLogs` (which respects `selectedType`) 
              inside EACH `TabsContent`? No, because `selectedType` is set by `onValueChange`.
              
              If I use `value={activeTab}` I can control it.
              The original code didn't use controlled tabs state for filtering logic, 
              it used `TabsContent value="shortlist"`. 
              
              I'll just implement `TabsContent` for the new categories I added.
           */}

          {/* Re-implementing specific tabs for compatibility with ShadCN structure */}
          {["process_resume", "create_job", "override", "publish"].map(tabValue => (
            <TabsContent key={tabValue} value={tabValue} className="space-y-3">
              {filteredLogs.map(log => (
                <Card key={log.id}>
                  <CardContent className="pt-6">
                    <div className="flex gap-4">
                      <Badge className={getTypeColor(log.type)} variant="secondary">{log.type.replace("_", " ")}</Badge>
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-2">
                          <p className="font-medium">{log.action}</p>
                          <p className="text-xs text-muted-foreground">
                            {format(new Date(log.timestamp), "MMM d, yyyy HH:mm")}
                          </p>
                        </div>
                        <div className="space-y-1 text-sm">
                          <p className="text-muted-foreground">
                            <span className="font-medium">Candidate:</span> {log.candidateName}
                          </p>
                          {log.metadata_json && (
                            <p className="text-xs text-muted-foreground font-mono">{log.metadata_json}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {filteredLogs.length === 0 && <p className="text-center text-muted-foreground py-8">No logs found for this category.</p>}
            </TabsContent>
          ))}

        </Tabs>
      </main>
    </div>
  )
}
