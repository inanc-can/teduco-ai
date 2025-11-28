"use client";

import type { ArtifactKind, Attachment, ChatMessage, Vote } from "@/lib/types";
import type { VisibilityType } from "./visibility-selector";
import type { ArtifactData, ArtifactMetadata } from "@/hooks/use-artifact";

export type ArtifactDefinition = {
  kind: ArtifactKind;
  onStreamPart?: (params: {
    streamPart: { type: string; data: unknown };
    setArtifact: React.Dispatch<React.SetStateAction<ArtifactData>>;
    setMetadata: React.Dispatch<React.SetStateAction<ArtifactMetadata>>;
  }) => void;
};

export const artifactDefinitions: ArtifactDefinition[] = [
  { kind: "text" },
  { kind: "code" },
  { kind: "image" },
  { kind: "sheet" },
];

export type ArtifactProps = {
  attachments: Attachment[];
  chatId: string;
  input: string;
  isReadonly: boolean;
  messages: ChatMessage[];
  regenerate: (messageId: string) => void;
  selectedModelId: string;
  selectedVisibilityType: VisibilityType;
  sendMessage: (message: ChatMessage) => void;
  setAttachments: React.Dispatch<React.SetStateAction<Attachment[]>>;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  status: "ready" | "streaming" | "submitted";
  stop: () => void;
  votes?: Vote[];
};

export function Artifact(_props: ArtifactProps) {
  // Artifact viewer - placeholder implementation
  // Will be expanded to show generated artifacts (documents, code, etc.)
  return null;
}
