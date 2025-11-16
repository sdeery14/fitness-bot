"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { ChatInterface } from "@/components/chat/chat-interface";
import { type Message } from "@/components/chat/message-list";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Plus } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function ChatPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isCreatingNewChat = useRef(false);

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    } else {
      setAccessToken(token);
    }
  }, [router]);

  // Start a new conversation when component mounts
  useEffect(() => {
    if (accessToken && !conversationId && !isCreatingNewChat.current) {
      startConversation(false);
    }
  }, [accessToken, conversationId]);

  const startConversation = async (forceNew: boolean = false) => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await fetch(`${API_URL}/ai/conversations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          force_new: forceNew,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to start conversation");
      }

      setConversationId(data.conversation_id);
      
      // Load message history (backend returns both user message and AI response)
      if (data.message_history && data.message_history.length > 0) {
        // Map backend's "assistant" sender_type to frontend's "ai"
        const mappedMessages = data.message_history.map((msg: any) => ({
          ...msg,
          sender_type: msg.sender_type === "assistant" ? "ai" : msg.sender_type,
        }));
        setMessages(mappedMessages);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start conversation");
      console.error("Error starting conversation:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    // Set flag to prevent useEffect from interfering
    isCreatingNewChat.current = true;
    
    // Clear current state immediately for better UX
    setMessages([]);
    setError(null);
    setConversationId(null);
    
    // Start a new conversation (forceNew=true to prevent loading history)
    await startConversation(true);
    
    // Reset flag after conversation created
    isCreatingNewChat.current = false;
  };

  const handleSendMessage = async (content: string) => {
    if (!conversationId) {
      setError("No active conversation");
      return;
    }

    // Optimistically add user message to chat immediately
    const tempMessageId = `temp-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: tempMessageId,
        sender_type: "user",
        message_content: content,
        created_at: new Date().toISOString(),
      },
    ]);

    try {
      const res = await fetch(`${API_URL}/ai/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          message: content,
        }),
      });

      const data = await res.json();

      console.log("Response from backend:", data);

      if (!res.ok) {
        throw new Error(data.detail || "Failed to send message");
      }

      // Replace optimistic message with real messages from backend
      setMessages((prev) => {
        console.log("Current messages:", prev);
        console.log("Replacing optimistic message");
        console.log("Adding AI response:", data.agent_response);
        
        return [
          ...prev.filter((m) => m.id !== tempMessageId), // Remove optimistic message
          { 
            id: Date.now().toString(), 
            sender_type: "user", 
            message_content: content,
            created_at: new Date().toISOString(),
          },
          { 
            id: (Date.now() + 1).toString(), 
            sender_type: "ai", 
            message_content: data.agent_response,
            created_at: new Date().toISOString(),
          },
        ];
      });
    } catch (err) {
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempMessageId));
      setError(err instanceof Error ? err.message : "Failed to send message");
      console.error("Error sending message:", err);
      throw err; // Re-throw to handle in ChatInterface
    }
  };

  if (!accessToken || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={() => router.push("/dashboard")}>
            Go to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/dashboard")}
              className="text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Dashboard
            </Button>
            <div className="h-6 w-px bg-gray-300"></div>
            <h1 className="text-lg font-semibold text-gray-900">AI Fitness Coach</h1>
          </div>
          
          {conversationId && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleNewChat}
              className="gap-2 border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
          )}
        </div>
      </div>

      {/* Chat Area */}
      {conversationId && (
        <ChatInterface
          conversationId={conversationId}
          messages={messages}
          onSendMessage={handleSendMessage}
        />
      )}
    </div>
  );
}
