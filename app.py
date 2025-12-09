# AVOID MODIFYING THIS FILE EXCEPT YOU KNOW WHAT YOU ARE DOING

"""
Pixella Web UI Module
Streamlit-based web interface for the Pixella chatbot powered by Google Generative AI

"""

import streamlit as st
import logging
import sys
import os
from pathlib import Path
import json
from typing import Optional


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from chatbot import chatbot, ChatbotError, ConfigurationError, APIError
from config import get_config, set_config
from memory import MemoryManager

# Try to import memory and RAG modules
try:
    from memory import get_memory
    memory: Optional[MemoryManager] = get_memory()
except Exception as e:
    logging.warning(f"Memory module not available: {e}")
    memory = None

try:
    from chromadb_rag import get_rag
    rag = get_rag()
except Exception as e:
    logging.warning(f"RAG module not available: {e}")
    rag = None

# Configure logging - suppress by default, enable with PIXELLA_DEBUG environment variable
config = get_config()
debug_mode = config.get("ALWAYS_DEBUG", "false").lower() == "true"

if debug_mode:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("langchain").setLevel(logging.DEBUG)
    logging.getLogger("langchain_google_genai").setLevel(logging.DEBUG)
else:
    logging.disable(logging.CRITICAL)
    logging.basicConfig(level=logging.CRITICAL)
    logging.getLogger("langchain").setLevel(logging.CRITICAL)
    logging.getLogger("langchain_google_genai").setLevel(logging.CRITICAL)
    logging.getLogger("google").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("grpc").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Pixella Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={"Get help": "https://github.com"}
)

