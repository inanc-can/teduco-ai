import { auth } from "@/lib/mocks/auth";
import { mockDataStore } from "@/lib/mocks/data-store";
import { createChatStreamResponse } from "@/lib/mocks/stream-helpers";
import { getTextFromMessage } from "@/lib/utils";
import type { ChatMessage, VisibilityType } from "@/lib/types";
import { ChatSDKError } from "@/lib/errors";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      id,
      message,
      selectedVisibilityType,
    }: {
      id: string;
      message: ChatMessage;
      selectedChatModel?: string;
      selectedVisibilityType: VisibilityType;
    } = body;

    const session = await auth();

    if (!session?.user) {
      return new ChatSDKError("unauthorized:chat").toResponse();
    }

    // Check if chat exists, if not create it
    const chat = await mockDataStore.getChatById(id);
    if (!chat) {
      const title = `Chat ${new Date().toLocaleString()}`;
      await mockDataStore.saveChat({
        id,
        userId: session.user.id,
        title,
        visibility: selectedVisibilityType,
      });
    }

    // Save the user message
    await mockDataStore.saveMessages(id, [
      {
        id: message.id,
        chatId: id,
        role: message.role,
        parts: message.parts,
        createdAt: new Date(),
      },
    ]);

    // Get the text from the message
    const prompt = getTextFromMessage(message);

    // Return streaming response
    return createChatStreamResponse(prompt);
  } catch (error) {
    console.error("Error in chat route:", error);
    return new ChatSDKError("bad_request:chat").toResponse();
  }
}

export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      return new ChatSDKError("bad_request:chat").toResponse();
    }

    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError("unauthorized:chat").toResponse();
    }

    const chat = await mockDataStore.getChatById(id);
    if (!chat) {
      return new ChatSDKError("not_found:chat").toResponse();
    }

    if (chat.userId !== session.user.id) {
      return new ChatSDKError("forbidden:chat").toResponse();
    }

    await mockDataStore.deleteChatById(id);

    return new Response(null, { status: 204 });
  } catch (error) {
    console.error("Error deleting chat:", error);
    return new ChatSDKError("bad_request:chat").toResponse();
  }
}
