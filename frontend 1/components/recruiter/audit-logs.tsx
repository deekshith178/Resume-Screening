"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { format } from "date-fns"

interface AuditLog {
  id: string
  action: string
  candidateName: string
  changedBy: string
  timestamp: string
  details: string
  type: "shortlist" | "reject" | "override" | "weight_change" | "score_update"
}

const mockLogs: AuditLog[] = [
  {
    id: "1",
    action: "Candidate Shortlisted",
    candidateName: "Alice Johnson",
    changedBy: "John Recruiter",
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    details: "Final score: 92",
    type: "shortlist",
  },
  {
    id: "2",
    action: "Score Override Applied",
    candidateName: "Bob Smith",
    changedBy: "Jane Manager",
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    details: "Overridden score from 78 to 85",
    type: "override",
  },
  {
    id: "3",
    action: "Candidate Rejected",
    candidateName: "Carol Davis",
    changedBy: "John Recruiter",
    timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    details: "Final score: 65",
    type: "reject",
  },
  {
    id: "4",
    action: "Weights Updated",
    candidateName: "N/A",
    changedBy: "Admin User",
    timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    details: "Skills: 50%, Experience: 30%, Projects: 15%, Certificates: 5%",
    type: "weight_change",
  },
]

export default function AuditLogs() {
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
      case "score_update":
        return "bg-purple-100 text-purple-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "shortlist":
        return "Shortlist"
      case "reject":
        return "Reject"
      case "override":
        return "Override"
      case "weight_change":
        return "Weight Change"
      case "score_update":
        return "Score Update"
      default:
        return type
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit Logs</CardTitle>
        <CardDescription>Track all changes and decisions</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockLogs.map((log) => (
            <div key={log.id} className="flex items-start gap-4 pb-4 border-b last:border-b-0">
              <Badge className={getTypeColor(log.type)}>{getTypeLabel(log.type)}</Badge>
              <div className="flex-1 min-w-0">
                <p className="font-medium">{log.action}</p>
                <p className="text-sm text-muted-foreground">{log.candidateName}</p>
                <p className="text-xs text-muted-foreground mt-1">{log.details}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  By {log.changedBy} • {format(new Date(log.timestamp), "MMM d, HH:mm")}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
