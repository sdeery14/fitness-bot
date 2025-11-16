"use client";

import { useEffect, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface StreamingResponseProps {
  conversationId: string;
  onComplete?: (fullResponse: string) => void;
}

export function StreamingResponse({ conversationId, onComplete }: StreamingResponseProps) {
  const [streamedContent, setStreamedContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(true);

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const eventSource = new EventSource(
      `${API_URL}/ai/conversations/${conversationId}/stream`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === "chunk") {
          setStreamedContent((prev) => prev + data.content);
        } else if (data.type === "done") {
          setIsStreaming(false);
          onComplete?.(streamedContent);
          eventSource.close();
        }
      } catch (error) {
        console.error("Error parsing SSE data:", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE error:", error);
      setIsStreaming(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [conversationId, streamedContent, onComplete]);

  if (!streamedContent && isStreaming) {
    return (
      <div className="flex gap-3 justify-start">
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground">
            AI
          </AvatarFallback>
        </Avatar>
        <div className="rounded-lg px-4 py-3 bg-gray-100">
          <div className="flex space-x-2">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 justify-start">
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback className="bg-primary text-primary-foreground">
          AI
        </AvatarFallback>
      </Avatar>
      <div className="rounded-lg px-4 py-3 bg-gray-100 text-gray-900 max-w-[80%]">
        <p className="text-sm whitespace-pre-wrap">
          {streamedContent}
          {isStreaming && <span className="inline-block w-1 h-4 ml-1 bg-gray-900 animate-pulse" />}
        </p>
      </div>
    </div>
  );
}
