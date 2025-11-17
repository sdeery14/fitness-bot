"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { ChatInterface } from "@/components/chat/chat-interface";
import { type Message } from "@/components/chat/message-list";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowLeft, Plus } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Conversation types with descriptions
const CONVERSATION_TYPES = [
  {
    value: "general_question",
    label: "General Question",
    description: "Ask general fitness and nutrition questions",
  },
  {
    value: "plan_creation",
    label: "Create Plan",
    description: "Create a new fitness or meal plan",
  },
  {
    value: "plan_update",
    label: "Update Progress",
    description: "Log workouts, meals, and track progress",
  },
  {
    value: "plan_modification",
    label: "Modify Plan",
    description: "Adjust exercises, meals, or plan settings",
  },
  {
    value: "disruption_handling",
    label: "Handle Disruption",
    description: "Report schedule changes or disruptions",
  },
] as const;

type ConversationType = typeof CONVERSATION_TYPES[number]["value"];

export default function ChatPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversationType, setConversationType] = useState<ConversationType>("general_question");
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
          conversation_type: conversationType,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to start conversation");
      }

      // Backend response format: { status, data: { conversation_id, ... }, metadata }
      const responseData = data.data || data; // Support both new and old formats
      
      setConversationId(responseData.conversation_id);
      
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
    
    // Reset flag after conversation created
    isCreatingNewChat.current = false;
  };

  const handleConversationTypeChange = async (newType: ConversationType) => {
    setConversationType(newType);
    
    // Start a new conversation with the new type
    isCreatingNewChat.current = true;
    setMessages([]);
    setError(null);
    setConversationId(null);
    await startConversation(true);
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

      // Backend response format: { status, data: { assistant_response, ... }, metadata }
      const responseData = data.data || data; // Support both new and old formats
      
      console.log("Response data keys:", Object.keys(responseData));
      console.log("Response data:", responseData);
      
      // Extract AI response - check multiple possible keys
      const aiResponse = responseData.assistant_response || responseData.agent_response || responseData.assistant_message?.content;

      // Replace optimistic user message with confirmed one and add AI response
      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== tempMessageId);
        
        return [
          ...withoutTemp,
          { 
            id: responseData.message_id || Date.now().toString(), 
            sender_type: "user", 
            message_content: content,
            created_at: new Date().toISOString(),
          },
          { 
            id: (Date.now() + 1).toString(), 
            sender_type: "ai", 
            message_content: aiResponse || "I'm processing your request...",
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

          <div className="flex items-center gap-3">
            {/* Conversation Type Selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Mode:</span>
              <Select value={conversationType} onValueChange={handleConversationTypeChange}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONVERSATION_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex flex-col">
                        <span className="font-medium">{type.label}</span>
                        <span className="text-xs text-gray-500">{type.description}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
