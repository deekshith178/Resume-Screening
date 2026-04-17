import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { BookOpen, ExternalLink, Zap } from "lucide-react"

interface GuidanceItem {
  skill: string
  resources: Array<{ title: string; type: string; url: string; snippet?: string }>
}

const mockGuidance: GuidanceItem[] = [
  {
    skill: "Machine Learning",
    resources: [
      { title: "Andrew Ng ML Course", type: "Course", url: "#" },
      { title: "Kaggle ML Competitions", type: "Practice", url: "#" },
    ],
  },
]

interface GuidanceDashboardProps {
  onOptIn?: () => void
  data?: any // Backend GuidancePreview format
  category?: string
  skills?: string[]
}

export default function GuidanceDashboard({ onOptIn, data, category = "General", skills = [] }: GuidanceDashboardProps) {
  // Map backend data to display format if present
  let displayData: GuidanceItem[] = mockGuidance

  if (data && data.missing_skills && (data.resources || data.suggested_resources)) {
    const rawResources = data.suggested_resources || data.resources
    displayData = data.missing_skills.map((skill: string) => {
      const skillResources = rawResources[skill] || []
      return {
        skill: skill,
        resources: skillResources.map((r: any) => ({
          title: r.title || "Learning Resource",
          type: r.type || "Resource",
          url: r.link || r.url || r,
          snippet: r.snippet || ""
        }))
      }
    })
  }

  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-r from-accent/5 to-primary/5 border-accent/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-accent" />
            Personalized Learning Path
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3">
            {category !== "General" 
              ? `As a ${category} professional, we've analyzed successful candidates in your field and identified key skills to help you advance your career.`
              : "Based on k-NN analysis of successful candidates, we've identified key skills to focus on."}
          </p>
          {skills && skills.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border">
              <p className="text-xs font-medium text-muted-foreground mb-2">Your Current Skills:</p>
              <div className="flex flex-wrap gap-2">
                {skills.slice(0, 10).map((skill: string, idx: number) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))}
                {skills.length > 10 && (
                  <Badge variant="outline" className="text-xs">
                    +{skills.length - 10} more
                  </Badge>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {displayData.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center p-8 text-muted-foreground">
              <p className="mb-2">Great news! No specific skill gaps identified for your {category !== "General" ? `${category} ` : ""}profile.</p>
              <p className="text-sm">You're well-positioned for success. Keep building on your existing skills!</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card className="border-primary/20">
            <CardHeader>
              <CardTitle className="text-lg">Recommended Skills to Develop</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                These skills are commonly found in successful {category !== "General" ? `${category} ` : ""}candidates and can help improve your profile.
              </p>
            </CardContent>
          </Card>
          {displayData.map((item, idx) => (
        <Card key={idx}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{item.skill}</CardTitle>
              <Badge variant="secondary">High Priority</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {item.resources.map((resource, ridx) => (
                <div key={ridx} className="flex items-start justify-between p-4 border border-border rounded-lg hover:bg-accent/5 transition-colors">
                  <div className="flex items-start gap-3 flex-1">
                    <BookOpen className="w-4 h-4 text-muted-foreground mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium mb-1">{resource.title}</p>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs capitalize">
                          {resource.type}
                        </Badge>
                      </div>
                      {resource.snippet && (
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                          {resource.snippet}
                        </p>
                      )}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" className="ml-2 flex-shrink-0" asChild>
                    <a href={resource.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1">
                      <span className="text-xs hidden sm:inline">Open</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
        </>
      )}
    </div>
  )
}
