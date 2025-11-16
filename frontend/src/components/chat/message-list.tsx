"use client";

import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export interface Message {
  id: string;
  sender_type: "user" | "ai";
  message_content: string;
  created_at: string;
}

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <ScrollArea className="flex-1">
      <div className="">
        {messages.length === 0 && !isLoading && (
          <div className="flex items-center justify-center min-h-[60vh] text-center px-4">
            <div className="max-w-2xl">
              <div className="mb-6 text-6xl">💪</div>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Start Your Fitness Journey</h2>
              <p className="text-lg text-gray-600 mb-8">
                Tell me about your fitness goals and I'll help create a personalized plan just for you.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-left">
                <div className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer">
                  <p className="text-sm font-medium text-gray-700">🎯 "I want to lose 20 pounds in 3 months"</p>
                </div>
                <div className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer">
                  <p className="text-sm font-medium text-gray-700">💪 "Build muscle and gain strength"</p>
                </div>
                <div className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer">
                  <p className="text-sm font-medium text-gray-700">🏃 "Train for my first marathon"</p>
                </div>
                <div className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer">
                  <p className="text-sm font-medium text-gray-700">🧘 "Improve flexibility and balance"</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "py-8 px-4",
              message.sender_type === "ai" ? "bg-gray-50" : "bg-white"
            )}
          >
            <div className="max-w-3xl mx-auto flex gap-6 items-start">
              <Avatar className="h-8 w-8 flex-shrink-0 mt-1">
                <AvatarFallback 
                  className={cn(
                    "font-bold text-sm",
                    message.sender_type === "ai" 
                      ? "bg-green-600 text-white" 
                      : "bg-purple-600 text-white"
                  )}
                >
                  {message.sender_type === "ai" ? "AI" : "U"}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-gray-900">
                  {message.sender_type === "ai" ? "AI Fitness Coach" : "You"}
                </p>
                <div className="prose prose-sm max-w-none">
                  <p className="text-[15px] leading-relaxed text-gray-800 whitespace-pre-wrap">{message.message_content}</p>
                </div>
                <p className="text-xs text-gray-400 pt-1">
                  {new Date(message.created_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="py-8 px-4 bg-gray-50">
            <div className="max-w-3xl mx-auto flex gap-6 items-start">
              <Avatar className="h-8 w-8 flex-shrink-0 mt-1">
                <AvatarFallback className="font-bold text-sm bg-green-600 text-white">
                  AI
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900 mb-2">AI Fitness Coach</p>
                <div className="flex space-x-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]"></div>
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]"></div>
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>
    </ScrollArea>
  );
}
