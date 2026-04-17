"use client"

import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"

interface ScoreWeightsProps {
  weights: Record<string, number>
  setWeights: (weights: Record<string, number>) => void
}

export default function ScoreWeights({ weights, setWeights }: ScoreWeightsProps) {
  const handleWeightChange = (key: string, value: number[]) => {
    setWeights({ ...weights, [key]: value[0] })
  }

  const total = Object.values(weights).reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-4">
      {Object.entries(weights).map(([key, value]) => (
        <div key={key} className="space-y-2">
          <div className="flex justify-between items-center">
            <Label className="capitalize">{key}</Label>
            <span className="text-sm font-semibold">{Math.round((value / total) * 100)}%</span>
          </div>
          <Slider
            value={[value]}
            onValueChange={(v) => handleWeightChange(key, v)}
            max={100}
            step={1}
            className="w-full"
          />
        </div>
      ))}
      <div className="pt-2 border-t border-border">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Total Weight</span>
          <span className="font-semibold">100%</span>
        </div>
      </div>
    </div>
  )
}
