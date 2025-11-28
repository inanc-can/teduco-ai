import { auth } from "@/lib/mocks/auth";
import { mockDataStore } from "@/lib/mocks/data-store";
import { ChatSDKError } from "@/lib/errors";
import type { ArtifactKind } from "@/lib/types";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      return new ChatSDKError("bad_request:document").toResponse();
    }

    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError("unauthorized:document").toResponse();
    }

    const documents = await mockDataStore.getDocumentsById(id);

    return Response.json(documents);
  } catch (error) {
    console.error("Error fetching documents:", error);
    return new ChatSDKError("bad_request:document").toResponse();
  }
}

export async function POST(request: Request) {
  try {
    const { id, title, content, kind } = await request.json() as {
      id: string;
      title: string;
      content: string;
      kind: ArtifactKind;
    };

    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError("unauthorized:document").toResponse();
    }

    const document = await mockDataStore.saveDocument({
      id,
      title,
      content,
      kind,
      userId: session.user.id,
      createdAt: new Date(),
    });

    return Response.json(document);
  } catch (error) {
    console.error("Error creating document:", error);
    return new ChatSDKError("bad_request:document").toResponse();
  }
}
