import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
    try {
        const { email, password } = await request.json()

        if (!email || !password) {
            return NextResponse.json(
                { detail: "Email and password are required" },
                { status: 400 }
            )
        }

        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

        const response = await fetch(`${API_URL}/auth/recruiter/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, password }),
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { detail: data.detail || "Registration failed" },
                { status: response.status }
            )
        }

        // Backend returns { access_token, token_type, email, role }
        return NextResponse.json(data, { status: 200 })
    } catch (error) {
        console.error("Recruiter registration error:", error)
        return NextResponse.json(
            { detail: "Internal server error" },
            { status: 500 }
        )
    }
}