# Custom CSS with enhanced styling
st.markdown("""
    <style>
        /* Main title */
        .main-title {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            font-size: 3rem;
            font-weight: 900;
            margin-bottom: 0.3rem;
            letter-spacing: 2px;
        }
        
        /* Subtitle */
        .subtitle {
            text-align: center;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 2rem;
        }
        
        /* User message */
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.2rem;
            border-radius: 1rem;
            margin: 0.8rem 0;
            border-left: 5px solid #667eea;
            color: white;
            box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2);
        }
        
        .user-label {
            font-weight: bold;
            font-size: 0.9rem;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }
        
        .user-text {
            font-size: 1rem;
            line-height: 1.5;
        }
        
        /* Bot message */
        .bot-message {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 1.2rem;
            border-radius: 1rem;
            margin: 0.8rem 0;
            border-left: 5px solid #f5576c;
            color: white;
            box-shadow: 0 4px 6px rgba(245, 87, 108, 0.2);
        }
        
        .bot-label {
            font-weight: bold;
            font-size: 0.9rem;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }
        
        .bot-text {
            font-size: 1rem;
            line-height: 1.5;
        }
        
        /* Input area */
        .input-section {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(245, 87, 108, 0.1));
            padding: 1.5rem;
            border-radius: 1rem;
            margin: 1rem 0;
            border: 2px solid rgba(102, 126, 234, 0.3);
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: bold;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Chat history header */
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            font-weight: bold;
            text-align: center;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: #888;
            font-size: 0.85rem;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid #eee;
        }
        
        /* Spinner text */
        .thinking-text {
            color: #667eea;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Helper to read network URL from log file
def get_network_url():
    log_file = os.path.expanduser("~/.pixella_ui.log")
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                if "Network URL: " in line:
                    return line.split("Network URL: ")[1].split("\n")[0].strip()
    return "http://localhost:8501" # Default fallback

# Helper to read PID from file
def get_ui_pid():
    pid_file = os.path.expanduser("~/.pixella_ui.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                data = json.load(f)
                return data.get("pid")
        except json.JSONDecodeError:
            return None
    return None


def display_message(role, content):
    """Display a message in the chat UI."""
    if role == "user":
        st.markdown(
            f'<div class="user-message">'
            f'<div class="user-label">👤 You</div>'
            f'<div class="user-text">{content}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="bot-message">'
            f'<div class="bot-label">🤖 Pixella</div>'
            f'<div class="bot-text">{content}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# Initialize session state for chat history and settings
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
    if memory:
        sessions = memory.get_all_sessions()
        if sessions:
            st.session_state.session_id = sessions[0]["session_id"]
            session = memory.get_session(st.session_state.session_id)
            if session:
                st.session_state.messages = [{"role": m.role, "content": m.content} for m in session.messages]
if "creating_new_session" not in st.session_state:
    st.session_state.creating_new_session = False

config = get_config()
if "user_name" not in st.session_state:
    st.session_state.user_name = config.get("USER_NAME", "User")
if "user_persona" not in st.session_state:
    st.session_state.user_persona = config.get("USER_PERSONA", "")

# Header
st.markdown('<div class="main-title">🤖 PIXELLA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">✨ Powered by Google Generative AI</div>', unsafe_allow_html=True)

# Check if chatbot is initialized
if chatbot is None:
    st.error("❌ Failed to initialize chatbot. Please check your .env file and API configuration.")
    st.stop()

if not memory:
    st.warning("Memory module not available. Chat history will not be saved.")
if not rag:
    st.warning("RAG module not available. Document-based answers will not be available.")

# Sidebar with settings
with st.sidebar:
    # API Quota Warning Note
    st.warning("Note: Make sure to know and follow the limit of your API quota for models to avoid exceeding limits.", icon="⚠️")
    
    st.markdown("### ⚙️ Settings")
    st.divider()
    
    # Settings tabs
    settings_tab1, settings_tab2, settings_tab3, settings_tab4 = st.tabs(["Chat", "Memory", "Models", "RAG"])
    
    with settings_tab1:
        st.markdown("#### Chat Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                if memory and st.session_state.session_id:
                    if memory.clear_session_messages(st.session_state.session_id):
                        st.session_state.messages = []
                        st.success("Chat history cleared!")
                    else:
                        st.error("Failed to clear chat history.")
                else:
                    st.session_state.messages = []
                    st.warning("Memory not available. Only UI chat history cleared.")
                st.rerun()
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        st.divider()
        
        # User name and persona
        st.session_state.user_name = st.text_input(
            "👤 Your Name",
            value=st.session_state.user_name,
            placeholder="Enter your name..."
        )
        
        st.session_state.user_persona = st.text_area(
            "🎭 Your Persona",
            value=st.session_state.user_persona,
            placeholder="Describe your role or context (e.g., 'a python developer')...",
            height=100
        )
        if st.button("💾 Save User Info", use_container_width=True):
            set_config("USER_NAME", st.session_state.user_name)
            set_config("USER_PERSONA", st.session_state.user_persona)
            st.success("User info saved to config!")
        st.caption("Note: Do not enter sensitive information.")

        st.divider()

        st.markdown("#### Document Import for session")
        temp_doc_file = st.file_uploader(
            "Upload document for current chat context",
            type=["txt", "md", "pdf", "csv", "json"],
            key="temp_doc_uploader"
        )
        if temp_doc_file is not None:
            if st.button("Import for Current Chat", use_container_width=True):
                if chatbot:
                    try:
                        with st.spinner("Importing document..."):
                            # Streamlit's file_uploader reads the file into a BytesIO object
                            # We need to read its content
                            file_content = temp_doc_file.read().decode('utf-8')
                            # Create a temporary file to pass to chatbot.import_document_for_chat
                            temp_file_path = Path("./temp_uploaded_doc.txt")
                            with open(temp_file_path, "w", encoding="utf-8") as f:
                                f.write(file_content)
                            
                            char_count = chatbot.import_document_for_chat(str(temp_file_path))
                            st.success(f"✓ Imported {char_count} characters from {temp_doc_file.name} for current chat.")
                            temp_file_path.unlink() # Clean up temporary file
                    except Exception as e:
                        st.error(f"Error importing document for chat: {e}")
                else:
                    st.warning("Chatbot not available for document import.")
    
    with settings_tab2:
        st.markdown("#### Memory Settings")
        
        if memory:
            st.markdown("##### Current Session")
            st.info(f"Active Session ID: {st.session_state.session_id or 'None'}")

            new_session_name = st.text_input(
                "Rename current session to:",
                value=st.session_state.session_id or "",
                key="rename_session_input"
            )
            if st.button("✏️ Rename Session", use_container_width=True):
                if st.session_state.session_id and new_session_name and new_session_name != st.session_state.session_id:
                    if memory.rename_session(st.session_state.session_id, new_session_name):
                        st.session_state.session_id = new_session_name
                        st.success(f"Session renamed to '{new_session_name}'")
                        st.rerun()
                    else:
                        st.error("Failed to rename session. Name might already exist.")
                else:
                    st.warning("Please enter a new valid session name.")
            
            st.divider()

            st.markdown("##### Session Management")
            if st.button("➕ New Session", use_container_width=True):
                st.session_state.creating_new_session = True
                st.rerun()
            
            st.divider()

            st.markdown("##### Saved Sessions")
            sessions = memory.get_all_sessions()
            if sessions:
                session_ids = [s['session_id'] for s in sessions]
                selected_session_id = str(st.selectbox("Load Session:", session_ids, key="load_session_select"))
                if st.button("📂 Load Selected Session", use_container_width=True):
                    loaded_session = memory.get_session(selected_session_id)
                    if loaded_session:
                        st.session_state.session_id = loaded_session.session_id
                        st.session_state.messages = [{"role": m.role, "content": m.content} for m in loaded_session.messages]
                        st.session_state.user_name = loaded_session.user_name
                        st.session_state.user_persona = loaded_session.user_persona
                        st.success(f"Session '{selected_session_id}' loaded!")
                        st.rerun()
                    else:
                        st.error(f"Failed to load session '{selected_session_id}'.")
                
                st.divider()

                # Dropdown for deleting sessions
                sessions_to_delete_ids = [""] + [s['session_id'] for s in sessions] # Add empty option
                session_to_delete = st.selectbox("Select Session to Delete:", sessions_to_delete_ids, key="delete_session_select")
                if st.button("🗑️ Delete Selected Session", use_container_width=True):
                    if session_to_delete:
                        if memory.delete_session(session_to_delete):
                            st.success(f"Session '{session_to_delete}' deleted.")
                            if st.session_state.session_id == session_to_delete:
                                st.session_state.session_id = None
                                st.session_state.messages = []
                            st.rerun()
                        else:
                            st.error(f"Failed to delete session '{session_to_delete}'. It might not exist.")
                    else:
                        st.warning("Please select a session to delete.")
            else:
                st.info("No saved sessions.")
            
            st.divider()

            if st.button("💥 Clear ALL Memory (DANGER!)", use_container_width=True):
                if st.warning("Are you sure you want to clear ALL sessions and messages? This cannot be undone."):
                    if st.button("Yes, Clear ALL Memory", use_container_width=True, type="primary"):
                        memory.clear_all()
                        st.session_state.session_id = None
                        st.session_state.messages = []
                        st.success("All memory cleared!")
                        st.rerun()
        else:
            st.info("Memory module not available")

    with settings_tab3:
        st.markdown("#### Model Settings")

        from chatbot import get_available_chat_models, get_current_chat_model, set_chat_model
        from chromadb_rag import list_available_embedding_models, get_current_embedding_model, set_embedding_model

        # Chat model selection
        st.markdown("##### Chat Model")
        available_chat_models = get_available_chat_models()
        current_chat_model = get_current_chat_model()
        
        # Find the index of the current model
        chat_model_options = list(available_chat_models.keys())
        try:
            current_chat_index = chat_model_options.index(current_chat_model)
        except ValueError:
            current_chat_index = 0
            
        selected_chat_model = st.selectbox(
            "Select Chat Model:",
            chat_model_options,
            index=current_chat_index,
            help="Choose the generative model for the chatbot."
        )
        if selected_chat_model != current_chat_model:
            set_chat_model(selected_chat_model)
            st.success(f"Chat model set to: {selected_chat_model}")
            st.rerun()

        st.divider()

        # Embedding model selection
        st.markdown("##### Embedding Model")
        available_embedding_models = list_available_embedding_models()
        current_embedding_model = get_current_embedding_model()
        
        # Find the index of the current model
        embedding_model_options = list(available_embedding_models.keys())
        try:
            current_embedding_index = embedding_model_options.index(current_embedding_model)
        except ValueError:
            current_embedding_index = 0

        selected_embedding_model = st.selectbox(
            "Select Embedding Model:",
            embedding_model_options,
            index=current_embedding_index,
            help="Choose the model for document embeddings (RAG)."
        )
        if selected_embedding_model != current_embedding_model:
            set_embedding_model(selected_embedding_model)
            st.success(f"Embedding model set to: {selected_embedding_model}")
            st.rerun()

    with settings_tab4: # RAG Settings
        st.markdown("#### RAG Settings")
        
        if rag:
            st.markdown("##### Import Documents to RAG")
            with st.expander("Click to import RAG documents"):
                uploaded_rag_file = st.file_uploader(
                    "Upload Document to RAG",
                    type=["txt", "md", "pdf", "csv", "json"],
                    key="rag_uploader_popup"
                )
                
                if uploaded_rag_file is not None:
                    if st.button("📥 Import to RAG", use_container_width=True):
                        try:
                            with st.spinner("Processing..."):
                                # Streamlit's file_uploader reads the file into a BytesIO object
                                # We need to read its content
                                file_content = uploaded_rag_file.read().decode('utf-8')
                                count = rag.add_text(file_content, source=uploaded_rag_file.name)
                                st.success(f"✓ Added {count} chunks from {uploaded_rag_file.name} to RAG.")
                        except Exception as e:
                            st.error(f"Error importing to RAG: {e}")
            
            st.divider()
            
            # RAG info
            info = rag.get_collection_info()
            if info:
                st.markdown("##### RAG Collection Info")
                st.metric("Documents in RAG", info.get("count", 0))
                st.write(f"Collection Name: {info.get('name', 'N/A')}")
                st.write(f"Storage Path: {info.get('db_path', 'N/A')}")
            
            if st.button("🗑️ Clear RAG Collection", use_container_width=True):
                if st.warning("Are you sure you want to clear the RAG collection? This cannot be undone."):
                    if st.button("Yes, Clear RAG", use_container_width=True, type="primary"):
                        if rag.clear_all():
                            st.success("✓ RAG collection cleared")
                            st.rerun()
                        else:
                            st.error("Failed to clear RAG collection.")
        else:
            st.info("RAG module not available")

    st.divider()
    
    st.markdown(f"""
    ### 📋 About
    This chatbot is powered by:
    - **AI**: Google Generative AI
    - **Model**: {chatbot.model if chatbot else 'N/A'}
    - **Framework**: LangChain & Streamlit
    - **RAG**: ChromaDB
    - **Memory**: SQLite/JSON
    
    ### 💡 Tips
    - Ask questions clearly
    - Use natural language
    - Check your chat history
    """)


if st.session_state.creating_new_session:
    st.markdown("### 🆕 Create New Session")
    new_session_name = st.text_input("Enter a name for the new session:")
    if st.button("Create Session", use_container_width=True):
        if new_session_name and memory:
            session = memory.create_session(session_id=new_session_name)
            st.session_state.session_id = session.session_id
            st.session_state.messages = []
            st.session_state.creating_new_session = False
            st.success(f"New session '{session.session_id}' created!")
            st.rerun()
        else:
            st.warning("Please enter a valid session name.")
else:
    # Display chat history with enhanced styling
    if st.session_state.messages:
        st.markdown('<div class="chat-header">💬 Chat History</div>', unsafe_allow_html=True)
        
        for message in st.session_state.messages:
            display_message(message["role"], message["content"])

    # Input section with gradient background
    st.divider()
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown("### ✉️ Send a Message")

    col1, col2 = st.columns([4, 1])

    with col1:
        user_input = st.text_input(
            "Your message:",
            placeholder="Type your question here...",
            label_visibility="collapsed",
            key="user_input"
        )

    with col2:
        send_button = st.button("📤 Send", use_container_width=True, key="send_button")

    st.markdown('</div>', unsafe_allow_html=True)

    # Process user input
    if send_button and user_input.strip():
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Create session if needed
        if memory and not st.session_state.session_id:
            session = memory.create_session()
            st.session_state.session_id = session.session_id
        
        # Get bot response
        with st.spinner("🤔 Thinking..."):
            try:
                # Get RAG context if available
                rag_context = ""
                if rag:
                    results = rag.query(user_input, top_k=2)
                    if results:
                        rag_context = rag.query_with_context(user_input, top_k=2)
                
                # Add to memory if available
                if memory and st.session_state.session_id:
                    memory.add_message("user", user_input, st.session_state.session_id)
                
                # Get response
                bot_response = chatbot.chat(
                    user_input,
                    user_name=st.session_state.user_name,
                    user_persona=st.session_state.user_persona
                )
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
                # Add to memory if available
                if memory and st.session_state.session_id:
                    memory.add_message("assistant", bot_response, st.session_state.session_id)
                
                logger.info("Message processed successfully")
                st.rerun()
            except ConfigurationError as e:
                logger.error(f"Configuration error: {e}")
                st.error(f"❌ Configuration Error: {e}")
            except APIError as e:
                logger.error(f"API error: {e}")
                st.error(f"❌ API Error: {e}\n\nPlease check your internet connection and API key.")
            except ChatbotError as e:
                logger.error(f"Chatbot error: {e}")
                st.error(f"❌ Error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                st.error(f"❌ Unexpected Error: {e}")

# Footer
st.markdown("""
<div class="footer">
    Built with ❤️ using Streamlit, LangChain, and Google Generative AI
</div>
""", unsafe_allow_html=True)
