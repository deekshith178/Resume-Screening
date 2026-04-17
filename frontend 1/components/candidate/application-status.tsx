import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, Clock } from "lucide-react"

interface ApplicationStatusProps {
  status?: string
}

export default function ApplicationStatus({ status = "new" }: ApplicationStatusProps) {
  let progress = 0
  let statusLabel = "Application Received"

  switch (status) {
    case "new":
      progress = 25
      statusLabel = "Resume Received"
      break
    case "processed":
      progress = 50
      statusLabel = "Analysis Complete"
      break
    case "scored":
      progress = 75
      statusLabel = "Scoring Complete"
      break
    case "shortlisted":
      progress = 100
      statusLabel = "Shortlisted"
      break
    case "rejected":
      progress = 100
      statusLabel = "Not Selected"
      break
    default:
      progress = 0
      statusLabel = "Pending"
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Application Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">{statusLabel}</span>
            <Badge variant={status === "shortlisted" ? "default" : "outline"}>{status ? status.toUpperCase() : "PENDING"}</Badge>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle2 className={`w-5 h-5 flex-shrink-0 mt-0.5 ${progress >= 25 ? "text-accent" : "text-muted"}`} />
            <div>
              <p className="font-medium text-sm">Resume Received</p>
              <p className="text-xs text-muted-foreground">Your resume has been received and parsed</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle2 className={`w-5 h-5 flex-shrink-0 mt-0.5 ${progress >= 50 ? "text-accent" : "text-muted"}`} />
            <div>
              <p className="font-medium text-sm">Skills Analyzed</p>
              <p className="text-xs text-muted-foreground">Your skills have been extracted and normalized</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            {progress >= 75 ? (
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-accent" />
            ) : (
              <Clock className="w-5 h-5 flex-shrink-0 mt-0.5 text-muted" />
            )}
            <div>
              <p className="font-medium text-sm">Scoring Complete</p>
              <p className="text-xs text-muted-foreground">Your profile has been scored against the job requirements</p>
            </div>
          </div>
          {progress >= 100 && (
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-accent" />
              <div>
                <p className="font-medium text-sm">Final Decision</p>
                <p className="text-xs text-muted-foreground">
                  {status === "shortlisted" 
                    ? "Congratulations! You've been shortlisted for this position." 
                    : status === "rejected"
                    ? "Thank you for your interest. We've completed our evaluation."
                    : "Evaluation complete."}
                </p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
