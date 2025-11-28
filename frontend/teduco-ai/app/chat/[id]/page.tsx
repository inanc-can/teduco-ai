import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { auth } from "@/lib/mocks/auth";
import { mockDataStore } from "@/lib/mocks/data-store";
import { DEFAULT_CHAT_MODEL } from "@/lib/constants";
import { convertToUIMessages } from "@/lib/utils";

export default async function Page(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const { id } = params;
  
  const chat = await mockDataStore.getChatById(id);

  if (!chat) {
    notFound();
  }

  const session = await auth();

  // Mock auth - always have a session in demo mode
  if (!session) {
    return <div>No session</div>;
  }

  // Check privacy
  if (chat.visibility === "private") {
    if (!session.user) {
      return notFound();
    }

    if (session.user.id !== chat.userId) {
      return notFound();
    }
  }

  const messagesFromDb = await mockDataStore.getMessagesByChatId(id);
  const uiMessages = convertToUIMessages(messagesFromDb);

  const cookieStore = await cookies();
  const chatModelFromCookie = cookieStore.get("chat-model");

  // For now, return a placeholder until Chat component is implemented
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="text-center">
        <h1 className="mb-4 text-2xl font-bold">{chat.title}</h1>
        <p className="text-muted-foreground">
          Chat ID: {chat.id}
          <br />
          Model: {chatModelFromCookie?.value || DEFAULT_CHAT_MODEL}
          <br />
          Messages: {uiMessages.length}
          <br />
          Visibility: {chat.visibility}
        </p>
        <p className="mt-4 text-sm text-muted-foreground">
          Chat component will be implemented next
        </p>
      </div>
    </div>
  );

  // TODO: Uncomment when Chat and DataStreamHandler components are ready
  // if (!chatModelFromCookie) {
  //   return (
  //     <>
  //       <Chat
  //         autoResume={true}
  //         id={chat.id}
  //         initialChatModel={DEFAULT_CHAT_MODEL}
  //         initialMessages={uiMessages}
  //         initialVisibilityType={chat.visibility}
  //         isReadonly={session?.user?.id !== chat.userId}
  //       />
  //       <DataStreamHandler />
  //     </>
  //   );
  // }

  // return (
  //   <>
  //     <Chat
  //       autoResume={true}
  //       id={chat.id}
  //       initialChatModel={chatModelFromCookie.value}
  //       initialMessages={uiMessages}
  //       initialVisibilityType={chat.visibility}
  //       isReadonly={session?.user?.id !== chat.userId}
  //     />
  //     <DataStreamHandler />
  //   </>
  // );
}
