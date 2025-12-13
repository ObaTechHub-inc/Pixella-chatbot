---
layout: default
title: Development Setup Guide

---

# 🚀 Development Setup Guide

This guide outlines the recommended setup process for developers and contributors working on Pixella.

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.11 or higher** (required)
- **Git** for version control
- **Internet connection** for downloading dependencies
- **A Google AI API key** (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))

## ⚙️ Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/DominionDev-coder/Pixella-chatbot.git
cd Pixella-chatbot
```

Then Cofigure your environment and 

## 📁 Project Structure

After setup, your project structure should look like this:

```
Pixella-chatbot/
├── .venv/                    # Python virtual environment
├── bin/
│   └── pixella              # Command wrapper
├── data/
│   └── memory/              # Session data storage
├── db/
│   └── chroma/              # Vector database
├── docs/                    # Documentation
├── scripts/
│   └── install.sh           # Installation script
├── .env                     # Environment configuration
├── main.py                  # Main application entry point
├── pixella/                 # Main package
│   ├── __init__.py
│   ├── cli.py              # CLI commands
│   ├── config.py           # Configuration management
│   ├── memory.py           # Memory management
│   └── ...
└── requirements.txt         # Python dependencies
```

## 🔧 Development Workflow

### 1. Activate Your Environment

```bash
# The installation script should have added pixella to your PATH
# If not, activate the virtual environment manually:
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### 2. Verify Installation

```bash
# Check that everything is working
python main.py

# Or use the pixella command
pixella --help
```

### 3. Configure API Key

If you didn't set it during installation:

```bash
pixella config --google-api-key "your-api-key-here"
```

### 4. Start Developing

```bash
# Run in development mode
pixella cli --interactive

# Or start the web UI
pixella ui
```

## 🧪 Testing

```bash
# Run the test suite
python -m pytest

# Run specific tests
python -m pytest tests/test_specific.py

# Run with coverage
python -m pytest --cov=pixella
```

## 📝 Code Style

We follow these conventions:

- **Python**: PEP 8 with Black formatting
- **Commits**: Conventional commits (`feat:`, `fix:`, `Implement`, `Minor Changes`, `Improvement` etc.)
- **Documentation**: Clear, concise comments and docstrings

### Linting and Formatting

```bash
# Format code
black pixella/

# Check style
flake8 pixella/

# Type checking
mypy pixella/
```

## 🔄 Development Commands

### Common Tasks

```bash
# Update dependencies
pip install -r requirements.txt

# Clean cache files
find . -type d -name __pycache__ -exec rm -rf {} +

# Reset database (be careful!)
rm -rf db/ data/

# View logs
tail -f pixella.log
```

### Working with Git
1.  **Create a new branch** for your feature or bugfix:
    ```bash
    # Create a feature branch
    git checkout -b feature/your-feature-name
    # or for bugfix
    git checkout -b bugfix/issue-number```
  Start coding!

2. Create a .gitignore file to exclude unnecessary files:
   refer to the .gitignore template in README.md for details.

3. Make your changes...
  - Write codes
  Avoid creating unrelated files or changes in the same pull request.
  Only use python language for coding.

  - Run tests
    ```bash
    python -m pytest
    ```

  - Commit with conventional format
    ```bash
    git commit -m "feat: Add new feature description"
    # or "fix: Fix bug description"
    ```

  - Push and create PR
    ```bash
    git push origin feature/your-feature-name
  Open a Pull Request on GitHub with a descriptive title and explanation.
   

## 🐛 Troubleshooting

### Common Issues

**"pixella command not found"**

```bash
export PATH="$PWD/bin:$PATH"
```

**"Module not found" errors**

```bash
# Reactivate virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**"API key not configured"**

```bash
pixella config --google-api-key "your-key-here"
# or edit .env file directly
```

### Getting Help

- Check the [README.md](README.md) for general usage
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Open an issue on GitHub for bugs or feature requests

## 🎯 Next Steps

1. Explore the codebase in `pixella/`
2. Check out the CLI commands with `pixella --help`
3. Try the web UI with `pixella ui`
4. Look at existing issues for contribution ideas

Happy coding! 🤖
