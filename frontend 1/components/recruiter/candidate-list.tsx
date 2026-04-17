"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MoreHorizontal, AlertCircle } from "lucide-react"

interface Candidate {
  id: string
  name: string
  email: string
  score: number
  status: "shortlisted" | "rejected" | "pending"
  skills: string[]
  experience: number
  hybrid: boolean
}

interface CandidateListProps {
  candidates: Candidate[]
  onStatusChange: (id: string, status: Candidate["status"]) => void
}

export default function CandidateList({ candidates, onStatusChange }: CandidateListProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "shortlisted":
        return "bg-accent/20 text-accent"
      case "pending":
        return "bg-primary/20 text-primary"
      case "rejected":
        return "bg-destructive/20 text-destructive"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  return (
    <div className="space-y-3">
      {candidates.map((candidate) => (
        <div
          key={candidate.id}
          className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/30 transition"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold truncate">{candidate.name || "Unknown Candidate"}</h3>
              {candidate.hybrid && (
                <AlertCircle className="w-4 h-4 text-primary flex-shrink-0" />
              )}
            </div>
            <p className="text-sm text-muted-foreground">{candidate.email || "No email"}</p>
            {candidate.skills && Array.isArray(candidate.skills) && candidate.skills.length > 0 && (
              <div className="flex gap-1 mt-2 flex-wrap">
                {candidate.skills.slice(0, 3).map((skill, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {skill}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center gap-4 ml-4">
            <div className="text-right">
              <div className="text-2xl font-bold text-primary">{candidate.score}</div>
              <div className="text-xs text-muted-foreground">{candidate.experience}y exp</div>
            </div>
            <Badge className={getStatusColor(candidate.status)}>{candidate.status}</Badge>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onStatusChange(candidate.id, "shortlisted")}>
                  Shortlist
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onStatusChange(candidate.id, "pending")}>
                  Mark as Pending
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onStatusChange(candidate.id, "rejected")}>Reject</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      ))}
    </div>
  )
}
