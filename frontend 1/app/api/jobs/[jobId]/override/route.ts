import { NextRequest, NextResponse } from "next/server"

export async function POST(
    request: NextRequest,
    props: { params: Promise<{ jobId: string }> }
) {
    const params = await props.params
    const token = request.headers.get("Authorization")

    if (!token) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const { jobId } = params

    try {
        const body = await request.json()
        const { candidate_id, is_selected } = body

        if (!candidate_id || typeof is_selected !== "boolean") {
            return NextResponse.json(
                { error: "candidate_id and is_selected are required" },
                { status: 400 }
            )
        }

        const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || "http://localhost:8000"
        const res = await fetch(`${backendUrl}/jobs/${jobId}/override`, {
            method: "POST",
            headers: {
                Authorization: token,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                candidate_id,
                is_selected,
            }),
        })

        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: "Failed to override candidate selection" }))
            return NextResponse.json(
                { error: error.detail || "Failed to override candidate selection" },
                { status: res.status }
            )
        }

        const data = await res.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error("Failed to override candidate:", error)
        return NextResponse.json(
            { error: "Internal Server Error" },
            { status: 500 }
        )
    }
}

