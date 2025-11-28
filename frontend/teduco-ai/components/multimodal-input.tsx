"use client";

import type { Attachment, ChatMessage } from "@/lib/types";
import type { AppUsage } from "@/lib/usage";
import type { VisibilityType } from "./visibility-selector";
import { generateUUID } from "@/lib/utils";
import { Button } from "./ui/button";

export type MultimodalInputProps = {
  attachments: Attachment[];
  chatId: string;
  input: string;
  messages: ChatMessage[];
  onModelChange: (modelId: string) => void;
  selectedModelId: string;
  selectedVisibilityType: VisibilityType;
  sendMessage: (message: ChatMessage) => void;
  setAttachments: React.Dispatch<React.SetStateAction<Attachment[]>>;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  status: "ready" | "streaming" | "submitted";
  stop: () => void;
  usage?: AppUsage;
};

export function MultimodalInput({
  attachments: _attachments,
  chatId: _chatId,
  input,
  messages: _messages,
  onModelChange: _onModelChange,
  selectedModelId: _selectedModelId,
  selectedVisibilityType: _selectedVisibilityType,
  sendMessage,
  setAttachments: _setAttachments,
  setInput,
  setMessages: _setMessages,
  status,
  stop,
  usage: _usage,
}: MultimodalInputProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || status !== "ready") return;

    const message: ChatMessage = {
      id: generateUUID(),
      role: "user",
      parts: [{ type: "text", text: input.trim() }],
    };

    sendMessage(message);
    setInput("");
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        disabled={status !== "ready"}
        className="flex-1 rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
      />
      {status === "streaming" ? (
        <Button type="button" onClick={stop} variant="outline">
          Stop
        </Button>
      ) : (
        <Button type="submit" disabled={!input.trim() || status !== "ready"}>
          Send
        </Button>
      )}
    </form>
  );
}
