import { type NextRequest, NextResponse } from "next/server"

export async function PUT(
    request: NextRequest,
    props: { params: Promise<{ candidateId: string }> }
) {
    try {
        const params = await props.params
        const { candidateId } = params
        const body = await request.json()
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const token = request.headers.get("authorization")?.replace("Bearer ", "")

        if (!token) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
        }

        const response = await fetch(`${API_URL}/admin/candidates/${candidateId}`, {
            method: "PUT",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { error: data.detail || "Failed to update candidate" },
                { status: response.status }
            )
        }

        return NextResponse.json(data, { status: 200 })
    } catch (error) {
        console.error("Update candidate error:", error)
        return NextResponse.json({ error: "Internal server error" }, { status: 500 })
    }
}

export async function DELETE(
    request: NextRequest,
    props: { params: Promise<{ candidateId: string }> }
) {
    try {
        const params = await props.params
        const { candidateId } = params
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const token = request.headers.get("authorization")?.replace("Bearer ", "")

        if (!token) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
        }

        const response = await fetch(`${API_URL}/admin/candidates/${candidateId}`, {
            method: "DELETE",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { error: data.detail || "Failed to delete candidate" },
                { status: response.status }
            )
        }

        return NextResponse.json(data, { status: 200 })
    } catch (error) {
        console.error("Delete candidate error:", error)
        return NextResponse.json({ error: "Internal server error" }, { status: 500 })
    }
}


