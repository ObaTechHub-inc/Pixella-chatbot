# Installation

This document guides you through the process of installing Pixella, setting up its dependencies, and getting it ready for use.

## Prerequisites

Before installing Pixella, ensure you have the following installed on your system:

*   **Python**: Version 3.9 or higher. You can download it from [python.org](https://www.python.org/downloads/).
*   **pip**: Python's package installer, usually comes with Python.
*   **Git**: For cloning the repository. Download from [git-scm.com](https://git-scm.com/downloads).

## Step-by-Step Installation

### 1. Clone the Repository

Open your terminal or command prompt and clone the Pixella repository:

```bash
git clone https://github.com/your-username/Pixella.git # Replace with actual repository URL
cd Pixella
```

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies and avoid conflicts with other Python projects.

```bash
python3 -m venv venv
```

Activate the virtual environment:

*   **On macOS/Linux:**
    ```bash
    source venv/bin/activate
    ```
*   **On Windows:**
    ```bash
    .\venv\Scripts\activate
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

You should see the current version of Pixella displayed.

## Running the Chatbot

After installation, you can run Pixella in two main modes:

*   **CLI Interactive Mode**:
    ```bash
    pixella cli --interactive
    ```
*   **Web UI Mode**:
    ```bash
    pixella ui
    ```

For more details on usage, refer to `get-started.md`.
