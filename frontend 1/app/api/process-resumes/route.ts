import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData()
        const files = formData.getAll("files")
        const jobId = formData.get("job_id")

        if (!files || files.length === 0) {
            return NextResponse.json({ error: "No files provided" }, { status: 400 })
        }

        if (!jobId) {
            return NextResponse.json({ error: "Job ID is required" }, { status: 400 })
        }

        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const token = request.headers.get("authorization")?.replace("Bearer ", "")

        if (!token) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
        }

        // Forward the form data to backend
        const backendFormData = new FormData()
        files.forEach((file) => {
            backendFormData.append("files", file as Blob)
        })
        backendFormData.append("job_id", jobId as string)

        // Forward weights if provided
        const weights = formData.get("weights")
        if (weights) {
            backendFormData.append("weights", weights as string)
        }

        const response = await fetch(`${API_URL}/batch-process-resumes`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
            },
            body: backendFormData,
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { error: data.detail || "Failed to process resumes" },
                { status: response.status }
            )
        }

        return NextResponse.json(data, { status: 200 })
    } catch (error) {
        console.error("Process resumes error:", error)
        return NextResponse.json({ error: "Internal server error" }, { status: 500 })
    }
}
