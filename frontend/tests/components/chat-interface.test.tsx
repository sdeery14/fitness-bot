/**
 * Component tests for ChatInterface
 *
 * Tests conversational AI interface for fitness plan generation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '@/components/chat/chat-interface';

// Mock the API hooks
vi.mock('@/hooks/use-conversation', () => ({
  useConversation: () => ({
    conversationId: 'test-conversation-id',
    messages: [
      {
        id: '1',
        sender_type: 'user',
        message_content: 'I want to lose 15 pounds',
        created_at: new Date().toISOString(),
      },
      {
        id: '2',
        sender_type: 'assistant',
        message_content: 'Great goal! Let me help you create a plan.',
        created_at: new Date().toISOString(),
      },
    ],
    isLoading: false,
    sendMessage: vi.fn(),
    startNewConversation: vi.fn(),
  }),
}));

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders conversation messages', () => {
    render(<ChatInterface conversationId="test-id" />);

    expect(screen.getByText(/I want to lose 15 pounds/i)).toBeInTheDocument();
    expect(screen.getByText(/Great goal!/i)).toBeInTheDocument();
  });

  it('displays user and assistant messages with correct styling', () => {
    render(<ChatInterface conversationId="test-id" />);

    const userMessage = screen.getByText(/I want to lose 15 pounds/i);
    const assistantMessage = screen.getByText(/Great goal!/i);

    // User messages should be right-aligned
    expect(userMessage.closest('[data-sender="user"]')).toBeInTheDocument();
    // Assistant messages should be left-aligned
    expect(assistantMessage.closest('[data-sender="assistant"]')).toBeInTheDocument();
  });

  it('allows user to send new messages', async () => {
    const user = userEvent.setup();
    const { useConversation } = await import('@/hooks/use-conversation');
    const mockSendMessage = vi.fn();
    vi.mocked(useConversation).mockReturnValue({
      conversationId: 'test-id',
      messages: [],
      isLoading: false,
      sendMessage: mockSendMessage,
      startNewConversation: vi.fn(),
    } as any);

    render(<ChatInterface conversationId="test-id" />);

    const input = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await user.type(input, 'I have access to a gym');
    await user.click(sendButton);

    expect(mockSendMessage).toHaveBeenCalledWith('I have access to a gym');
  });

  it('disables input while message is sending', () => {
    const { useConversation } = require('@/hooks/use-conversation');
    vi.mocked(useConversation).mockReturnValue({
      conversationId: 'test-id',
      messages: [],
      isLoading: true,
      sendMessage: vi.fn(),
      startNewConversation: vi.fn(),
    } as any);

    render(<ChatInterface conversationId="test-id" />);

    const input = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('shows loading indicator while waiting for response', () => {
    const { useConversation } = require('@/hooks/use-conversation');
    vi.mocked(useConversation).mockReturnValue({
      conversationId: 'test-id',
      messages: [],
      isLoading: true,
      sendMessage: vi.fn(),
      startNewConversation: vi.fn(),
    } as any);

    render(<ChatInterface conversationId="test-id" />);

    expect(screen.getByText(/typing/i)).toBeInTheDocument();
  });

  it('scrolls to bottom when new messages arrive', async () => {
    const scrollIntoViewMock = vi.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { useConversation } = require('@/hooks/use-conversation');
    const { rerender } = render(<ChatInterface conversationId="test-id" />);

    // Add a new message
    vi.mocked(useConversation).mockReturnValue({
      conversationId: 'test-id',
      messages: [
        {
          id: '3',
          sender_type: 'user',
          message_content: 'New message',
          created_at: new Date().toISOString(),
        },
      ],
      isLoading: false,
      sendMessage: vi.fn(),
      startNewConversation: vi.fn(),
    } as any);

    rerender(<ChatInterface conversationId="test-id" />);

    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalled();
    });
  });
});
