"""Contract tests for AI agent API endpoints.

Tests validate that AI endpoints conform to the API contracts defined in
specs/001-ai-fitness-planner/contracts/api-contracts.md
"""
import pytest
from httpx import AsyncClient

from src.models.user import User
from src.models.conversation import Conversation


class TestCreateConversationEndpoint:
    """Contract tests for POST /api/v1/ai/conversations"""

    @pytest.mark.asyncio
    async def test_create_conversation_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test successful conversation creation returns 201 with correct schema."""
        payload = {
            "conversation_type": "plan_creation",
            "initial_message": "I want to lose 15 pounds in 3 months"
        }

        response = await async_client.post(
            "/api/v1/ai/conversations",
            json=payload,
            headers=auth_headers
        )

        # Contract: 201 Created status
        assert response.status_code == 201

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains conversation data
        assert "data" in data
        conv_data = data["data"]
        assert "conversation_id" in conv_data
        assert conv_data["conversation_type"] == payload["conversation_type"]
        assert conv_data["status"] == "active"
        assert "started_at" in conv_data

        # Contract: Response contains metadata
        assert "metadata" in data
        assert "timestamp" in data["metadata"]

    @pytest.mark.asyncio
    async def test_create_conversation_invalid_type(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test conversation creation with invalid type returns 400 BAD_REQUEST."""
        payload = {
            "conversation_type": "invalid_type",
            "initial_message": "Test message"
        }

        response = await async_client.post(
            "/api/v1/ai/conversations",
            json=payload,
            headers=auth_headers
        )

        # Contract: 400 BAD_REQUEST status
        assert response.status_code == 400

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "code" in data["error"]

    @pytest.mark.asyncio
    async def test_create_conversation_unauthorized(self, async_client: AsyncClient):
        """Test creating conversation without auth returns 401 UNAUTHORIZED."""
        payload = {
            "conversation_type": "plan_creation",
            "initial_message": "Test message"
        }

        response = await async_client.post("/api/v1/ai/conversations", json=payload)

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401


class TestSendMessageEndpoint:
    """Contract tests for POST /api/v1/ai/conversations/{conversation_id}/messages"""

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_conversation: Conversation
    ):
        """Test successful message sending returns 200 with correct schema."""
        payload = {
            "message": "I have access to a gym with all equipment"
        }

        response = await async_client.post(
            f"/api/v1/ai/conversations/{test_conversation.id}/messages",
            json=payload,
            headers=auth_headers
        )

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains message data
        assert "data" in data
        msg_data = data["data"]
        assert "message_id" in msg_data
        assert msg_data["conversation_id"] == str(test_conversation.id)

        # Contract: User message details
        assert "user_message" in msg_data
        user_msg = msg_data["user_message"]
        assert user_msg["content"] == payload["message"]
        assert "sent_at" in user_msg

        # Contract: Assistant response details
        assert "assistant_response" in msg_data
        assistant_msg = msg_data["assistant_response"]
        assert "content" in assistant_msg
        assert "sent_at" in assistant_msg

        # Contract: Optional function calls
        if "function_calls" in assistant_msg:
            assert isinstance(assistant_msg["function_calls"], list)
            if len(assistant_msg["function_calls"]) > 0:
                func_call = assistant_msg["function_calls"][0]
                assert "function" in func_call
                assert "arguments" in func_call

    @pytest.mark.asyncio
    async def test_send_message_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test sending message to non-existent conversation returns 404 NOT_FOUND."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"message": "Test message"}

        response = await async_client.post(
            f"/api/v1/ai/conversations/{fake_id}/messages",
            json=payload,
            headers=auth_headers
        )

        # Contract: 404 NOT_FOUND status
        assert response.status_code == 404

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "NOT_FOUND" in data["error"]["code"]

    @pytest.mark.asyncio
    async def test_send_message_empty(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_conversation: Conversation
    ):
        """Test sending empty message returns 400 BAD_REQUEST."""
        payload = {"message": ""}

        response = await async_client.post(
            f"/api/v1/ai/conversations/{test_conversation.id}/messages",
            json=payload,
            headers=auth_headers
        )

        # Contract: 400 BAD_REQUEST status
        assert response.status_code == 400

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"

    @pytest.mark.asyncio
    async def test_send_message_unauthorized(
        self, async_client: AsyncClient, test_conversation: Conversation
    ):
        """Test sending message without auth returns 401 UNAUTHORIZED."""
        payload = {"message": "Test message"}

        response = await async_client.post(
            f"/api/v1/ai/conversations/{test_conversation.id}/messages",
            json=payload
        )

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401


