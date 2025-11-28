import { generateUUID } from "../utils";

export type StreamPart =
  | { type: "text-delta"; textDelta: string }
  | { type: "data"; data: Record<string, unknown> }
  | { type: "finish"; usage?: { promptTokens: number; completionTokens: number } };

export async function* createMockTextStream(prompt: string): AsyncGenerator<string> {
  // Simple pattern matching for different responses
  const lowerPrompt = prompt.toLowerCase();
  
  let response: string;
  
  if (lowerPrompt.includes("code") || lowerPrompt.includes("function") || lowerPrompt.includes("python")) {
    response = "Here's a simple Python function:\n\n```python\ndef greet(name):\n    return f'Hello, {name}!'\n\nprint(greet('World'))\n```\n\nThis function takes a name as input and returns a greeting message.";
  } else if (lowerPrompt.includes("weather")) {
    response = "I can help you check the weather! However, I currently don't have access to live weather data. In a production environment, I would connect to a weather API to fetch real-time information.";
  } else if (lowerPrompt.includes("hello") || lowerPrompt.includes("hi")) {
    response = "Hello! I'm here to help you. How can I assist you today?";
  } else {
    response = `You asked: "${prompt}"\n\nThis is a mock response demonstrating the chat interface. In a production environment, this would be connected to a real AI model that can understand and respond to your questions intelligently.\n\nThe system supports:\n- Streaming responses (like you're seeing now)\n- Code artifacts\n- Document creation\n- Rich text formatting\n- And much more!`;
  }

  // Stream character by character with a delay
  for (const char of response) {
    yield char;
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
}

export function createMockStreamResponse(parts: StreamPart[]): ReadableStream {
  const encoder = new TextEncoder();
  
  return new ReadableStream({
    async start(controller) {
      for (const part of parts) {
        const line = `data: ${JSON.stringify(part)}\n\n`;
        controller.enqueue(encoder.encode(line));
        
        // Small delay between parts
        await new Promise((resolve) => setTimeout(resolve, 10));
      }
      
      controller.close();
    },
  });
}

export async function createChatStreamResponse(
  prompt: string
): Promise<Response> {
  const encoder = new TextEncoder();
  
  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Send message start
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ type: "message-start", id: generateUUID(), role: "assistant" })}\n\n`
          )
        );

        // Stream text deltas
        for await (const char of createMockTextStream(prompt)) {
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({ type: "text-delta", textDelta: char })}\n\n`
            )
          );
        }

        // Send finish
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              type: "finish",
              usage: { promptTokens: 50, completionTokens: 100 },
            })}\n\n`
          )
        );

        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
