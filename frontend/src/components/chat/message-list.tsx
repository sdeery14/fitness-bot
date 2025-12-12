"use client";

import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { SuggestionCards } from "@/components/chat/suggestion-cards";
import { PlanMessageCard } from "@/components/chat/plan-message-card";

export interface Message {
  id: string;
  sender_type: "user" | "ai" | "plan";
  message_content: string;
  created_at: string;
  plan_id?: string;
}

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  onSelectSuggestion?: (prompt: string) => void;
  onFillInput?: (prompt: string) => void;
}

export function MessageList({ messages, isLoading, onSelectSuggestion, onFillInput }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Show suggestions if no messages OR only AI greeting (no user messages yet)
  const hasUserMessages = messages.some(msg => msg.sender_type === "user");
  const shouldShowSuggestions = !hasUserMessages && !isLoading && (onSelectSuggestion || onFillInput);

  return (
    <ScrollArea className="flex-1">
      <div className="">
        {shouldShowSuggestions && (
          <SuggestionCards 
            onSelectSuggestion={onSelectSuggestion || (() => {})} 
            onFillInput={onFillInput}
          />
        )}

        {messages.map((message) => {
          // Render plan message card
          if (message.sender_type === "plan" && message.plan_id) {
            return (
              <div key={message.id} className="py-4 px-4">
                <div className="max-w-3xl mx-auto">
                  <PlanMessageCard planId={message.plan_id} />
                </div>
              </div>
            );
          }

          // Render normal message
          return (
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
          );
        })}

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
