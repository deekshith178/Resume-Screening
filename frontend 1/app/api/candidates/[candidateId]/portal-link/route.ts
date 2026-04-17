import { NextRequest, NextResponse } from "next/server"

export async function POST(
    request: NextRequest,
    props: { params: Promise<{ candidateId: string }> }
) {
    const params = await props.params
    const token = request.headers.get("Authorization")

    if (!token) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const { candidateId } = params

    try {
        const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
        const res = await fetch(`${backendUrl}/candidates/${candidateId}/portal-link`, {
            method: "POST",
            headers: {
                Authorization: token,
                "Content-Type": "application/json",
            },
        })

        if (!res.ok) {
            const error = await res.text()
            return NextResponse.json({ error }, { status: res.status })
        }

        const data = await res.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error("Failed to generate portal link:", error)
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
    }
}
