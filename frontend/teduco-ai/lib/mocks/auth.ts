import type { User } from "../types";

export function getMockSession(): { user: User } | null {
  // Always return a mock user session for demo purposes
  return {
    user: {
      id: "mock-user-1",
      email: "demo@teduco.ai",
      type: "regular",
    },
  };
}

export async function auth() {
  return getMockSession();
}
