"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import RecruiterHeader from "@/components/recruiter/recruiter-header"
import { Bell, Lock, User, Palette, Save } from "lucide-react"

export default function SettingsPage() {
  const [profile, setProfile] = useState({
    name: "John Recruiter",
    email: "john@company.com",
    company: "Tech Recruiting Co.",
    phone: "+1-555-123-4567",
  })

  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    pushNotifications: true,
    weeklyDigest: false,
    darkMode: false,
    language: "en",
  })

  const handleSave = () => {
    console.log("Settings saved:", { profile, preferences })
  }

  return (
    <div className="min-h-screen bg-background">
      <RecruiterHeader />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-2">Manage your account and preferences</p>
        </div>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile" className="flex gap-2">
              <User className="w-4 h-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex gap-2">
              <Bell className="w-4 h-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="appearance" className="flex gap-2">
              <Palette className="w-4 h-4" />
              Appearance
            </TabsTrigger>
            <TabsTrigger value="privacy" className="flex gap-2">
              <Lock className="w-4 h-4" />
              Privacy
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Update your account details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Full Name</label>
                  <Input
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    placeholder="Your name"
                    className="mt-2"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Email Address</label>
                  <Input
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    type="email"
                    placeholder="your@email.com"
                    className="mt-2"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Company</label>
                  <Input
                    value={profile.company}
                    onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                    placeholder="Company name"
                    className="mt-2"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Phone</label>
                  <Input
                    value={profile.phone}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    placeholder="Phone number"
                    className="mt-2"
                  />
                </div>
                <Button onClick={handleSave} gap-2>
                  <Save className="w-4 h-4" />
                  Save Changes
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Control how you receive updates</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  {
                    id: "email",
                    label: "Email Notifications",
                    description: "Receive updates via email",
                    state: preferences.emailNotifications,
                    setState: (val: boolean) => setPreferences({ ...preferences, emailNotifications: val }),
                  },
                  {
                    id: "push",
                    label: "Push Notifications",
                    description: "Real-time in-app notifications",
                    state: preferences.pushNotifications,
                    setState: (val: boolean) => setPreferences({ ...preferences, pushNotifications: val }),
                  },
                  {
                    id: "digest",
                    label: "Weekly Digest",
                    description: "Summary email every Monday",
                    state: preferences.weeklyDigest,
                    setState: (val: boolean) => setPreferences({ ...preferences, weeklyDigest: val }),
                  },
                ].map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div>
                      <p className="font-medium text-sm">{item.label}</p>
                      <p className="text-xs text-muted-foreground">{item.description}</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={item.state}
                      onChange={(e) => item.setState(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </div>
                ))}
                <Button onClick={handleSave} gap-2>
                  <Save className="w-4 h-4" />
                  Save Preferences
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Appearance Tab */}
          <TabsContent value="appearance">
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
                <CardDescription>Customize how the app looks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                  <div>
                    <p className="font-medium text-sm">Dark Mode</p>
                    <p className="text-xs text-muted-foreground">Use dark theme</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.darkMode}
                    onChange={(e) => setPreferences({ ...preferences, darkMode: e.target.checked })}
                    className="w-4 h-4"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium">Language</label>
                  <select
                    value={preferences.language}
                    onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
                    className="w-full mt-2 p-2 border border-border rounded-lg bg-background"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                  </select>
                </div>

                <Button onClick={handleSave} gap-2>
                  <Save className="w-4 h-4" />
                  Save Settings
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Privacy Tab */}
          <TabsContent value="privacy">
            <Card>
              <CardHeader>
                <CardTitle>Privacy & Security</CardTitle>
                <CardDescription>Manage security settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-muted/50 rounded-lg border border-border">
                  <p className="font-medium text-sm mb-3">Password</p>
                  <Button variant="outline">Change Password</Button>
                </div>

                <div className="p-4 bg-muted/50 rounded-lg border border-border">
                  <p className="font-medium text-sm mb-3">Two-Factor Authentication</p>
                  <p className="text-sm text-muted-foreground mb-3">Add extra security to your account</p>
                  <Button variant="outline">Enable 2FA</Button>
                </div>

                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <p className="font-medium text-sm text-red-900 mb-3">Danger Zone</p>
                  <Button variant="outline" className="text-red-600 hover:text-red-700 bg-transparent">
                    Delete Account
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
