import { cookies } from "next/headers";
import { auth } from "@/lib/mocks/auth";
import { DEFAULT_CHAT_MODEL } from "@/lib/constants";
import { generateUUID } from "@/lib/utils";
import { Chat } from "@/components/chat";
import { DataStreamHandler } from "@/components/data-stream-handler";

export default async function Page() {
  const session = await auth();

  // Mock auth - always have a session in demo mode
  if (!session) {
    return <div>No session</div>;
  }

  const id = generateUUID();

  const cookieStore = await cookies();
  const modelIdFromCookie = cookieStore.get("chat-model");

  // For now, return a placeholder until Chat component is implemented
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="text-center">
        <h1 className="mb-4 text-2xl font-bold">Chat Interface</h1>
        <p className="text-muted-foreground">
          Chat ID: {id}
          <br />
          Model: {modelIdFromCookie?.value || DEFAULT_CHAT_MODEL}
          <br />
          User: {session.user.email}
        </p>
        <p className="mt-4 text-sm text-muted-foreground">
          Chat component will be implemented next
        </p>
      </div>
    </div>
  );

  // TODO: Uncomment when Chat and DataStreamHandler components are ready
  if (!modelIdFromCookie) {
    return (
      <>
        <Chat
          autoResume={false}
          id={id}
          initialChatModel={DEFAULT_CHAT_MODEL}
          initialMessages={[]}
          initialVisibilityType="private"
          isReadonly={false}
          key={id}
        />
        <DataStreamHandler />
      </>
    );
  }

  return (
    <>
      <Chat
        autoResume={false}
        id={id}
        initialChatModel={modelIdFromCookie.value}
        initialMessages={[]}
        initialVisibilityType="private"
        isReadonly={false}
        key={id}
      />
      <DataStreamHandler />
    </>
  );
}
