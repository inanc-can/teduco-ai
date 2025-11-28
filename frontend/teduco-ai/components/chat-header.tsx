"use client";

import type { VisibilityType } from "./visibility-selector";

export type ChatHeaderProps = {
  chatId: string;
  isReadonly: boolean;
  selectedVisibilityType: VisibilityType;
};

export function ChatHeader({
  chatId: _chatId,
  isReadonly,
  selectedVisibilityType,
}: ChatHeaderProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b px-4">
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold">Chat</h1>
        {isReadonly && (
          <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
            Read Only
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">
          {selectedVisibilityType === "private" ? "Private" : "Public"}
        </span>
      </div>
    </header>
  );
}
