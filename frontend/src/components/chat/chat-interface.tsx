"use client";

import { useState } from "react";
import { MessageList, type Message } from "@/components/chat/message-list";
import { MessageInput } from "@/components/chat/message-input";

interface ChatInterfaceProps {
  conversationId: string;
  messages: Message[];
  onSendMessage: (content: string) => Promise<void>;
}

export function ChatInterface({
  messages,
  onSendMessage,
}: ChatInterfaceProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (content: string) => {
    setIsLoading(true);

    try {
      await onSendMessage(content);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <MessageList messages={messages} isLoading={isLoading} />
      
      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={isLoading}
        placeholder="Tell me about your fitness goals, dietary preferences, or ask questions..."
      />
    </div>
  );
}
