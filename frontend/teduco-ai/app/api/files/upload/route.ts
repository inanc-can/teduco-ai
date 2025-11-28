import { auth } from "@/lib/mocks/auth";
import { ChatSDKError } from "@/lib/errors";

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError("unauthorized:api").toResponse();
    }

    const formData = await request.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return new ChatSDKError("bad_request:api").toResponse();
    }

    // Convert file to data URL for mock purposes
    const buffer = await file.arrayBuffer();
    const base64 = Buffer.from(buffer).toString("base64");
    const dataUrl = `data:${file.type};base64,${base64}`;

    return Response.json({
      url: dataUrl,
      name: file.name,
      contentType: file.type,
    });
  } catch (error) {
    console.error("Error uploading file:", error);
    return new ChatSDKError("bad_request:api").toResponse();
  }
}
