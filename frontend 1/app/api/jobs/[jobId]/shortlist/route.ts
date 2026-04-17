import { NextRequest, NextResponse } from "next/server"

export async function GET(
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
        const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
        const res = await fetch(`${backendUrl}/jobs/${jobId}/shortlist`, {
            headers: {
                Authorization: token,
            },
        })

        if (!res.ok) {
            const error = await res.text()
            return NextResponse.json({ error }, { status: res.status })
        }

        const data = await res.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error("Failed to fetch shortlist:", error)
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
    }
}
