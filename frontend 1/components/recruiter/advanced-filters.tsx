"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Filter, X } from "lucide-react"

interface FilterState {
  scoreRange: [number, number]
  skills: string[]
  experienceRange: [number, number]
  hybrid: boolean
  status: string[]
}

interface AdvancedFiltersProps {
  onFilterChange: (filters: FilterState) => void
}

export default function AdvancedFilters({ onFilterChange }: AdvancedFiltersProps) {
  const [filters, setFilters] = useState<FilterState>({
    scoreRange: [0, 100],
    skills: [],
    experienceRange: [0, 20],
    hybrid: false,
    status: [],
  })

  const [expanded, setExpanded] = useState(false)
  const availableSkills = ["Python", "React", "Node.js", "Machine Learning", "Java", "Vue.js"]
  const statusOptions = ["shortlisted", "pending", "rejected"]

  const handleSkillToggle = (skill: string) => {
    const updated = filters.skills.includes(skill)
      ? filters.skills.filter((s) => s !== skill)
      : [...filters.skills, skill]
    const newFilters = { ...filters, skills: updated }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleStatusToggle = (status: string) => {
    const updated = filters.status.includes(status)
      ? filters.status.filter((s) => s !== status)
      : [...filters.status, status]
    const newFilters = { ...filters, status: updated }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const clearFilters = () => {
    const cleared = {
      scoreRange: [0, 100] as [number, number],
      skills: [],
      experienceRange: [0, 20] as [number, number],
      hybrid: false,
      status: [],
    }
    setFilters(cleared)
    onFilterChange(cleared)
  }

  const hasActiveFilters = filters.skills.length > 0 || filters.status.length > 0 || filters.hybrid

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            <div>
              <CardTitle className="text-base">Filters</CardTitle>
              {hasActiveFilters && (
                <Badge variant="secondary" className="ml-2">
                  {filters.skills.length + filters.status.length}
                </Badge>
              )}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)} className="text-xs">
            {expanded ? "Hide" : "Show"}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-6">
          {/* Score Range */}
          <div>
            <p className="text-sm font-medium mb-3">
              Score Range: {filters.scoreRange[0]} - {filters.scoreRange[1]}
            </p>
            <Slider
              value={filters.scoreRange}
              onValueChange={(value) => {
                const newFilters = { ...filters, scoreRange: value as [number, number] }
                setFilters(newFilters)
                onFilterChange(newFilters)
              }}
              min={0}
              max={100}
              step={5}
              className="w-full"
            />
          </div>

          {/* Skills Filter */}
          <div>
            <p className="text-sm font-medium mb-2">Skills</p>
            <div className="flex flex-wrap gap-2">
              {availableSkills.map((skill) => (
                <Button
                  key={skill}
                  variant={filters.skills.includes(skill) ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleSkillToggle(skill)}
                  className="text-xs"
                >
                  {skill}
                </Button>
              ))}
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <p className="text-sm font-medium mb-2">Status</p>
            <div className="space-y-2">
              {statusOptions.map((status) => (
                <div key={status} className="flex items-center space-x-2">
                  <Checkbox
                    id={status}
                    checked={filters.status.includes(status)}
                    onCheckedChange={() => handleStatusToggle(status)}
                  />
                  <label htmlFor={status} className="text-sm cursor-pointer capitalize">
                    {status}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Hybrid Filter */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="hybrid"
              checked={filters.hybrid}
              onCheckedChange={(checked) => {
                const newFilters = { ...filters, hybrid: checked as boolean }
                setFilters(newFilters)
                onFilterChange(newFilters)
              }}
            />
            <label htmlFor="hybrid" className="text-sm cursor-pointer">
              Hybrid Role Fit Only
            </label>
          </div>

          {/* Clear Button */}
          {hasActiveFilters && (
            <Button variant="outline" size="sm" onClick={clearFilters} className="w-full gap-2 bg-transparent">
              <X className="w-4 h-4" />
              Clear Filters
            </Button>
          )}
        </CardContent>
      )}
    </Card>
  )
}
