# AVOID MODIFYING THIS FILE EXCEPT YOU KNOW WHAT YOU ARE DOING

"""
Memory Management Module

Handles conversation history, session storage, and user context persistence
Works with both CLI and Web UI

"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sqlite3
from dataclasses import dataclass, asdict, field

from config import get_config

ENV_PATH = Path(".env")

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in a conversation"""
    role: str  # "user", "assistant", or "document_context"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)


@dataclass
class Session:
    """Represents a conversation session"""
    session_id: str
    user_name: str = "User"
    user_persona: str = ""
    model: str = "gemini-2.5-flash"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    messages: List[Message] = field(default_factory=list)
    context: Dict = field(default_factory=dict)  # RAG context, user info, etc.


class MemoryManager:
    """
    Manages conversation history and session persistence
    Supports both JSON file storage and SQLite database
    """
    
    def __init__(self, storage_path: str = "./data/memory", use_db: bool = True):
        """
        Initialize Memory Manager
        
        Args:
            storage_path: Base path for storing memory data
            use_db: Use SQLite database (True) or JSON files (False)
        """
        self.storage_path = Path(storage_path)
        self.use_db = use_db
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Current session
        self.current_session = None
        
        if use_db:
            self.db_path = self.storage_path / "memory.db"
            self._init_database()
        
        logger.debug(f"MemoryManager initialized at {storage_path}")
    
    def _init_database(self):
        """Initialize SQLite database for session and message storage"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_name TEXT,
                    user_persona TEXT,
                    model TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    context TEXT
                )
            """)
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.debug("Database initialized")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def create_session(
        self,
        session_id: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ) -> Session:
        """
        Create a new conversation session
        
        Args:
            session_id: Custom session ID (auto-generated if None)
            model: AI model to use
        
        Returns:
            New Session object
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = get_config()
        user_name = config.get("USER_NAME", "User")
        user_persona = config.get("USER_PERSONA", "")

        session = Session(
            session_id=session_id,
            user_name=user_name,
            user_persona=user_persona,
            model=model
        )
        
        if self.use_db:
            self._save_session_to_db(session)
        else:
            self._save_session_to_file(session)
        
        self.current_session = session
        logger.debug(f"Created session {session_id}")
        return session
    
    def _save_session_to_db(self, session: Session):
        """Save session to SQLite database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO sessions 
                (session_id, user_name, user_persona, model, created_at, updated_at, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_name,
                session.user_persona,
                session.model,
                session.created_at,
                session.updated_at,
                json.dumps(session.context)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving session to database: {e}")
    
    def _save_session_to_file(self, session: Session):
        """Save session to JSON file"""
        try:
            file_path = self.storage_path / f"{session.session_id}.json"
            with open(file_path, 'w') as f:
                json.dump(asdict(session), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving session to file: {e}")
            
    def save_session(self, session: Session):
        """Saves the current state of a session."""
        session.updated_at = datetime.now().isoformat()
        if self.use_db:
            self._save_session_to_db(session)
        else:
            self._save_session_to_file(session)
    
    def rename_session(self, old_session_id: str, new_session_id: str) -> bool:
        """
        Rename a session.

        Args:
            old_session_id: The current ID of the session.
            new_session_id: The new ID for the session.

        Returns:
            True if successful, False otherwise.
        """
        if not new_session_id or not new_session_id.strip():
            logger.error("New session ID cannot be empty.")
            return False

        if self.get_session(new_session_id):
            logger.error(f"Session with ID '{new_session_id}' already exists.")
            return False

        if self.use_db:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                # Need to disable foreign keys to update the primary key
                cursor.execute("PRAGMA foreign_keys=off;")
                # Start a transaction
                cursor.execute("BEGIN;")
                # Update sessions table
                cursor.execute("UPDATE sessions SET session_id = ? WHERE session_id = ?", (new_session_id, old_session_id))
                # Update messages table
                cursor.execute("UPDATE messages SET session_id = ? WHERE session_id = ?", (new_session_id, old_session_id))
                # Commit the transaction
                cursor.execute("COMMIT;")
                # Re-enable foreign keys
                cursor.execute("PRAGMA foreign_keys=on;")
                conn.close()
            except Exception as e:
                logger.error(f"Error renaming session in database: {e}")
                # Rollback transaction on error
                return False
        else:
            old_file_path = self.storage_path / f"{old_session_id}.json"
            new_file_path = self.storage_path / f"{new_session_id}.json"
            if old_file_path.exists():
                try:
                    # First, read the content and update the session_id inside the json
                    with open(old_file_path, 'r') as f:
                        data = json.load(f)
                    data['session_id'] = new_session_id
                    with open(old_file_path, 'w') as f:
                        json.dump(data, f, indent=2)

                    # Then, rename the file
                    old_file_path.rename(new_file_path)
                except Exception as e:
                    logger.error(f"Error renaming session file: {e}")
                    return False
            else:
                logger.error(f"Session file not found: {old_file_path}")
                return False

        if self.current_session and self.current_session.session_id == old_session_id:
            self.current_session.session_id = new_session_id

        logger.debug(f"Renamed session {old_session_id} to {new_session_id}")
        return True
    
    def add_message(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Message]:
        """
        Add a message to the current or specified session
        
        Args:
            role: "user" or "assistant" or "document_context"
            content: Message content
            session_id: Session ID (uses current if None)
            metadata: Optional metadata
        
        Returns:
            Message object or None if failed
        """
        if metadata is None:
            metadata = {}
        
        session_id = session_id or (self.current_session.session_id if self.current_session else None)
        
        if not session_id:
            logger.error("No active session")
            return None
        
        message = Message(role=role, content=content, metadata=metadata)
        
        if self.use_db:
            self._add_message_to_db(session_id, message)
        else:
            # Add to file-based session
            session = self.get_session(session_id)
            if session:
                session.messages.append(message)
                self._save_session_to_file(session)
        
        if self.current_session and self.current_session.session_id == session_id:
            self.current_session.messages.append(message)
        
        logger.debug(f"Added {role} message to session {session_id}")
        return message
    
    def _add_message_to_db(self, session_id: str, message: Message):
        """Add message to SQLite database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                message.role,
                message.content,
                message.timestamp,
                json.dumps(message.metadata)
            ))
            
            # Update session's updated_at
            cursor.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (datetime.now().isoformat(), session_id)
            )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding message to database: {e}")
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID
        
        Args:
            session_id: Session ID
        
        Returns:
            Session object or None if not found
        """
        if self.use_db:
            return self._get_session_from_db(session_id)
        else:
            return self._get_session_from_file(session_id)
    
    def _get_session_from_db(self, session_id: str) -> Optional[Session]:
        """Get session from SQLite database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            session = Session(
                session_id=row[0],
                user_name=row[1],
                user_persona=row[2],
                model=row[3],
                created_at=row[4],
                updated_at=row[5],
                context=json.loads(row[6]) if row[6] else {}
            )
            
            # Get messages
            cursor.execute(
                "SELECT role, content, timestamp, metadata FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,)
            )
            
            for msg_row in cursor.fetchall():
                message = Message(
                    role=msg_row[0],
                    content=msg_row[1],
                    timestamp=msg_row[2],
                    metadata=json.loads(msg_row[3]) if msg_row[3] else {}
                )
                session.messages.append(message)
            
            conn.close()
            return session
        except Exception as e:
            logger.error(f"Error getting session from database: {e}")
            return None
    
    def _get_session_from_file(self, session_id: str) -> Optional[Session]:
        """Get session from JSON file"""
        try:
            file_path = self.storage_path / f"{session_id}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            session = Session(
                session_id=data["session_id"],
                user_name=data["user_name"],
                user_persona=data["user_persona"],
                model=data["model"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                context=data.get("context", {})
            )
            
            for msg_data in data.get("messages", []):
                message = Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=msg_data.get("timestamp", datetime.now().isoformat()),
                    metadata=msg_data.get("metadata", {})
                )
                session.messages.append(message)
            
            return session
        except Exception as e:
            logger.error(f"Error getting session from file: {e}")
            return None
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Get list of all sessions (metadata only)
        
        Returns:
            List of session metadata dictionaries
        """
        if self.use_db:
            return self._get_all_sessions_from_db()
        else:
            return self._get_all_sessions_from_files()
    
    def _get_all_sessions_from_db(self) -> List[Dict]:
        """Get all sessions from database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, user_name, model, created_at, updated_at,
                       (SELECT COUNT(*) FROM messages WHERE session_id = sessions.session_id) as msg_count
                FROM sessions
                ORDER BY updated_at DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "user_name": row[1],
                    "model": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "message_count": row[5]
                })
            
            conn.close()
            return sessions
        except Exception as e:
            logger.error(f"Error getting all sessions from database: {e}")
            return []
    
    def _get_all_sessions_from_files(self) -> List[Dict]:
        """Get all sessions from JSON files"""
        try:
            sessions = []
            for file_path in self.storage_path.glob("session_*.json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                sessions.append({
                    "session_id": data["session_id"],
                    "user_name": data["user_name"],
                    "model": data["model"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "message_count": len(data.get("messages", []))
                })
            
            # Sort by updated_at descending
            sessions.sort(key=lambda x: x["updated_at"], reverse=True)
            return sessions
        except Exception as e:
            logger.error(f"Error getting sessions from files: {e}")
            return []
    
    def get_conversation_history(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Tuple[str, str]]:
        """
        Get conversation history as list of (role, content) tuples
        
        Args:
            session_id: Session ID (uses current if None)
            limit: Max number of messages to return
        
        Returns:
            List of (role, content) tuples
        """
        session_id = session_id or (self.current_session.session_id if self.current_session else None)
        
        if not session_id:
            return []
        
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages
        if limit:
            messages = messages[-limit:]
        
        return [(msg.role, msg.content) for msg in messages]
    
    def get_context_string(self, session_id: Optional[str] = None) -> str:
        """
        Get formatted context string for LLM
        
        Args:
            session_id: Session ID (uses current if None)
        
        Returns:
            Formatted context string
        """
        session_id = session_id or (self.current_session.session_id if self.current_session else None)
        
        if not session_id:
            return ""
        
        session = self.get_session(session_id)
        if not session:
            return ""
        
        context = ""
        
        # Add user context
        if session.user_persona:
            context += f"## User Context:\n{session.user_persona}\n\n"
        
        # Add conversation history (last 10 messages)
        if session.messages:
            context += "## Conversation History:\n"
            for msg in session.messages[-10:]:
                if msg.role == "document_context":
                    context += f"## Imported Document:\n{msg.content}\n"
                elif msg.role == "user":
                    context += f"User: {msg.content}\n"
                else: # assistant
                    context += f"Assistant: {msg.content}\n"
        
        return context
    
    def clear_session_messages(self, session_id: str) -> bool:
        """
        Clear all messages from a specific session without deleting the session itself.
        
        Args:
            session_id: The ID of the session to clear messages from.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.use_db:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                # Update session's updated_at to reflect the change
                cursor.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    (datetime.now().isoformat(), session_id)
                )
                conn.commit()
                conn.close()
            else:
                session = self.get_session(session_id)
                if session:
                    # Filter out only user and assistant messages to clear
                    session.messages = [msg for msg in session.messages if msg.role == "document_context"]
                    self._save_session_to_file(session)
                else:
                    logger.warning(f"Session {session_id} not found for clearing messages.")
                    return False
            
            if self.current_session and self.current_session.session_id == session_id:
                # Filter out only user and assistant messages from current session
                self.current_session.messages = [msg for msg in self.current_session.messages if msg.role == "document_context"]
            
            logger.debug(f"Cleared user/assistant messages for session {session_id}. Document contexts preserved.")
            return True
        except Exception as e:
            logger.error(f"Error clearing messages for session {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_db:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                conn.close()
            else:
                file_path = self.storage_path / f"{session_id}.json"
                if file_path.exists():
                    file_path.unlink()
            
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
            
            logger.debug(f"Deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Clear all sessions and messages
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_db:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages")
                cursor.execute("DELETE FROM sessions")
                conn.commit()
                conn.close()
            else:
                for file_path in self.storage_path.glob("session_*.json"):
                    file_path.unlink()
            
            self.current_session = None
            logger.debug("Cleared all sessions")
            return True
        except Exception as e:
            logger.error(f"Error clearing all sessions: {e}")
            return False


# Global memory manager instance
_memory_instance = None


def get_memory() -> Optional[MemoryManager]:
    """
    Get or create the global MemoryManager instance
    
    Returns:
        MemoryManager instance or None if initialization fails
    """
    global _memory_instance
    
    try:
        if _memory_instance is None:
            config = get_config()
            storage_path = config.get("MEMORY_PATH", "./data/memory")
            _memory_instance = MemoryManager(storage_path)
        return _memory_instance
    except Exception as e:
        logger.error(f"Failed to initialize memory: {e}")
        return None


def reset_memory():
    """Reset the global memory manager instance"""
    global _memory_instance
    _memory_instance = None