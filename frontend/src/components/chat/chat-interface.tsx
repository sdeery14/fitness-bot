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
  const [inputValue, setInputValue] = useState("");

  const handleSendMessage = async (content: string) => {
    setIsLoading(true);

    try {
      await onSendMessage(content);
      setInputValue(""); // Clear input after successful send
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFillInput = (prompt: string) => {
    setInputValue(prompt);
    // Note: We don't send automatically - user can review and edit first
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <MessageList 
        messages={messages} 
        isLoading={isLoading}
        onFillInput={handleFillInput}
      />
      
      <MessageInput
        onSendMessage={handleSendMessage}
        isSending={isLoading}
        placeholder="Tell me about your fitness goals, dietary preferences, or ask questions..."
        value={inputValue}
        onValueChange={setInputValue}
      />
    </div>
  );
}
