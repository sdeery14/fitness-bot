"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { ChatInterface } from "@/components/chat/chat-interface";
import { type Message } from "@/components/chat/message-list";
import { Button } from "@/components/ui/button";
import { Plus, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Conversation {
  id: string;
  title?: string;
  status: string;
  conversation_type: string;
  created_at: string;
  updated_at: string;
}

export default function ChatPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
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

  // Load user's conversations
  useEffect(() => {
    if (accessToken) {
      loadConversations();
    }
  }, [accessToken]);

  // Start a new conversation when component mounts
  useEffect(() => {
    if (accessToken && !conversationId && !isCreatingNewChat.current) {
      startConversation(false);
    }
  }, [accessToken, conversationId]);

  const loadConversations = async () => {
    try {
      const res = await fetch(`${API_URL}/ai/conversations`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      const data = await res.json();
      if (res.ok) {
        const responseData = data.data || data;
        setConversations(responseData.conversations || []);
      }
    } catch (err) {
      console.error("Error loading conversations:", err);
    }
  };

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

      // Backend response format: { status, data: { conversation_id, ... }, metadata }
      const responseData = data.data || data; // Support both new and old formats
      
      // conversation_id will be null for initial greeting (not yet stored in DB)
      setConversationId(responseData.conversation_id || null);
      
      // Load message history (backend returns both user message and AI response)
      if (responseData.message_history && responseData.message_history.length > 0) {
        // Map backend's "assistant" sender_type to frontend's "ai"
        const mappedMessages = responseData.message_history.map((msg: any) => ({
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
    
    // Reload conversations list
    await loadConversations();
    
    // Reset flag after conversation created
    isCreatingNewChat.current = false;
  };

  const handleSelectConversation = async (convId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      setConversationId(convId);

      // Load the conversation details
      const res = await fetch(`${API_URL}/ai/conversations/${convId}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      const data = await res.json();
      if (res.ok) {
        const responseData = data.data || data;
        // Load message history if available
        if (responseData.message_history && responseData.message_history.length > 0) {
          const mappedMessages = responseData.message_history.map((msg: any) => ({
            ...msg,
            sender_type: msg.sender_type === "assistant" ? "ai" : msg.sender_type,
          }));
          setMessages(mappedMessages);
        } else {
          setMessages([]);
        }
      }
    } catch (err) {
      console.error("Error loading conversation:", err);
      setError("Failed to load conversation");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    // Use "new" for first message when no conversation exists
    const targetConversationId = conversationId || "new";

    // Add user message to chat immediately (optimistic UI)
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender_type: "user",
      message_content: content,
      created_at: new Date().toISOString(),
    };
    
    setMessages((prev) => [...prev, userMessage]);

    try {
      const res = await fetch(`${API_URL}/ai/conversations/${targetConversationId}/messages`, {
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

      // Backend response format: { status, data: { assistant_response, ... }, metadata }
      const responseData = data.data || data; // Support both new and old formats
      
      console.log("Response data keys:", Object.keys(responseData));
      console.log("Response data:", responseData);
      
      // Set conversation ID if this was a new conversation
      const newConversationId = !conversationId && responseData.conversation_id 
        ? responseData.conversation_id 
        : conversationId;
      
      if (newConversationId !== conversationId) {
        setConversationId(newConversationId);
      }

      // Reload full conversation history to get all messages including plan messages
      if (newConversationId) {
        const historyRes = await fetch(`${API_URL}/ai/conversations/${newConversationId}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        
        const historyData = await historyRes.json();
        if (historyRes.ok) {
          const historyResponseData = historyData.data || historyData;
          if (historyResponseData.message_history && historyResponseData.message_history.length > 0) {
            const mappedMessages = historyResponseData.message_history.map((msg: any) => ({
              ...msg,
              sender_type: msg.sender_type === "assistant" ? "ai" : msg.sender_type,
            }));
            setMessages(mappedMessages);
          }
        }
      } else {
        // Fallback: Add AI response to chat if conversation reload fails
        const aiResponse = responseData.assistant_response || responseData.agent_response || responseData.assistant_message?.content;
        setMessages((prev) => [
          ...prev,
          { 
            id: (Date.now() + 1).toString(), 
            sender_type: "ai", 
            message_content: aiResponse || "I'm processing your request...",
            created_at: new Date().toISOString(),
          },
        ]);
      }

      // Reload conversations to pick up the newly generated title
      await loadConversations();
    } catch (err) {
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
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
    <div className="flex h-[calc(100vh-4rem)] bg-white">
      {/* Sidebar */}
      <div className="w-64 border-r border-gray-200 flex flex-col bg-gray-50">
        {/* New Chat Button */}
        <div className="p-4 border-b border-gray-200">
          <Button
            onClick={handleNewChat}
            className="w-full gap-2"
            disabled={isLoading}
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto p-2">
          <div className="space-y-1">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => handleSelectConversation(conv.id)}
                className={cn(
                  "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                  "hover:bg-gray-200",
                  conversationId === conv.id
                    ? "bg-gray-200 font-medium"
                    : "text-gray-700"
                )}
              >
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="truncate">
                      {conv.title || "New Conversation"}
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      {new Date(conv.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {conversationId || messages.length > 0 ? (
          <ChatInterface
            conversationId={conversationId || "new"}
            messages={messages}
            onSendMessage={handleSendMessage}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>Select a conversation or start a new chat</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
