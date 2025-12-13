---
layout: default
title: Installation
---

# Installation

This document guides you through the process of installing Pixella, setting up its dependencies, and getting it ready for use.

## Quick Installation (Recommended)

For a fast and automated setup, you can use our installation script, This script will:

1.  Detect your operating system (Linux, macOS, Windows/WSL/Git Bash).
2.  Check for compatible Python (3.11+) and Git installations.
3.  Clone the repository (if running remotely).
4.  **Create and activate a Python virtual environment (`.venv`).**
5.  Install all Python dependencies into the virtual environment.
6.  Create necessary data directories.
7.  Generate a `.env` template if one doesn't exist.
8.  Prompt for your Google API Key and save it to `.env`.
9.  Create a `pixella` command wrapper in `bin/` and add it to your shell's PATH.
10. Verify the installation.

Open your terminal and run one of the following commands:
- **For macOS/Linux:**

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/ObaTechHub-inc/Pixella-chatbot/main/scripts/install.sh)"
```
- **For Windows (Git Bash/WSL):**

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/ObaTechHub-inc/Pixella-chatbot/main/scripts/install.sh)"
```
- **For Windows (PowerShell):**

Not Available Yet, use Git Bash or WSL instead.

After the script completes, follow the prompts for initial configuration.

## Prerequisites

Before installing Pixella, ensure you have the following installed on your system:

- **Python**: Version 3.11 or higher. You can download it from [python.org](https://www.python.org/downloads/).
- **Git**: For cloning the repository. Download from [git-scm.com](https://git-scm.com/downloads).
- Internet connection (for dependencies)

The installation script will handle `pip` and virtual environment setup automatically.

## Step-by-Step Installation

If you prefer a manual setup or need to troubleshoot, Also recommend for developers(contributors), follow these steps:

### 1. Clone the Repository

Open your terminal or command prompt and clone the Pixella repository:

```bash
git clone https://github.com/DominionDev-coder/Pixella-chatbot.git # Make sure this is the correct repository URL
cd Pixella-chatbot
```
Since it Cloned, the installation script is also available in the `scripts/` directory and works well when cloned.

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment (`.venv`) to manage project dependencies and avoid conflicts with other Python projects.

```bash
python3 -m venv .venv
```

Activate the virtual environment:

- **On macOS/Linux (Bash/Zsh):**
  ```bash
  source .venv/bin/activate
  ```
- **On Windows (Git Bash/WSL):**
  ```bash
  source .venv/Scripts/activate
  ```
- **On Windows (Command Prompt):**
  ```bash
  .\.venv\Scripts\activate.bat
  ```
- **On Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

### 3. Install Dependencies

With your virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Pixella

Pixella requires some configuration, primarily your Google Generative AI API Key. You can set this up interactively.

```bash
pixella config --init
```

Follow the prompts to enter your API key and other preferences. Alternatively, you can manually create a `.env` file in the `Pixella/` directory and add your `GOOGLE_API_KEY` there. Refer to `setup.md` for more detailed configuration options.

### 5. Verify Installation

You can verify that Pixella is installed correctly by running its version command:

```bash
pixella --version
```

You should see version `v1.20.7` of Pixella displayed.

## Running the Chatbot

After installation, you can run Pixella in two main modes:

- **CLI Interactive Mode**:
  ```bash
  pixella cli --interactive
  ```
- **Web UI Mode**:
  ```bash
  pixella ui
  ```

For more details on usage, refer to `get-started.md`.
