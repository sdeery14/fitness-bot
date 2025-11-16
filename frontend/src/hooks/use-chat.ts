import { useState, useCallback } from "react";
import { useSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Message {
  id: string;
  sender_type: "user" | "ai";
  message_content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  conversation_type: string;
  status: string;
  created_at: string;
}

export function useChat(conversationId?: string) {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startConversation = useCallback(
    async (type: string = "plan_creation"): Promise<string> => {
      try {
        setIsLoading(true);
        setError(null);

        const res = await fetch(`${API_URL}/ai/conversations`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${(session as any)?.accessToken}`,
          },
          body: JSON.stringify({
            conversation_type: type,
          }),
        });

        const data = await res.json();

        if (!res.ok || data.status !== "success") {
          throw new Error(data.error?.message || "Failed to start conversation");
        }

        return data.data.conversation_id;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to start conversation";
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [session]
  );

  const sendMessage = useCallback(
    async (content: string, convId: string = conversationId || ""): Promise<void> => {
      if (!convId) {
        throw new Error("No conversation ID provided");
      }

      try {
        setIsLoading(true);
        setError(null);

        const res = await fetch(`${API_URL}/ai/conversations/${convId}/messages`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${(session as any)?.accessToken}`,
          },
          body: JSON.stringify({
            message_content: content,
          }),
        });

        const data = await res.json();

        if (!res.ok || data.status !== "success") {
          throw new Error(data.error?.message || "Failed to send message");
        }

        // Update messages with response
        setMessages((prev) => [
          ...prev,
          data.data.user_message,
          data.data.ai_message,
        ]);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to send message";
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, session]
  );

  const getConversation = useCallback(
    async (convId: string): Promise<Conversation> => {
      try {
        setIsLoading(true);
        setError(null);

        const res = await fetch(`${API_URL}/ai/conversations/${convId}`, {
          headers: {
            Authorization: `Bearer ${(session as any)?.accessToken}`,
          },
        });

        const data = await res.json();

        if (!res.ok || data.status !== "success") {
          throw new Error(data.error?.message || "Failed to fetch conversation");
        }

        // Update messages from conversation history
        if (data.data.messages) {
          setMessages(data.data.messages);
        }

        return data.data.conversation;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to fetch conversation";
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [session]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    startConversation,
    sendMessage,
    getConversation,
    clearMessages,
    clearError,
  };
}
