"""
Chatbot module for Pixella using Google Generative AI.
Main file to interact with the chatbot functionality.

"""

import os
import logging
import time # Import the time module
from pathlib import Path
from typing import Optional, List, Tuple
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI
from google.api_core.exceptions import InvalidArgument, GoogleAPIError
from config import get_config, set_config
from memory import get_memory

# Configure logging
logger = logging.getLogger(__name__)

# Define the rate limit duration in seconds
RATE_LIMIT_DURATION = 60 # 1 minute

class ChatbotError(Exception):
    """Base exception for chatbot errors."""
    pass


class ConfigurationError(ChatbotError):
    """Raised when configuration is missing or invalid."""
    pass


class APIError(ChatbotError):
    """Raised when API call fails."""
    pass


class Chatbot:
    """A wrapper class for the Google Generative AI chatbot."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the chatbot with GoogleGenerativeAI LLM. 
        
        Args:
            api_key: Google API key (uses env var if not provided)
            model: Model name (uses env var if not provided)
            
        Raises:
            ConfigurationError: If required environment variables are missing
        """
        # Load environment variables from .env file if it exists
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        
        # Get API key and model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model = model or os.environ.get("GOOGLE_AI_MODEL")
        
        # Validate configuration
        if not self.api_key:
            raise ConfigurationError(
                "GOOGLE_API_KEY not found. Please set it in .env file or pass it as parameter."
            )
        if not self.model:
            raise ConfigurationError(
                "GOOGLE_AI_MODEL not found. Please set it in .env file or pass it as parameter."
            )
        
        # Initialize LLM
        try:
            self.llm = GoogleGenerativeAI(
                google_api_key=self.api_key,
                model=self.model
            )
            logger.info(f"Chatbot initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}")
            raise ConfigurationError(f"Failed to initialize chatbot: {e}")
            
        self.last_request_time = 0 # Initialize last request time for rate limiting
    
    def set_model(self, model: str):
        """Changes the model used by the chatbot."""
        if not model or not model.strip():
            raise ValueError("Model name cannot be empty")
        
        try:
            self.model = model
            self.llm = GoogleGenerativeAI(
                google_api_key=self.api_key,
                model=self.model
            )
            logger.info(f"Chatbot model changed to: {self.model}")
        except Exception as e:
            logger.error(f"Failed to set new model: {e}")
            raise ConfigurationError(f"Failed to initialize chatbot with model {model}: {e}")

    def import_document_for_chat(self, file_path: str, session_id: Optional[str] = None) -> int:
        """
        Import document content permanently into the current session's memory.
        
        Args:
            file_path: The path to the document file.
            session_id: The ID of the session to import the document into.
                        If None, uses the current active session.
            
        Returns:
            The number of characters imported.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            memory = get_memory()
            if not memory:
                raise ChatbotError("Memory system not initialized. Cannot import document permanently.")
            
            # Get current session or create a temporary one if none is active
            current_session = memory.current_session
            if session_id:
                current_session = memory.get_session(session_id)
                if not current_session:
                    raise ChatbotError(f"Session with ID '{session_id}' not found.")
            elif not current_session:
                current_session = memory.create_session() # Create a temporary session if no active one

            # Add document content as a message with a specific role
            memory.add_message(
                role="document_context",
                content=f"Document: {Path(file_path).name}\n{content}",
                session_id=current_session.session_id if current_session else None # Ensure session ID is passed
            )
            
            logger.info(f"Imported {len(content)} characters from {file_path} permanently to session {current_session.session_id if current_session else 'N/A'}.")
            return len(content)
        except Exception as e:
            logger.error(f"Error importing document {file_path} for chat: {e}")
            raise ChatbotError(f"Could not import document: {e}")

    def chat(
        self,
        message: str,
        user_name: Optional[str] = None,
        user_persona: Optional[str] = None,
        history: Optional[List[Tuple[str, str]]] = None,
        rag_context: Optional[str] = None
    ) -> str:
        """
        Send a message to the chatbot and get a response.
        
        Args:
            message: The user's message/query
            user_name: The user's name for context
            user_persona: The user's persona for context
            history: A list of previous messages in the conversation
            rag_context: Retrieved context from RAG system
            
        Returns:
            The chatbot's response as a string
            
        Raises:
            ValueError: If message is empty or invalid
            APIError: If API call fails
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
            
        # --- Rate Limiting Logic ---
        current_time = time.time()
        elapsed_time = current_time - self.last_request_time
        
        if elapsed_time < RATE_LIMIT_DURATION:
            sleep_time = RATE_LIMIT_DURATION - elapsed_time
            logger.debug(f"Rate limit active. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time() # Update last request time
        # --- End Rate Limiting Logic ---

        # Construct a more detailed prompt if user details are provided
        prompt_parts = []
        if user_name and user_persona:
            prompt_parts.append(f"You are responding to {user_name}, whose persona is: '{user_persona}'.")
        elif user_name:
            prompt_parts.append(f"You are responding to {user_name}.")
        elif user_persona:
            prompt_parts.append(f"The user's persona is: '{user_persona}'.")
        
        # Add RAG context if available
        if rag_context:
            prompt_parts.append(rag_context)

        # Retrieve and add permanently imported document context from history
        if history:
            for role, content in history:
                if role == "document_context": # Check for our custom role
                    prompt_parts.append(f"## Imported Document Context:\n{content}")
        
        # Add conversation history (excluding document_context from prompt_parts above)
        if history:
            for role, content in history:
                if role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append(f"User's message: {message}")
        prompt = "\n\n".join(prompt_parts)
        
        try:
            logger.debug(f"Sending prompt: {prompt[:150]}...")
            result = self.llm.invoke(prompt)
            logger.debug("Response received successfully")
            return result
        except InvalidArgument as e:
            logger.error(f"Invalid API argument: {e}")
            raise APIError(f"Invalid API request: {e}")
        except GoogleAPIError as e:
            logger.error(f"Google API error: {e}")
            raise APIError(f"Google API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during chat: {e}")
            raise APIError(f"Unexpected error: {e}")


# Create a global instance for easy access
try:
    chatbot = Chatbot()
except ConfigurationError as e:
    logger.error(f"Failed to create chatbot instance: {e}")
    chatbot = None


def get_available_chat_models() -> dict[str, str]:
    """
    List available chat models. 
    
    Returns:
        Dictionary of available models with descriptions
    """
    return {
        "gemini-2.5-flash": "Latest fast and versatile model.",
        "gemini-2.5-flash-lite": "A lighter, faster version of Gemini 2.5 Flash for quicker responses.",
        "gemini-2.5-pro": "Latest most capable model for complex reasoning and understanding.",
    }


def get_current_chat_model() -> str:
    """
    Get the current chat model from config. 
    
    Returns:
        The current chat model name
    """
    config = get_config()
    return config.get("GOOGLE_AI_MODEL", "gemini-2.5-flash")


def set_chat_model(model_name: str) -> None:
    """
    Set the chat model in the config. 
    
    Args:
        model_name: The name of the model to set
    """
    set_config("GOOGLE_AI_MODEL", model_name)
    if chatbot:
        chatbot.set_model(model_name)
    logger.info(f"Chat model set to: {model_name}")

