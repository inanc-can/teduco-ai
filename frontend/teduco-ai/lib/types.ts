import { z } from "zod";

export const messageMetadataSchema = z.object({
  createdAt: z.string(),
});

export type MessageMetadata = z.infer<typeof messageMetadataSchema>;

// User types
export type User = {
  id: string;
  email: string;
  type?: "guest" | "regular";
};

// Chat types
export type Chat = {
  id: string;
  title: string;
  userId: string;
  createdAt: Date;
  visibility: "private" | "public";
};

export type VisibilityType = "private" | "public";

// Artifact types (defined early for use in other types)
export type ArtifactKind = "text" | "code" | "image" | "sheet";

// Usage types
export type AppUsage = {
  promptTokens: number;
  completionTokens: number;
};

// Message part types
export type TextPart = {
  type: "text";
  text: string;
};

export type ToolCallPart = {
  type: "tool-call";
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
};

export type ToolResultPart = {
  type: "tool-result";
  toolCallId: string;
  toolName: string;
  result: unknown;
};

export type DataPart = {
  type: "data";
  data: Record<string, unknown>;
};

export type MessagePart = TextPart | ToolCallPart | ToolResultPart | DataPart;

// Message types
export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  parts: MessagePart[];
  metadata?: MessageMetadata;
  createdAt?: Date;
};

export type DBMessage = {
  id: string;
  chatId: string;
  role: "user" | "assistant" | "system";
  parts: MessagePart[];
  createdAt: Date;
};

// Attachment types
export type Attachment = {
  name: string;
  url: string;
  contentType: string;
};

// Vote types
export type Vote = {
  chatId: string;
  messageId: string;
  isUpvoted: boolean;
};

// Document types
export type Document = {
  id: string;
  title: string;
  content: string;
  kind: ArtifactKind;
  userId: string;
  createdAt: Date;
};
