import { NextRequest, NextResponse } from "next/server";
import { onboardingSchema } from "@/lib/schemas/onboarding";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate with Zod on the server side
    const validation = onboardingSchema.safeParse(body);
    if (!validation.success) {
      return NextResponse.json(
        {
          error: "Validation failed",
          details: validation.error.flatten().fieldErrors,
        },
        { status: 400 }
      );
    }

    // Get auth token from request
    const authHeader = request.headers.get("authorization");
    if (!authHeader) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    // Forward to FastAPI backend with auth header
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/onboarding`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": authHeader,
      },
      body: JSON.stringify(validation.data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.error || errorData.detail || "Backend request failed" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error("API route error:", error);
    
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
