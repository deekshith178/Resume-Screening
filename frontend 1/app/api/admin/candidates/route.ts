import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
    try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const token = request.headers.get("authorization")?.replace("Bearer ", "")
        const { searchParams } = new URL(request.url)
        const recruiterId = searchParams.get("recruiter_id")

        if (!token) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
        }

        let url = `${API_URL}/admin/candidates`
        if (recruiterId) {
            url += `?recruiter_id=${recruiterId}`
        }

        const response = await fetch(url, {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { error: data.detail || "Failed to fetch candidates" },
                { status: response.status }
            )
        }

        return NextResponse.json(data, { status: 200 })
    } catch (error) {
        console.error("Fetch candidates error:", error)
        return NextResponse.json({ error: "Internal server error" }, { status: 500 })
    }
}


