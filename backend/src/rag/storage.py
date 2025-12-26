"""
Chat History Storage Module

Handles storing and retrieving chat conversations in memory and/or on disk.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict, field
from uuid import uuid4


@dataclass
class ChatMessage:
    """Represents a single message in a chat."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Chat:
    """Represents a chat conversation with multiple messages."""
    chat_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ChatHistoryStorage:
    """
    Manages chat history storage.
    
    Features:
    - Create new chats
    - Add messages to existing chats
    - Retrieve chat history
    - Persist chats to disk (optional)
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize chat history storage.
        
        Args:
            storage_dir: Optional directory to persist chats. If None, only in-memory storage.
        """
        self.chats: Dict[str, Chat] = {}
        self.storage_dir = Path(storage_dir) if storage_dir else None
        
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self._load_existing_chats()
    
    def _load_existing_chats(self):
        """Load existing chats from disk."""
        if not self.storage_dir:
            return
        
        for chat_file in self.storage_dir.glob("*.json"):
            try:
                with open(chat_file, 'r') as f:
                    data = json.load(f)
                    messages = [ChatMessage(**msg) for msg in data.get("messages", [])]
                    chat = Chat(
                        chat_id=data["chat_id"],
                        messages=messages,
                        created_at=data.get("created_at", datetime.now().isoformat()),
                        updated_at=data.get("updated_at", datetime.now().isoformat())
                    )
                    self.chats[chat.chat_id] = chat
            except Exception as e:
                print(f"Warning: Could not load chat from {chat_file}: {e}")
    
    def _save_chat(self, chat: Chat):
        """Save a chat to disk."""
        if not self.storage_dir:
            return
        
        chat_file = self.storage_dir / f"{chat.chat_id}.json"
        with open(chat_file, 'w') as f:
            data = {
                "chat_id": chat.chat_id,
                "messages": [asdict(msg) for msg in chat.messages],
                "created_at": chat.created_at,
                "updated_at": chat.updated_at
            }
            json.dump(data, f, indent=2)
    
    def create_chat(self) -> Chat:
        """
        Create a new chat.
        
        Returns:
            Chat: New chat object with unique ID
        """
        chat_id = str(uuid4())
        chat = Chat(chat_id=chat_id)
        self.chats[chat_id] = chat
        self._save_chat(chat)
        return chat
    
    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """
        Get an existing chat by ID.
        
        Args:
            chat_id: Chat ID to retrieve
            
        Returns:
            Chat object if found, None otherwise
        """
        return self.chats.get(chat_id)
    
    def add_message_to_chat(self, chat_id: str, content: str, role: str):
        """
        Add a message to an existing chat.
        
        Args:
            chat_id: ID of the chat to add message to
            content: Message content
            role: Message role ("user" or "assistant")
        """
        chat = self.chats.get(chat_id)
        if not chat:
            raise ValueError(f"Chat {chat_id} not found")
        
        message = ChatMessage(role=role, content=content)
        chat.messages.append(message)
        chat.updated_at = datetime.now().isoformat()
        self._save_chat(chat)
    
    def get_chat_history(self, chat_id: str) -> List[Dict]:
        """
        Get chat history in dictionary format.
        
        Args:
            chat_id: ID of the chat
            
        Returns:
            List of message dictionaries
        """
        chat = self.chats.get(chat_id)
        if not chat:
            return []
        
        return [asdict(msg) for msg in chat.messages]
    
    def list_chats(self) -> List[str]:
        """
        List all chat IDs.
        
        Returns:
            List of chat IDs
        """
        return list(self.chats.keys())
    
    def delete_chat(self, chat_id: str):
        """
        Delete a chat.
        
        Args:
            chat_id: ID of the chat to delete
        """
        if chat_id in self.chats:
            del self.chats[chat_id]
            
            if self.storage_dir:
                chat_file = self.storage_dir / f"{chat_id}.json"
                if chat_file.exists():
                    chat_file.unlink()
