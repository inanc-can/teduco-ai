import { NextRequest, NextResponse } from "next/server";
import { onboardingSchema } from "@/lib/schemas/onboarding";
import { api, isApiError } from "@/lib/api-client";

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

    // Forward to FastAPI backend using api-client
    const data = await api.onboarding.submit(validation.data);
    
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error("API route error:", error);
    
    // Handle ApiError with proper status codes
    if (isApiError(error)) {
      return NextResponse.json(
        { error: error.message, details: error.details },
        { status: error.status || 500 }
      );
    }
    
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
