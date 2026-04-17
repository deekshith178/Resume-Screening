"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import RecruiterHeader from "@/components/recruiter/recruiter-header"
import { Bell, Mail, Settings, Check } from "lucide-react"

interface Notification {
  id: string
  title: string
  message: string
  type: "info" | "success" | "warning" | "alert"
  timestamp: string
  read: boolean
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: "1",
      title: "Application Updated",
      message: "Your application status has been updated to Shortlisted",
      type: "success",
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      read: false,
    },
    {
      id: "2",
      title: "New Candidates",
      message: "5 new candidates have applied for Senior React Developer",
      type: "info",
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      read: false,
    },
    {
      id: "3",
      title: "Screening Complete",
      message: "Resume screening for Product Manager role is complete",
      type: "info",
      timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      read: true,
    },
    {
      id: "4",
      title: "Low Candidates",
      message: "Only 2 candidates remain for Data Analyst role",
      type: "warning",
      timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      read: true,
    },
  ])

  const markAsRead = (id: string) => {
    setNotifications(notifications.map((n) => (n.id === id ? { ...n, read: true } : n)))
  }

  const markAllAsRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, read: true })))
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case "success":
        return "bg-green-100 text-green-800"
      case "warning":
        return "bg-yellow-100 text-yellow-800"
      case "alert":
        return "bg-red-100 text-red-800"
      case "info":
        return "bg-blue-100 text-blue-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <div className="min-h-screen bg-background">
      <RecruiterHeader />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Notifications</h1>
            <p className="text-muted-foreground mt-2">
              {unreadCount > 0 ? `${unreadCount} unread notifications` : "All caught up"}
            </p>
          </div>
          {unreadCount > 0 && (
            <Button onClick={markAllAsRead} variant="outline">
              Mark all as read
            </Button>
          )}
        </div>

        <Tabs defaultValue="all" className="space-y-6">
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="unread">
              Unread
              {unreadCount > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {unreadCount}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="preferences">Preferences</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-3">
            {notifications.map((notif) => (
              <Card key={notif.id} className={notif.read ? "opacity-60" : ""}>
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <Badge className={getTypeColor(notif.type)}>{notif.type}</Badge>
                    <div className="flex-1">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{notif.title}</p>
                          <p className="text-sm text-muted-foreground mt-1">{notif.message}</p>
                          <p className="text-xs text-muted-foreground mt-2">
                            {new Date(notif.timestamp).toLocaleString()}
                          </p>
                        </div>
                        {!notif.read && (
                          <Button variant="ghost" size="sm" onClick={() => markAsRead(notif.id)}>
                            <Check className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="unread" className="space-y-3">
            {notifications
              .filter((n) => !n.read)
              .map((notif) => (
                <Card key={notif.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <Badge className={getTypeColor(notif.type)}>{notif.type}</Badge>
                      <div className="flex-1">
                        <p className="font-medium">{notif.title}</p>
                        <p className="text-sm text-muted-foreground mt-1">{notif.message}</p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => markAsRead(notif.id)}>
                        <Check className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            {unreadCount === 0 && (
              <Card>
                <CardContent className="text-center py-8">
                  <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-2 opacity-50" />
                  <p className="text-muted-foreground">No unread notifications</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="preferences" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Manage how you receive notifications</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4" />
                      <div>
                        <p className="text-sm font-medium">Email Notifications</p>
                        <p className="text-xs text-muted-foreground">Receive updates via email</p>
                      </div>
                    </div>
                    <input type="checkbox" className="w-4 h-4" defaultChecked />
                  </div>

                  <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div className="flex items-center gap-2">
                      <Bell className="w-4 h-4" />
                      <div>
                        <p className="text-sm font-medium">Push Notifications</p>
                        <p className="text-xs text-muted-foreground">Real-time updates in app</p>
                      </div>
                    </div>
                    <input type="checkbox" className="w-4 h-4" defaultChecked />
                  </div>

                  <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div className="flex items-center gap-2">
                      <Settings className="w-4 h-4" />
                      <div>
                        <p className="text-sm font-medium">Daily Digest</p>
                        <p className="text-xs text-muted-foreground">One summary email per day</p>
                      </div>
                    </div>
                    <input type="checkbox" className="w-4 h-4" />
                  </div>
                </div>

                <Button className="w-full">Save Preferences</Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
