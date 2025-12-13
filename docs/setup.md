---
layout: default
title: Setup and Configuration

---

# Setup and Configuration

This document details how to set up and configure Pixella for optimal use. Configuration is primarily managed through environment variables, which can be easily set using a `.env` file or interactively via the CLI.

## 1. Initial Configuration

The easiest way to get started with configuration is to use the interactive setup:

```bash
pixella config --init
```

This command will prompt you for essential settings like your Google API Key and preferred model.

## 2. Environment Variables (.env file)

Pixella reads its configuration from a `.env` file located in the `Pixella/` directory. You can manually create or edit this file. Here are the key environment variables:

*   **`GOOGLE_API_KEY`**: (Required) Your API key for Google Generative AI. Obtain this from the Google AI Studio.
*   **`GOOGLE_AI_MODEL`**: The name of the Google AI model to use (e.g., `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`).
*   **`CHROMA_DB_PATH`**: Path to the ChromaDB database for Retrieval-Augmented Generation (RAG). Default is `./db/chroma`.
*   **`USER_NAME`**: Your name, used by Pixella for personalized responses. Default is `User`.
*   **`USER_PERSONA`**: A description of your persona or role (e.g., "a Python developer working on AI projects"). This helps Pixella tailor its responses.
*   **`MEMORY_PATH`**: Path to the memory storage for conversation history. Default is `./data/memory`.
*   **`EMBEDDING_MODEL`**: The embedding model to use for RAG (from Google Generative AI, e.g., `models/embedding-001`).
*   **`ALWAYS_DEBUG`**: Set to `true` or `false` (default) to always enable debug logging.
*   **`DISABLE_COLORS`**: Set to `true` or `false` (default) to disable colored output in the CLI.

Example `.env` file:

```dotenv
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
GOOGLE_AI_MODEL=gemini-2.5-flash
CHROMA_DB_PATH=./db/chroma
USER_NAME=Alice
USER_PERSONA="a data scientist specializing in NLP"
MEMORY_PATH=./data/memory
EMBEDDING_MODEL=models/embedding-001
ALWAYS_DEBUG=false
DISABLE_COLORS=false
```

## 3. Managing Configuration via CLI

You can manage individual configuration settings using the `pixella config` command.

*   **Show current configuration:**
    ```bash
    pixella config --show
    ```
*   **Set Google API Key:**
    ```bash
    pixella config --google-api-key YOUR_NEW_API_KEY
    ```
*   **Set AI Model:**
    ```bash
    pixella config --google-model gemini-2.5-pro
    ```
*   **Set User Name:**
    ```bash
    pixella config --user-name "Bob"
    ```
*   **Set User Persona:**
    ```bash
    pixella config --user-persona "a software engineer focused on backend systems"
    ```
*   **Enable Always Debug Mode:**
    ```bash
    pixella config --always-debug
    ```
*   **Disable Colors:**
    ```bash
    pixella config --disable-colors
    ```
*   **Reset configuration to defaults:**
    ```bash
    pixella config --reset
    ```
*   **Export configuration to a file:**
    ```bash
    pixella config --export my_config.env
    ```
*   **Restore configuration from backup:**
    ```bash
    pixella config --restore
    ```

## 4. API Quota Reminder

**Important:** When using Google Generative AI models, be aware of your API usage limits and quotas. Exceeding these limits can lead to service interruptions. Monitor your usage through the Google Cloud Console.
