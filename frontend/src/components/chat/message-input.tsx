"use client";

import { useState, KeyboardEvent, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";

interface MessageInputProps {
  onSendMessage: (content: string) => void;
  isSending?: boolean;
  placeholder?: string;
  value?: string;
  onValueChange?: (value: string) => void;
}

export function MessageInput({ 
  onSendMessage, 
  isSending = false,
  placeholder = "Type your message...",
  value: externalValue,
  onValueChange,
}: MessageInputProps) {
  const [internalInput, setInternalInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Use external value if provided, otherwise use internal state
  const input = externalValue !== undefined ? externalValue : internalInput;
  const setInput = onValueChange || setInternalInput;

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      // Set height based on scrollHeight, with a max height
      const maxHeight = 400; // Max height in pixels (about 20 lines)
      const newHeight = Math.min(textarea.scrollHeight, maxHeight);
      textarea.style.height = `${newHeight}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    
    const trimmedInput = input.trim();
    if (!trimmedInput || isSending) return;

    onSendMessage(trimmedInput);
    setInput("");
    
    // Refocus the textarea after sending message
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 0);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white py-4" role="region" aria-label="Message input">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto px-4" aria-label="Send message form">
        <div className="relative flex items-end gap-2 bg-white border-2 border-gray-300 rounded-2xl shadow-lg focus-within:border-blue-400 focus-within:shadow-xl transition-all">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="min-h-[52px] max-h-[400px] resize-none flex-1 bg-transparent border-0 px-4 py-3 text-gray-900 placeholder:text-gray-400 focus-visible:outline-none focus:outline-none focus:ring-0 focus-visible:ring-0 overflow-y-auto"
            rows={1}
            aria-label="Message input"
            aria-describedby="message-input-help"
            autoFocus
          />
          <button
            type="submit"
            disabled={isSending || !input.trim()}
            className="flex-shrink-0 m-2 h-10 w-10 inline-flex items-center justify-center text-white rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
            aria-label="Send message"
            aria-disabled={isSending || !input.trim()}
          >
            {isSending ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-solid border-current border-r-transparent" aria-hidden="true" />
            ) : (
              <Send className="h-5 w-5" aria-hidden="true" />
            )}
            <span className="sr-only">Send message</span>
          </button>
        </div>
        <p className="text-xs text-gray-500 text-center mt-2" id="message-input-help" aria-live="polite">
          Press Enter to send, Shift + Enter for new line
        </p>
      </form>
    </div>
  );
}
