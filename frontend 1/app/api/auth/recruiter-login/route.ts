import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    if (!email || !password) {
      return NextResponse.json({ error: "Email and password are required" }, { status: 400 })
    }


    // Backend authentication is now active - using real tokens

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

    // Backend expects 'username' (OAuth2 standard), but frontend sends 'email'
    // For now we map email -> username
    const response = await fetch(`${API_URL}/auth/recruiter/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: email,
        password: password,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || "Invalid credentials" },
        { status: response.status }
      )
    }

    // Backend returns { access_token, token_type }
    // Frontend expects { success: true, token, email, role }
    // We decode the token or just pass it back. For MVP we'll default role to 'admin'

    return NextResponse.json(
      {
        success: true,
        token: data.access_token,
        email: email,
        role: "admin", // Backend doesn't return role in login response yet, assume admin
      },
      { status: 200 },
    )
  } catch (error) {
    console.error("Recruiter login error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
