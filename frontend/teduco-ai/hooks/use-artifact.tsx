"use client";

import {
  type Dispatch,
  type SetStateAction,
  createContext,
  useContext,
  useState,
} from "react";
import type { ArtifactKind } from "@/lib/types";

export type ArtifactStatus = "idle" | "streaming";

export type ArtifactData = {
  documentId: string;
  title: string;
  kind: ArtifactKind;
  content: string;
  status: ArtifactStatus;
  isVisible: boolean;
};

export type ArtifactMetadata = {
  [key: string]: unknown;
};

export const initialArtifactData: ArtifactData = {
  documentId: "",
  title: "",
  kind: "text",
  content: "",
  status: "idle",
  isVisible: false,
};

type ArtifactContextType = {
  artifact: ArtifactData;
  setArtifact: Dispatch<SetStateAction<ArtifactData>>;
  metadata: ArtifactMetadata;
  setMetadata: Dispatch<SetStateAction<ArtifactMetadata>>;
};

const ArtifactContext = createContext<ArtifactContextType | null>(null);

export function useArtifact() {
  const context = useContext(ArtifactContext);
  if (!context) {
    throw new Error("useArtifact must be used within an ArtifactProvider");
  }
  return context;
}

export function useArtifactSelector<T>(
  selector: (state: ArtifactData) => T
): T {
  const context = useContext(ArtifactContext);
  if (!context) {
    // Return a default value when context is not available
    return selector(initialArtifactData);
  }
  return selector(context.artifact);
}

export function ArtifactProvider({ children }: { children: React.ReactNode }) {
  const [artifact, setArtifact] = useState<ArtifactData>(initialArtifactData);
  const [metadata, setMetadata] = useState<ArtifactMetadata>({});

  return (
    <ArtifactContext.Provider
      value={{ artifact, setArtifact, metadata, setMetadata }}
    >
      {children}
    </ArtifactContext.Provider>
  );
}
