import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
    try {
        const body = await req.json()
        const { email } = body

        const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
        const res = await fetch(`${backendUrl}/auth/candidate/request-token`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        })

        if (!res.ok) {
            const error = await res.json()
            return NextResponse.json(error, { status: res.status })
        }

        const data = await res.json()
        return NextResponse.json(data)
    } catch (error) {
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 })
    }
}
