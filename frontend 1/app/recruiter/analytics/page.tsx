"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import RecruiterHeader from "@/components/recruiter/recruiter-header"
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { TrendingUp, Users, Target, Clock } from "lucide-react"

const candidateData = [
  { month: "Jan", applications: 45, shortlisted: 12, hired: 3 },
  { month: "Feb", applications: 52, shortlisted: 18, hired: 5 },
  { month: "Mar", applications: 48, shortlisted: 15, hired: 4 },
  { month: "Apr", applications: 61, shortlisted: 22, hired: 6 },
  { month: "May", applications: 55, shortlisted: 20, hired: 5 },
  { month: "Jun", applications: 67, shortlisted: 25, hired: 7 },
]

const statusDistribution = [
  { name: "Shortlisted", value: 25, color: "#10b981" },
  { name: "Pending", value: 35, color: "#3b82f6" },
  { name: "Rejected", value: 40, color: "#ef4444" },
]

const jobMetrics = [
  { title: "Total Applications", value: 328, change: "+12% from last month", icon: Users },
  { title: "Shortlist Rate", value: "28%", change: "+5% improvement", icon: Target },
  { title: "Avg. Time to Hire", value: "21 days", change: "-3 days", icon: Clock },
  { title: "Hiring Success", value: "94%", change: "+2% from last quarter", icon: TrendingUp },
]

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-background">
      <RecruiterHeader />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Recruitment Analytics</h1>
          <p className="text-muted-foreground mt-2">Track hiring metrics and performance trends</p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {jobMetrics.map((metric, idx) => {
            const Icon = metric.icon
            return (
              <Card key={idx}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{metric.title}</p>
                      <p className="text-2xl font-bold mt-2">{metric.value}</p>
                      <p className="text-xs text-green-600 mt-2">{metric.change}</p>
                    </div>
                    <Icon className="w-8 h-8 text-muted-foreground opacity-50" />
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Charts */}
        <Tabs defaultValue="trends" className="space-y-6">
          <TabsList>
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="status">Status Distribution</TabsTrigger>
            <TabsTrigger value="jobs">By Job Position</TabsTrigger>
          </TabsList>

          <TabsContent value="trends">
            <Card>
              <CardHeader>
                <CardTitle>Application & Hiring Trends</CardTitle>
                <CardDescription>Monthly data for the last 6 months</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={candidateData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="applications" fill="#3b82f6" />
                    <Bar dataKey="shortlisted" fill="#10b981" />
                    <Bar dataKey="hired" fill="#f59e0b" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="status">
            <Card>
              <CardHeader>
                <CardTitle>Candidate Status Distribution</CardTitle>
                <CardDescription>Current pipeline breakdown</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col lg:flex-row gap-8">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={statusDistribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {statusDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>

                  <div className="space-y-4">
                    {statusDistribution.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                          <span className="text-sm">{item.name}</span>
                        </div>
                        <span className="font-semibold">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="jobs">
            <Card>
              <CardHeader>
                <CardTitle>Performance by Job Position</CardTitle>
                <CardDescription>Metrics broken down by role</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    {
                      job: "Senior React Developer",
                      applications: 48,
                      shortlisted: 12,
                      hired: 3,
                      fillRate: "100%",
                    },
                    {
                      job: "Product Manager",
                      applications: 35,
                      shortlisted: 8,
                      hired: 2,
                      fillRate: "50%",
                    },
                    {
                      job: "Data Analyst",
                      applications: 42,
                      shortlisted: 5,
                      hired: 2,
                      fillRate: "25%",
                    },
                  ].map((job, idx) => (
                    <div key={idx} className="border border-border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <p className="font-medium">{job.job}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {job.applications} applications • {job.shortlisted} shortlisted • {job.hired} hired
                          </p>
                        </div>
                        <span className="text-sm font-semibold text-green-600">{job.fillRate} filled</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div className="bg-primary h-2 rounded-full" style={{ width: job.fillRate }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
