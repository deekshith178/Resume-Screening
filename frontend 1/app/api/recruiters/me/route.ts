import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
    try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const token = request.headers.get("authorization")?.replace("Bearer ", "")

        if (!token) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
        }

        const response = await fetch(`${API_URL}/recruiters/me`, {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { error: data.detail || "Failed to fetch profile" },
                { status: response.status }
            )
        }

        return NextResponse.json(data, { status: 200 })
    } catch (error) {
        console.error("Fetch profile error:", error)
        return NextResponse.json({ error: "Internal server error" }, { status: 500 })
    }
}

export async function PUT(request: NextRequest) {
    try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const token = request.headers.get("authorization")?.replace("Bearer ", "")

        if (!token) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
        }

        const body = await request.json()

        const response = await fetch(`${API_URL}/recruiters/me`, {
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
                { error: data.detail || "Failed to update profile" },
                { status: response.status }
            )
        }

        return NextResponse.json(data, { status: 200 })
    } catch (error) {
        console.error("Update profile error:", error)
        return NextResponse.json({ error: "Internal server error" }, { status: 500 })
    }
}
