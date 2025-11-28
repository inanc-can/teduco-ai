"use client";

import type { ChatMessage, Vote } from "@/lib/types";

export type MessagesProps = {
  chatId: string;
  isArtifactVisible: boolean;
  isReadonly: boolean;
  messages: ChatMessage[];
  regenerate: (messageId: string) => void;
  selectedModelId: string;
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  status: "ready" | "streaming" | "submitted";
  votes?: Vote[];
};

export function Messages({
  chatId: _chatId,
  isArtifactVisible: _isArtifactVisible,
  isReadonly: _isReadonly,
  messages,
  regenerate: _regenerate,
  selectedModelId: _selectedModelId,
  setMessages: _setMessages,
  status,
  votes: _votes,
}: MessagesProps) {
  return (
    <div className="flex flex-1 flex-col gap-6 overflow-y-auto p-4">
      {messages.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-muted-foreground">
            Start a conversation by typing a message below.
          </p>
        </div>
      ) : (
        messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              {message.parts.map((part, index) => {
                if (part.type === "text") {
                  return <p key={index}>{part.text}</p>;
                }
                return null;
              })}
            </div>
          </div>
        ))
      )}
      {status === "streaming" && (
        <div className="flex justify-start">
          <div className="max-w-[80%] rounded-lg bg-muted p-3">
            <p className="animate-pulse">Thinking...</p>
          </div>
        </div>
      )}
    </div>
  );
}
