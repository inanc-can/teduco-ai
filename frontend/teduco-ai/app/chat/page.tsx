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
