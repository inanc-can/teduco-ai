import { auth } from "@/lib/mocks/auth";
import { mockDataStore } from "@/lib/mocks/data-store";
import { ChatSDKError } from "@/lib/errors";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = Number.parseInt(searchParams.get("limit") || "20");
    const endingBefore = searchParams.get("ending_before");

    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError("unauthorized:history").toResponse();
    }

    const chats = await mockDataStore.getChatsByUserId({
      userId: session.user.id,
      limit,
      endingBefore: endingBefore || undefined,
    });

    const hasMore = chats.length === limit;

    return Response.json({
      chats,
      hasMore,
    });
  } catch (error) {
    console.error("Error fetching chat history:", error);
    return new ChatSDKError("bad_request:history").toResponse();
  }
}

export async function DELETE() {
  try {
    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError("unauthorized:history").toResponse();
    }

    await mockDataStore.deleteAllChatsByUserId(session.user.id);

    return new Response(null, { status: 204 });
  } catch (error) {
    console.error("Error deleting all chats:", error);
    return new ChatSDKError("bad_request:history").toResponse();
  }
}
