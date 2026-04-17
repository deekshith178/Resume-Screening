"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { BookOpen, Award, Code, TrendingUp } from "lucide-react"

interface GuidanceItem {
  category: string
  skills: string[]
  resources: string[]
  estimatedTime: string
  priority: "high" | "medium" | "low"
}

const guidanceData: GuidanceItem[] = [
  {
    category: "Machine Learning",
    skills: ["TensorFlow", "PyTorch", "Scikit-learn"],
    resources: ["Andrew Ng's ML Course", "Fast.ai", "Kaggle Competitions"],
    estimatedTime: "3 months",
    priority: "high",
  },
  {
    category: "Advanced Python",
    skills: ["Async Programming", "Decorators", "Type Hints"],
    resources: ["Real Python", "Fluent Python Book", "Python Docs"],
    estimatedTime: "4 weeks",
    priority: "medium",
  },
  {
    category: "Cloud Deployment",
    skills: ["Docker", "Kubernetes", "AWS"],
    resources: ["Docker Docs", "Kubernetes Tutorial", "AWS Training"],
    estimatedTime: "2 months",
    priority: "medium",
  },
]

export default function GuidanceDetails() {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-red-100 text-red-800"
      case "medium":
        return "bg-yellow-100 text-yellow-800"
      case "low":
        return "bg-green-100 text-green-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Your Personalized Learning Path</CardTitle>
          <CardDescription>Based on successful candidates in similar roles</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {guidanceData.map((item, idx) => (
            <div key={idx} className="border border-border rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                  <Code className="w-5 h-5 text-primary" />
                  {item.category}
                </h3>
                <Badge className={getPriorityColor(item.priority)}>{item.priority}</Badge>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Key Skills to Learn:</p>
                <div className="flex flex-wrap gap-2">
                  {item.skills.map((skill) => (
                    <Badge key={skill} variant="secondary" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Recommended Resources:</p>
                <ul className="space-y-1">
                  {item.resources.map((resource) => (
                    <li key={resource} className="text-sm flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      {resource}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-4 h-4 text-muted-foreground" />
                  <span>{item.estimatedTime}</span>
                </div>
              </div>

              <Button variant="outline" size="sm" className="w-full bg-transparent">
                <Award className="w-4 h-4 mr-2" />
                Start Learning
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Progress Tracking</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm">Overall Progress</span>
                <span className="text-xs text-muted-foreground">35%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: "35%" }}></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
