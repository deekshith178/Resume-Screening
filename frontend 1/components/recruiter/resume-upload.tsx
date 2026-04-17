"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Upload, X, CheckCircle2 } from "lucide-react"

interface UploadedResume {
  id: string
  name: string
  uploadedAt: string
  status: "processing" | "completed" | "failed"
  score?: number
}

export default function ResumeUpload() {
  const [files, setFiles] = useState<UploadedResume[]>([
    { id: "1", name: "alice-johnson-resume.pdf", uploadedAt: "2024-11-27", status: "completed", score: 92 },
    { id: "2", name: "bob-smith-resume.pdf", uploadedAt: "2024-11-27", status: "completed", score: 78 },
  ])
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsUploading(true)
    setTimeout(() => {
      setUploadProgress(100)
      setTimeout(() => {
        setIsUploading(false)
        setUploadProgress(0)
      }, 500)
    }, 1500)
  }

  const removeFile = (id: string) => {
    setFiles(files.filter((f) => f.id !== id))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resume Management</CardTitle>
        <CardDescription>Upload and manage candidate resumes</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Upload Area */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-border rounded-lg cursor-pointer hover:border-primary/50 transition"
        >
          <div className="text-center">
            <Upload className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
            <span className="text-sm font-medium">Drop resumes or click to upload</span>
            <span className="text-xs text-muted-foreground">PDF, DOCX, TXT supported</span>
            <input type="file" className="hidden" multiple accept=".pdf,.docx,.txt" />
          </div>
        </div>

        {isUploading && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} className="h-2" />
          </div>
        )}

        {/* Uploaded Files List */}
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Uploaded Files ({files.length})</h3>
          {files.map((file) => (
            <div key={file.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-3 flex-1">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{file.uploadedAt}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {file.score && <Badge variant="secondary">{file.score}</Badge>}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(file.id)}
                  className="hover:bg-destructive/10"
                >
                  <X className="w-4 h-4 text-destructive" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        <Button className="w-full">Proceed to Screening</Button>
      </CardContent>
    </Card>
  )
}
