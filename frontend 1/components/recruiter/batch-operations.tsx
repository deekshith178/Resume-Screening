"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { ChevronDown, Download, Mail, Trash2 } from "lucide-react"

interface BatchOperationsProps {
  selectedCount: number
  onSelectAll?: () => void
  onClearSelection?: () => void
}

export default function BatchOperations({ selectedCount, onSelectAll, onClearSelection }: BatchOperationsProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (selectedCount === 0) return null

  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">{selectedCount} candidate(s) selected</p>
            <p className="text-xs text-muted-foreground">Choose an action below</p>
          </div>

          <div className="flex items-center gap-2">
            <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
              <DropdownMenuTrigger asChild>
                <Button className="gap-2">
                  Bulk Actions
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem className="flex gap-2">
                  <Mail className="w-4 h-4" />
                  Send Email
                </DropdownMenuItem>
                <DropdownMenuItem className="flex gap-2">
                  <Download className="w-4 h-4" />
                  Export as CSV
                </DropdownMenuItem>
                <DropdownMenuItem className="flex gap-2 text-destructive">
                  <Trash2 className="w-4 h-4" />
                  Delete Selected
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button variant="outline" onClick={onClearSelection}>
              Clear
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
