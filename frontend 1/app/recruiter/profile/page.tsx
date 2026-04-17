"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import RecruiterHeader from "@/components/recruiter/recruiter-header"
import { User, Mail, Shield, Briefcase, Users, Key, Save } from "lucide-react"
import { toast } from "sonner"

interface RecruiterProfile {
    id: number
    email: string
    name: string | null
    role: string
    jobs_count: number
    candidates_count: number
}

export default function RecruiterProfilePage() {
    const router = useRouter()
    const [profile, setProfile] = useState<RecruiterProfile | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)

    // Edit states
    const [editName, setEditName] = useState("")
    const [currentPassword, setCurrentPassword] = useState("")
    const [newPassword, setNewPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")

    useEffect(() => {
        fetchProfile()
    }, [])

    const fetchProfile = async () => {
        try {
            const token = localStorage.getItem("recruiter_token")
            if (!token) {
                router.push("/auth?tab=recruiter")
                return
            }

            const response = await fetch("/api/recruiters/me", {
                headers: { Authorization: `Bearer ${token}` },
            })

            if (response.ok) {
                const data = await response.json()
                setProfile(data)
                setEditName(data.name || "")
            } else if (response.status === 401) {
                router.push("/auth?tab=recruiter")
            } else {
                toast.error("Failed to load profile")
            }
        } catch (error) {
            console.error("Error fetching profile:", error)
            toast.error("Failed to load profile")
        } finally {
            setIsLoading(false)
        }
    }

    const handleUpdateProfile = async () => {
        if (newPassword && newPassword !== confirmPassword) {
            toast.error("New passwords don't match")
            return
        }

        setIsSaving(true)
        try {
            const token = localStorage.getItem("recruiter_token")
            const updateData: any = {}

            if (editName !== profile?.name) {
                updateData.name = editName
            }

            if (currentPassword && newPassword) {
                updateData.current_password = currentPassword
                updateData.new_password = newPassword
            }

            if (Object.keys(updateData).length === 0) {
                toast.info("No changes to save")
                setIsSaving(false)
                return
            }

            const response = await fetch("/api/recruiters/me", {
                method: "PUT",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(updateData),
            })

            const data = await response.json()

            if (response.ok) {
                setProfile(data)
                setCurrentPassword("")
                setNewPassword("")
                setConfirmPassword("")
                toast.success("Profile updated successfully!")
            } else {
                toast.error(data.error || "Failed to update profile")
            }
        } catch (error) {
            console.error("Error updating profile:", error)
            toast.error("Failed to update profile")
        } finally {
            setIsSaving(false)
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <RecruiterHeader />
                <main className="container mx-auto px-4 py-8">
                    <div className="flex items-center justify-center h-64">
                        <p className="text-muted-foreground">Loading profile...</p>
                    </div>
                </main>
            </div>
        )
    }

    if (!profile) {
        return (
            <div className="min-h-screen bg-background">
                <RecruiterHeader />
                <main className="container mx-auto px-4 py-8">
                    <div className="flex items-center justify-center h-64">
                        <p className="text-muted-foreground">Failed to load profile</p>
                    </div>
                </main>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background">
            <RecruiterHeader />

            <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="max-w-2xl mx-auto space-y-6">
                    <div>
                        <h1 className="text-2xl font-bold">My Profile</h1>
                        <p className="text-muted-foreground">Manage your account settings</p>
                    </div>

                    {/* Profile Info Card */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <User className="w-5 h-5" />
                                Account Information
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {/* ID */}
                            <div className="flex items-center justify-between py-2 border-b">
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Shield className="w-4 h-4" />
                                    <span>Recruiter ID</span>
                                </div>
                                <span className="font-mono font-medium">{profile.id}</span>
                            </div>

                            {/* Email */}
                            <div className="flex items-center justify-between py-2 border-b">
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Mail className="w-4 h-4" />
                                    <span>Email</span>
                                </div>
                                <span className="font-medium">{profile.email}</span>
                            </div>

                            {/* Role */}
                            <div className="flex items-center justify-between py-2 border-b">
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Shield className="w-4 h-4" />
                                    <span>Role</span>
                                </div>
                                <Badge variant={profile.role === "admin" ? "default" : "secondary"}>
                                    {profile.role.charAt(0).toUpperCase() + profile.role.slice(1)}
                                </Badge>
                            </div>

                            {/* Name - Editable */}
                            <div className="space-y-2 pt-2">
                                <Label htmlFor="name">Full Name</Label>
                                <Input
                                    id="name"
                                    value={editName}
                                    onChange={(e) => setEditName(e.target.value)}
                                    placeholder="Enter your name"
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Stats Card */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">Your Activity</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
                                    <Briefcase className="w-8 h-8 text-primary" />
                                    <div>
                                        <p className="text-2xl font-bold">{profile.jobs_count}</p>
                                        <p className="text-sm text-muted-foreground">Jobs Created</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
                                    <Users className="w-8 h-8 text-accent" />
                                    <div>
                                        <p className="text-2xl font-bold">{profile.candidates_count}</p>
                                        <p className="text-sm text-muted-foreground">Candidates Processed</p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Change Password Card */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Key className="w-5 h-5" />
                                Change Password
                            </CardTitle>
                            <CardDescription>Leave blank to keep current password</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="current-password">Current Password</Label>
                                <Input
                                    id="current-password"
                                    type="password"
                                    value={currentPassword}
                                    onChange={(e) => setCurrentPassword(e.target.value)}
                                    placeholder="Enter current password"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="new-password">New Password</Label>
                                <Input
                                    id="new-password"
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    placeholder="Enter new password"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="confirm-password">Confirm New Password</Label>
                                <Input
                                    id="confirm-password"
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="Confirm new password"
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Save Button */}
                    <Button
                        onClick={handleUpdateProfile}
                        disabled={isSaving}
                        className="w-full"
                        size="lg"
                    >
                        <Save className="w-4 h-4 mr-2" />
                        {isSaving ? "Saving..." : "Save Changes"}
                    </Button>
                </div>
            </main>
        </div>
    )
}
