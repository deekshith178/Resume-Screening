import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface ScoreBreakdownProps {
  score?: number
  components?: {
    normalized_similarity?: number
    E_norm?: number
    P_norm?: number
    C_norm?: number
  }
}

export default function ScoreBreakdown({ score, components }: ScoreBreakdownProps) {
  const overallScore = score ? Math.round(score * 100) : 0

  // Use real components if available, otherwise fallback to simulated data
  let scoreData: Array<{ category: string; value: number }> = []
  
  if (components) {
    // Convert normalized values (0-1) to percentages (0-100)
    scoreData = [
      { 
        category: "Skills Match", 
        value: components.normalized_similarity 
          ? Math.round(components.normalized_similarity * 100) 
          : 0 
      },
      { 
        category: "Experience", 
        value: components.E_norm 
          ? Math.round(components.E_norm * 100) 
          : 0 
      },
      { 
        category: "Projects", 
        value: components.P_norm 
          ? Math.round(components.P_norm * 100) 
          : 0 
      },
      { 
        category: "Certifications", 
        value: components.C_norm 
          ? Math.round(components.C_norm * 100) 
          : 0 
      },
    ]
  } else {
    // Fallback to simulated breakdown if components not available
    scoreData = [
    { category: "Skills Match", value: Math.min(100, overallScore + 5) },
    { category: "Experience", value: Math.max(0, overallScore - 5) },
    { category: "Projects", value: overallScore },
    { category: "Certifications", value: Math.max(0, overallScore - 10) },
  ]
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Overall Score</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <div className="text-6xl font-bold text-primary mb-2">{overallScore}</div>
          <p className="text-muted-foreground mb-4">
            {overallScore >= 80 ? "Excellent match" : overallScore >= 60 ? "Good potential" : "Low match"} for this position
          </p>
          <Progress value={overallScore} className="h-3" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Score Components</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={scoreData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--color-card)",
                  border: `1px solid var(--color-border)`,
                  borderRadius: "8px",
                }}
              />
              <Bar dataKey="value" fill="var(--color-primary)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Detailed Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {scoreData.map((item) => (
            <div key={item.category}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium">{item.category}</span>
                <span className="text-sm font-semibold text-primary">{item.value}%</span>
              </div>
              <Progress value={item.value} className="h-2" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
