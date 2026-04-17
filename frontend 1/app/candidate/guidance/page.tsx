"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import CandidateHeader from "@/components/candidate/candidate-header"
import GuidanceDetails from "@/components/candidate/guidance-details"
import { BookOpen, CheckCircle2, Calendar } from "lucide-react"

export default function GuidancePage() {
  const [completedItems, setCompletedItems] = useState<string[]>(["Python Basics"])

  return (
    <div className="min-h-screen bg-background">
      <CandidateHeader />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Your Learning Path</h1>
          <p className="text-muted-foreground mt-2">Personalized recommendations to improve your skills</p>
        </div>

        <Tabs defaultValue="learning" className="space-y-6">
          <TabsList>
            <TabsTrigger value="learning">Learning Path</TabsTrigger>
            <TabsTrigger value="progress">Progress</TabsTrigger>
            <TabsTrigger value="history">Completion History</TabsTrigger>
          </TabsList>

          <TabsContent value="learning">
            <GuidanceDetails />
          </TabsContent>

          <TabsContent value="progress" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Overall Progress</CardTitle>
                <CardDescription>Your learning journey milestones</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                      <div>
                        <p className="font-medium">Python Fundamentals</p>
                        <p className="text-xs text-muted-foreground">Completed</p>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground">2024-11-15</span>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <BookOpen className="w-5 h-5 text-primary" />
                      <div>
                        <p className="font-medium">Machine Learning Basics</p>
                        <p className="text-xs text-muted-foreground">In Progress - 65% complete</p>
                      </div>
                    </div>
                    <div className="w-12 h-12 rounded-full border-4 border-primary/20 flex items-center justify-center text-xs font-bold">
                      65%
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg opacity-50">
                    <div className="flex items-center gap-3">
                      <Calendar className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Advanced Python</p>
                        <p className="text-xs text-muted-foreground">Coming Soon</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history">
            <Card>
              <CardHeader>
                <CardTitle>Completion History</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {completedItems.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No completed items yet</p>
                  ) : (
                    completedItems.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200"
                      >
                        <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-green-900">{item}</p>
                          <p className="text-xs text-green-700">Completed on 2024-11-15</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
