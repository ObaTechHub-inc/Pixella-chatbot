---
layout: default
title: Get Started

---

# Getting Started with Pixella

This guide will help you quickly start using Pixella's Command-Line Interface (CLI) and Web User Interface (UI).

## Prerequisites

Before proceeding, ensure you have Pixella installed and configured. If not, please follow the [Installation Guide](installation.md) and [Setup and Configuration Guide](setup.md).

## 1. Command-Line Interface (CLI)

Pixella's CLI provides a powerful way to interact with the chatbot directly from your terminal.

### Interactive Mode

To start an interactive chat session:

```bash
pixella cli --interactive
```

In interactive mode, you can type your messages directly. You can also use various slash commands:

*   **`/exit` or `/quit`**: End the session.
*   **`/debug`**: Toggle debug logging for the session.
*   **`/persona [text]`**: Set or update your user persona.
*   **`/session [cmd]`**: Manage conversation sessions (e.g., `/session new`, `/session load <name>`, `/session list`).
*   **`/import [rag|doc] <file_path>`**: Import documents for RAG context or permanent chat context.
*   **`/clear`**: Clear the current conversation history.
*   **`/model [chat|embedding] <model_name>`**: Switch the active AI model.
*   **`/models [type]`**: List available chat or embedding models.
*   **`/help`**: Display a list of all available slash commands.

### Single Message Chat Mode

You can send a single message and get a response without entering interactive mode:

```bash
pixella cli "What is the capital of France?"
```

You can also specify a session to continue a conversation:

```bash
pixella cli "Tell me more about it" --session my_travel_plans
```

## 2. Web User Interface (UI)

Pixella also offers a user-friendly Web UI powered by Streamlit.

### Launching the Web UI

To launch the UI in your browser:

```bash
pixella ui
```

This will open a new tab in your default web browser (usually at `http://localhost:8501`). The UI provides a more visual way to chat, manage settings, and interact with Pixella.

### Running UI in Background

You can run the UI as a background process, freeing up your terminal:

```bash
pixella ui --background
```

To stop the background UI:

```bash
pixella ui --end
```

To view the logs of a background UI process:

```bash
pixella ui --log
```

## 3. Managing Configurations

You can adjust Pixella's settings (like API keys, models, user persona, etc.) using the `config` command:

```bash
pixella config --show       # Display current settings
pixella config --google-model gemini-2.5-pro # Change the AI model
```

For a full list of configuration options, refer to the [Setup and Configuration Guide](setup.md).

---

{% include admonition.html type="warning" title="API Quota Reminder" content="Remember to check your API quota regularly to avoid service interruptions. Monitor your usage through the Google Cloud Console or Google AI Studio." %}