class TestGetConversationEndpoint:
    """Contract tests for GET /api/v1/ai/conversations/{conversation_id}"""

    @pytest.mark.asyncio
    async def test_get_conversation_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_conversation: Conversation
    ):
        """Test successful conversation retrieval returns 200 with correct schema."""
        response = await async_client.get(
            f"/api/v1/ai/conversations/{test_conversation.id}",
            headers=auth_headers
        )

        # Contract: 200 OK status
        assert response.status_code == 200

        data = response.json()

        # Contract: Response has success status
        assert data["status"] == "success"

        # Contract: Response contains conversation data
        assert "data" in data
        conv_data = data["data"]
        assert conv_data["id"] == str(test_conversation.id)
        assert "conversation_type" in conv_data
        assert "status" in conv_data

        # Contract: Messages array
        assert "messages" in conv_data
        assert isinstance(conv_data["messages"], list)
        if len(conv_data["messages"]) > 0:
            message = conv_data["messages"][0]
            assert "sender_type" in message
            assert "message_content" in message
            assert "sent_at" in message

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent conversation returns 404 NOT_FOUND."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await async_client.get(
            f"/api/v1/ai/conversations/{fake_id}",
            headers=auth_headers
        )

        # Contract: 404 NOT_FOUND status
        assert response.status_code == 404

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "error" in data
        assert "NOT_FOUND" in data["error"]["code"]

    @pytest.mark.asyncio
    async def test_get_conversation_unauthorized(
        self, async_client: AsyncClient, test_conversation: Conversation
    ):
        """Test getting conversation without auth returns 401 UNAUTHORIZED."""
        response = await async_client.get(
            f"/api/v1/ai/conversations/{test_conversation.id}"
        )

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401


class TestStreamConversationEndpoint:
    """Contract tests for GET /api/v1/ai/conversations/{conversation_id}/stream"""

    @pytest.mark.asyncio
    async def test_stream_conversation_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_conversation: Conversation
    ):
        """Test successful streaming endpoint returns Server-Sent Events."""
        async with async_client.stream(
            "GET",
            f"/api/v1/ai/conversations/{test_conversation.id}/stream",
            headers=auth_headers
        ) as response:
            # Contract: 200 OK status
            assert response.status_code == 200

            # Contract: Content-Type is text/event-stream
            assert "text/event-stream" in response.headers.get("content-type", "")

            # Contract: Receives SSE data
            # Note: Full streaming test requires async iteration
            # This basic test validates the endpoint exists and returns correct headers

    @pytest.mark.asyncio
    async def test_stream_conversation_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test streaming non-existent conversation returns 404 NOT_FOUND."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await async_client.get(
            f"/api/v1/ai/conversations/{fake_id}/stream",
            headers=auth_headers
        )

        # Contract: 404 NOT_FOUND status
        assert response.status_code == 404

        data = response.json()

        # Contract: Error response format
        assert data["status"] == "error"
        assert "NOT_FOUND" in data["error"]["code"]

    @pytest.mark.asyncio
    async def test_stream_conversation_unauthorized(
        self, async_client: AsyncClient, test_conversation: Conversation
    ):
        """Test streaming conversation without auth returns 401 UNAUTHORIZED."""
        response = await async_client.get(
            f"/api/v1/ai/conversations/{test_conversation.id}/stream"
        )

        # Contract: 401 UNAUTHORIZED status
        assert response.status_code == 401
