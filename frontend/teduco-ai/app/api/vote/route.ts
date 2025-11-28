import { auth } from "@/lib/mocks/auth";
import { mockDataStore } from "@/lib/mocks/data-store";
import { ChatSDKError } from "@/lib/errors";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const chatId = searchParams.get("chatId");

    if (!chatId) {
      return new ChatSDKError("bad_request:vote").toResponse();
    }

    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError("unauthorized:vote").toResponse();
    }

    const votes = await mockDataStore.getVotesByChatId(chatId);

    return Response.json(votes);
  } catch (error) {
    console.error("Error fetching votes:", error);
    return new ChatSDKError("bad_request:vote").toResponse();
  }
}

export async function PATCH(request: Request) {
  try {
    const { chatId, messageId, isUpvoted } = await request.json();

    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError("unauthorized:vote").toResponse();
    }

    await mockDataStore.voteMessage({ chatId, messageId, isUpvoted });

    return Response.json({ success: true });
  } catch (error) {
    console.error("Error updating vote:", error);
    return new ChatSDKError("bad_request:vote").toResponse();
  }
}
