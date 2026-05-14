"""
Conversations Router — CRUD for conversation history

Endpoints:
  GET    /api/conversations           → list all conversations (newest first)
  GET    /api/conversations/{id}      → get all messages for a conversation
  DELETE /api/conversations/{id}      → delete a conversation and its messages
"""

from fastapi import APIRouter, HTTPException
from database import (
    list_conversations,
    get_messages_for_conversation,
    delete_conversation,
)

router = APIRouter()


@router.get("/conversations")
async def get_all_conversations():
    """
    Return all conversations ordered by most recently updated.
    Used by the sidebar to display conversation history.
    """
    return list_conversations()


@router.get("/conversations/{conversation_id}")
async def get_conversation_messages(conversation_id: str):
    """
    Return all messages for a specific conversation in chronological order.
    Used when the user clicks a conversation in the sidebar to resume it.
    """
    messages = get_messages_for_conversation(conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found or empty")
    return messages


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    delete_conversation(conversation_id)
    return {"success": True, "id": conversation_id}
