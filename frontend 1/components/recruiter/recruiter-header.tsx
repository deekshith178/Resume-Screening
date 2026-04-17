"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { LogOut, Settings, Bell, User, Shield } from "lucide-react"

export default function RecruiterHeader() {
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    // Check if user is admin
    const checkAdmin = async () => {
      const token = localStorage.getItem("recruiter_token")
      if (!token) return

      try {
        const response = await fetch("/api/recruiters/me", {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (response.ok) {
          const profile = await response.json()
          setIsAdmin(profile.role === "admin")
        }
      } catch (error) {
        console.error("Failed to check admin status:", error)
      }
    }

    checkAdmin()
  }, [])

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold">H</span>
            </div>
            <span className="font-semibold">HireFlow</span>
            <span className="text-xs bg-primary/20 text-primary px-2 py-1 rounded">
              {isAdmin ? (
                <span className="flex items-center gap-1">
                  <Shield className="w-3 h-3" />
                  Admin
                </span>
              ) : (
                "Recruiter"
              )}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {isAdmin && (
              <Button variant="ghost" size="sm" asChild>
                <Link href="/admin/dashboard">Admin Dashboard</Link>
              </Button>
            )}
            <Button variant="ghost" size="icon">
              <Bell className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" asChild>
              <Link href="/recruiter/profile">
                <User className="w-4 h-4" />
              </Link>
            </Button>
            <Button variant="ghost" size="icon" asChild>
              <Link href="/">
                <LogOut className="w-4 h-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}
