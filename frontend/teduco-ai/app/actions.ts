"use server";

import { cookies } from "next/headers";
import type { VisibilityType } from "@/lib/types";
import { mockDataStore } from "@/lib/mocks/data-store";

export async function saveChatModelAsCookie(model: string) {
  const cookieStore = await cookies();
  cookieStore.set("chat-model", model);
}

export async function generateTitleFromUserMessage() {
  // Mock title generation
  return `Chat ${new Date().toLocaleString()}`;
}

export async function deleteTrailingMessages({ id }: { id: string }) {
  const message = await mockDataStore.getMessageById(id);
  if (message) {
    await mockDataStore.deleteMessagesByChatIdAfterTimestamp({
      chatId: message.chatId,
      timestamp: message.createdAt,
    });
  }
}

export async function updateChatVisibility({
  chatId,
  visibility,
}: {
  chatId: string;
  visibility: VisibilityType;
}) {
  await mockDataStore.updateChatVisibility(chatId, visibility);
}
