import Link from "next/link"
import { Button } from "@/components/ui/button"
import { LogOut, Settings, Bell, User, Shield } from "lucide-react"

export default function AdminHeader() {
  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold">H</span>
            </div>
            <span className="font-semibold">HireFlow</span>
            <span className="text-xs bg-purple-500/20 text-purple-600 dark:text-purple-400 px-2 py-1 rounded flex items-center gap-1">
              <Shield className="w-3 h-3" />
              Admin
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/recruiter/dashboard">Recruiter Dashboard</Link>
            </Button>
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


