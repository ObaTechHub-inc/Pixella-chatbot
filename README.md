# 🤖 Pixella - AI Chatbot with RAG & Memory

**A powerful, production-ready chatbot system with CLI and Web UI, powered by Google Generative AI**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.20.0-blue)](version)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Active](https://img.shields.io/badge/status-active-brightgreen)]()

## 📋 Table of Contents

1. [Features](#-features)
2. [Installation](#-installation)
3. [Quick Start](#-quick-start)
4. [Configuration](#-configuration)
5. [CLI Commands](#-cli-commands)
6. [Slash Commands](#-slash-commands)
7. [Web UI](#-web-ui)
8. [Advanced Features](#-advanced-features)
9. [Architecture](#-architecture)
10. [Troubleshooting](#-troubleshooting)
11. [License](#-license)

## 🌟 Features

### Core Features

- ✅ **Multiple Interfaces**: CLI (Typer) + Web UI (Streamlit)
- ✅ **AI Models**: Google Generative AI (Gemini) integration
- ✅ **RAG System**: ChromaDB for document retrieval and embedding
- ✅ **Memory Management**: Persistent session and conversation history
- ✅ **Configuration Management**: Easy setup with `pixella config`
- ✅ **Rich Styling**: Beautiful terminal output with colors and formatting
- ✅ **Error Handling**: Comprehensive error handling with helpful messages
- ✅ **Production Ready**: Full logging, type hints, modular architecture

### Advanced Features

- 📚 **RAG (Retrieval-Augmented Generation)**: Import and query documents
- 💾 **Session Management**: Save and manage conversation sessions
- 🎯 **User Personas**: Customize AI responses with user context
- 🔧 **Slash Commands**: Discord-style commands in interactive mode
- 📊 **Statistics**: Session and usage tracking
- 🌐 **Web Settings**: Configure everything from the web UI
- 📁 **Document Upload**: Import documents directly from web UI

## 📦 Installation

### Prerequisites

- **Python 3.11 or higher** (required)
- pip package manager
- Internet connection (for dependencies)

### Automated Installation

Use the provided installation script:

```bash
# Navigate to Pixella directory
cd Pixella

# Run installation script
bash scripts/install.sh
```

This will:

1. ✓ Check Python 3.11+
2. ✓ Install dependencies
3. ✓ Create necessary directories
4. ✓ Generate .env template
5. ✓ Setup environment variables
6. ✓ Export command to PATH
7. ✓ Verify installation

### Manual Installation

```bash
# Navigate to project directory
cd Pixella

# Install Python dependencies
pip install -r requirements.txt
```

**Dependencies included:**

- `typer[all]` - CLI framework
- `streamlit` - Web interface
- `langchain` - LLM integration
- `langchain-google-genai` - Google AI models
- `chromadb` - Vector database for RAG
- `sentence-transformers` - Embedding models
- `python-dotenv` - Environment variables
- `rich` - Terminal styling

## 🎯 Quick Start

### 1. Verify Installation

```bash
python main.py
```

This runs the verification hub that checks:

- Python version (3.11+)
- Dependencies installed
- Configuration ready
- All systems operational

### 2. Initialize Configuration

```bash
pixella config --init
```

Or set API key directly:

```bash
pixella config --google-api-key "your-api-key-here"
```

### 3. Start Chatting

**Interactive CLI mode:**

```bash
pixella cli --interactive
```

**Single question:**

```bash
pixella chat "What is machine learning?"
```

**Web UI:**

```bash
pixella ui
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the Pixella directory:

```env
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional (with defaults)
GOOGLE_AI_MODEL=gemini-2.5-flash
DB_PATH=./db/chroma
USER_NAME=User
USER_PERSONA=
MEMORY_PATH=./data/memory
EMBEDDING_MODEL=all-MiniLM-L6-v2
MODELS_CACHE_DIR=./models
ALWAYS_DEBUG=false
DISABLE_COLORS=false
```

### Configuration Commands

```bash
# Interactive setup
pixella config --init

# View current configuration
pixella config --show

# Set specific values
pixella config --google-api-key "key-here"
pixella config --user-name "John"
pixella config --db-path "./custom/path"

# Reset to defaults
pixella config --reset

# Export configuration
pixella config --export settings.json

# Generate .env template
pixella config --template

# List all available options
pixella config --list
```

## 🖥️ CLI Commands

### Main Commands

```bash
# Show version
pixella --version

# Show all commands
pixella --help

# Send a single message
pixella chat "Your question here"
pixella chat "What is Python?" --debug

# Start interactive mode
pixella cli
pixella cli --interactive
pixella cli --debug

# Launch web interface
pixella ui
pixella ui --background      # Run in background
pixella ui --end             # Stop background UI
pixella ui --debug

# Run verification
python main.py

# Run test
pixella test
```

## ⚡ Slash Commands (Interactive Mode)

### User Management

```
/name, /n [text]           Set your name
/persona, /p [text]        Set your persona/context
```

### Chat Management

```
/clear, /c                 Clear conversation history
/stats, /st                Show session statistics
/sessions, /s              List all saved sessions
```

### Document & RAG

```
/rag, /ra                  Show RAG system status
/import, /i [file]         Import documents for RAG
/export, /ex [file]        Export RAG data
/models                    List available embedding models
```

### System

```
/debug, /d                 Toggle debug logging on/off
/model, /m [name]          Switch AI model
/exit, /quit, /q, /x       End the session
/help, /h, /?              Show all commands
```

### Example Usage

```bash
pixella cli --interactive
You: /name Alice
You: /persona I'm a Python expert with 10 years experience
You: /import ~/documents/python_guide.txt
You: What are decorators?
You: /rag
You: /stats
You: /exit
```

## 🌐 Web UI

### Starting the Web Interface

```bash
# Start Streamlit UI
pixella ui

# Run in background (specify port)
pixella ui --background

# Stop background UI
pixella ui --end

# With debug logging
pixella ui --debug
```

Access at: `http://localhost:8501`

### Web UI Features

#### Chat Tab

- Send messages to the chatbot
- View chat history
- Set user name and persona
- Clear chat history

#### Memory Tab

- View all sessions
- Create new sessions
- See session statistics
- Clear all memory

#### RAG Tab

- Upload documents (txt, md, pdf)
- View document count
- View RAG collection info
- Clear RAG database
- Export collection data

## 🚀 Advanced Features

### RAG (Retrieval-Augmented Generation)

Import documents to enhance chatbot responses:

```bash
# From CLI (interactive mode)
/import ~/documents/report.txt
/import ~/documents/guide.pdf

# From Web UI
1. Go to RAG Tab
2. Click file uploader
3. Select document
4. Click Import
```

### Session Management

Save and manage conversations:

```bash
# List sessions
/sessions

# Create new session
/new

# Clear current session
/clear

# Export session
/export sessions_backup.json
```

### User Personalization

Customize AI responses:

```bash
# Set name
/name "Your Name"

# Set persona
/persona "I am a senior software engineer specializing in Python and distributed systems"
```

### Model Information

```bash
# View current model
/model

# List available models
/models

# Change model (from config)
pixella config --google-model "gemini-2.5-flash"
```

## 📐 Architecture

### Project Structure

```
Pixella/
├── main.py                 # Verification hub & central entrypoint
├── test.py                 # Test script
├── entrypoint.py           # Main CLI router
├── cli.py                  # CLI interface with slash commands
├── app.py                  # Streamlit web UI
├── chatbot.py              # Core AI chatbot
├── config.py               # Configuration management
├── chromadb_rag.py         # RAG system with ChromaDB
├── memory.py               # Session & memory management
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .env.template           # Template with all options
├── LICENSE                 # MIT License
├── README.md               # This file
├── bin/
│   └── pixella            # Global command wrapper
├── scripts/
│   └── install.sh         # Installation script
├── db/
│   └── chroma/            # ChromaDB storage (created on first use)
├── data/
│   └── memory/            # Session data (created on first use)
└── models/                # Embedding models (created on first use)
```

### Data Flow

```
User Input (CLI/Web UI)
    ↓
├─→ Config Management (config.py)
├─→ Memory System (memory.py)
│   ├─→ SQLite Database / JSON Files
│   └─→ Session Persistence
├─→ RAG System (chromadb_rag.py)
│   ├─→ ChromaDB Vector Store
│   └─→ Document Retrieval
└─→ Chatbot (chatbot.py)
    └─→ Google Generative AI API
```

### Module Dependencies

```
entrypoint.py → cli.py → chatbot.py
                    ↓
              config.py
              memory.py
              chromadb_rag.py

app.py (Streamlit UI)
  ↓
chatbot.py, config.py, memory.py, chromadb_rag.py
```

## 🔧 API Integration

### Google Generative AI

The chatbot uses Google's Generative AI API (formerly PaLM).

**Get your API key:**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key"
3. Create a new API key
4. Add to `.env` as `GOOGLE_API_KEY`

**Supported Models:**

- `gemini-2.5-flash` (default, recommended)
- `gemini-2.5-pro`
- Other Gemini models (check Google AI docs)

## 🆘 Troubleshooting

### Python Version Error

If you see an error like `Python 3.11 or higher is required`, it means you are using an older version of Python. You can check your Python version by running `python3 --version`. If you have multiple Python versions installed, you can use `python3.11` or `python3.12` to run the application.

### "Module not found" Errors

If you see an error like `ModuleNotFoundError: No module named 'langchain'`, it means you have not installed the required dependencies. You can install them by running `pip install -r requirements.txt`.

### ChromaDB Issues

If you are having issues with ChromaDB, you can try clearing the cache and re-downloading the models by running the following commands:

```bash
rm -rf models/
rm -rf db/
```

Then, reinstall the `sentence-transformers` package:

```bash
pip install --force-reinstall sentence-transformers
```

### Google API Errors

If you see an error like `429 Resource exhausted`, it means you have exceeded your API quota. You can check your usage and limits in the Google AI Studio.

### Command Not Found

If you see an error like `pixella: command not found`, it means the `pixella` command is not in your `PATH`. You can fix this by reloading your shell configuration:

```bash
# For zsh
source ~/.zshrc

# For bash
source ~/.bashrc
```

### Can't Connect to Streamlit

If you can't connect to the Streamlit UI, make sure that port 8501 is not in use. You can check this by running `lsof -i :8501`. If the port is in use, you can kill the process and try again.

## 📊 Verification

Run the verification hub to check everything:

```bash
python main.py
```

This checks:

- ✓ Python version (3.11+)
- ✓ .env file present
- ✓ Environment variables set
- ✓ All modules installed
- ✓ Directories exist
- ✓ Chatbot initializes
- ✓ RAG system ready
- ✓ Memory system ready

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

Please read the [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

You are free to:

- ✓ Use commercially
- ✓ Modify the code
- ✓ Distribute
- ✓ Use privately

You must:

- ✓ Include license notice
- ✓ Include copyright notice

**Limitations:**

- ✗ No warranty
- ✗ No liability

## 🙏 Acknowledgments

Built with:

- **Google Generative AI** - LLM backend
- **LangChain** - LLM integration framework
- **ChromaDB** - Vector database for RAG
- **Streamlit** - Web UI framework
- **Typer** - CLI framework
- **Rich** - Terminal styling
- **HuggingFace** - Embedding models

## 📞 Support

For issues and questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Run `pixella --help` for command help
3. Use `pixella config --show` to view configuration
4. Run `python main.py` to verify installation

## 🗺️ Roadmap

Planned features:

- [ ] Voice input/output support
- [ ] Advanced RAG with multi-document search
- [ ] Session export/import
- [ ] Custom model selection UI
- [ ] Plugin system
- [ ] Analytics dashboard
- [ ] Batch processing
- [ ] API server mode

---

**Made with ❤️ by Pixella Contributors**

Last updated: December 2025 - version 1.0.0 -> 1.20.0
Python 3.11+ | MIT License