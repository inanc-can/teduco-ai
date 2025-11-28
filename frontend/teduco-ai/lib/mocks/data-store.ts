import type {
  Chat,
  DBMessage,
  Document,
  Vote,
  VisibilityType,
} from "../types";

// In-memory data stores
class MockDataStore {
  private chats = new Map<string, Chat>();
  private messages = new Map<string, DBMessage[]>();
  private documents = new Map<string, Document[]>();
  private votes = new Map<string, Vote>();

  // Helper to simulate network delay
  private delay(ms: number = 100) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // Chat operations
  async saveChat(params: {
    id: string;
    userId: string;
    title: string;
    visibility: VisibilityType;
  }) {
    await this.delay();
    const chat: Chat = {
      id: params.id,
      title: params.title,
      userId: params.userId,
      visibility: params.visibility,
      createdAt: new Date(),
    };
    this.chats.set(params.id, chat);
    return chat;
  }

  async getChatById(id: string): Promise<Chat | null> {
    await this.delay();
    return this.chats.get(id) || null;
  }

  async getChatsByUserId(params: {
    userId: string;
    limit: number;
    endingBefore?: string;
  }): Promise<Chat[]> {
    await this.delay();
    const allChats = Array.from(this.chats.values())
      .filter((chat) => chat.userId === params.userId)
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());

    if (params.endingBefore) {
      const endingBeforeIndex = allChats.findIndex(
        (chat) => chat.id === params.endingBefore
      );
      if (endingBeforeIndex > -1) {
        return allChats
          .slice(endingBeforeIndex + 1, endingBeforeIndex + 1 + params.limit);
      }
    }

    return allChats.slice(0, params.limit);
  }

  async deleteChatById(id: string) {
    await this.delay();
    this.chats.delete(id);
    this.messages.delete(id);
  }

  async deleteAllChatsByUserId(userId: string) {
    await this.delay();
    const userChats = Array.from(this.chats.values()).filter(
      (chat) => chat.userId === userId
    );
    userChats.forEach((chat) => {
      this.chats.delete(chat.id);
      this.messages.delete(chat.id);
    });
  }

  async updateChatVisibility(chatId: string, visibility: VisibilityType) {
    await this.delay();
    const chat = this.chats.get(chatId);
    if (chat) {
      chat.visibility = visibility;
      this.chats.set(chatId, chat);
    }
  }

  // Message operations
  async saveMessages(chatId: string, messages: DBMessage[]) {
    await this.delay();
    const existingMessages = this.messages.get(chatId) || [];
    this.messages.set(chatId, [...existingMessages, ...messages]);
  }

  async getMessagesByChatId(chatId: string): Promise<DBMessage[]> {
    await this.delay();
    return this.messages.get(chatId) || [];
  }

  async getMessageById(id: string): Promise<DBMessage | null> {
    await this.delay();
    for (const messages of this.messages.values()) {
      const message = messages.find((m) => m.id === id);
      if (message) return message;
    }
    return null;
  }

  async deleteMessagesByChatIdAfterTimestamp(params: {
    chatId: string;
    timestamp: Date;
  }) {
    await this.delay();
    const messages = this.messages.get(params.chatId) || [];
    const filtered = messages.filter(
      (m) => m.createdAt.getTime() <= params.timestamp.getTime()
    );
    this.messages.set(params.chatId, filtered);
  }

  // Document operations
  async saveDocument(document: Document) {
    await this.delay();
    const existingDocs = this.documents.get(document.id) || [];
    this.documents.set(document.id, [...existingDocs, document]);
    return document;
  }

  async getDocumentById(id: string): Promise<Document | null> {
    await this.delay();
    const docs = this.documents.get(id);
    return docs ? docs[docs.length - 1] : null;
  }

  async getDocumentsById(id: string): Promise<Document[]> {
    await this.delay();
    return this.documents.get(id) || [];
  }

  // Vote operations
  async getVotesByChatId(chatId: string): Promise<Vote[]> {
    await this.delay();
    return Array.from(this.votes.values()).filter((v) => v.chatId === chatId);
  }

  async voteMessage(params: {
    chatId: string;
    messageId: string;
    isUpvoted: boolean;
  }) {
    await this.delay();
    const key = `${params.chatId}-${params.messageId}`;
    this.votes.set(key, {
      chatId: params.chatId,
      messageId: params.messageId,
      isUpvoted: params.isUpvoted,
    });
  }
}

// Singleton instance
export const mockDataStore = new MockDataStore();
