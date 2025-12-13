# Contributing to Pixella

We welcome contributions to Pixella! Before you start, please take a moment to read these guidelines.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## How Can I Contribute?

### Reporting Bugs

- Ensure the bug hasn't already been reported.
- When reporting, use a clear and descriptive title.
- Include as much detail as possible: steps to reproduce, expected behavior, actual behavior, screenshots (if applicable), and your environment (OS, Python version, Pixella version).

### Suggesting Enhancements

- Use a clear and descriptive title.
- Explain why this enhancement would be useful.
- Provide concrete examples where appropriate.

### Code Contributions

1.  **Fork the repository** on GitHub.
2.  **Clone your forked repository** to your local machine.
    ```bash
    git clone https://github.com/your-username/Pixella.git
    cd Pixella
    ```
3.  **Create a new branch** for your feature or bug fix.
    ```bash
    git checkout -b feature/your-feature-name-or-bugfix/issue-number
    ```
4.  **Set up your development environment**:

    **Recommended: Use the automated installation script**

    ```bash
    # Clone the repository
    git clone https://github.com/DominionDev-coder/Pixella-chatbot.git
    cd Pixella-chatbot

    # Run the installation script (recommended for developers)
    bash scripts/install.sh
    ```

    This script will automatically:

    - Set up Python 3.11+ and virtual environment
    - Install all dependencies
    - Configure your environment
    - Set up the `pixella` command

    **Alternative: Manual setup**

    - Ensure you have Python 3.11+ installed.
    - Create and activate a virtual environment:
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
      ```
    - Install project dependencies:
      ```bash
      pip install -r requirements.txt
      ```
    - Configure your `.env` file (refer to `Pixella/config.py` for details or run `pixella config --init`).
    - use this `gitignore` template to avoid committing unnecessary files:

      ```
      # Byte-compiled / optimized / DLL files
        __pycache__/
        *.py[cod]
        *$py.class

      # C extensions
         *.so

      # Distribution / packaging
         .Python
         build/
         dist/
         download/
         /lib/
         wheels/
         pip-wheel-metadata/
         share/python-wheels/
         MANIFEST
      # PyInstaller
        *.manifest
        *.spec

      # Unit test / coverage reports
         *.cover
         *.py,cover
         .pytest_cache/

      # git files
         .gitignore

      # Environment variables
          .env
          .env.bak
          .env.local
          .env.*.local
          .env.template

      # IDEs
          .vscode/
          .idea/
          *.swp
          *.swo
          *~
          .DS_Store

      # Streamlit
          .streamlit/

      # Logs
          *.log
          logs/

      # memory and database files
          data
          db

      ```

5.  **Make your changes**:
    - **Focus on necessary changes**: Only modify the parts of the code directly relevant to your feature or bug fix. Avoid making unrelated stylistic or refactoring changes in the same pull request.
    - **Avoid committing ignored files**: Do not commit files that are typically ignored (e.g., `venv/`, `__pycache__/`, `.env` files). Refer to the recommended `.gitignore` template in `README.md` for details.
    - Follow existing code style and conventions.
    - Add unit tests for new features or bug fixes.
    - Ensure all existing tests pass.
6.  **Run tests**:
    ```bash
    python -m pytest
    ```
7.  **Commit your changes** with a clear and concise commit message.
    ```bash
    git commit -m "feat: Add new feature"
    # or "fix: Fix bug in X"
    ```
8.  **Push your branch** to your forked repository.
    ```bash
    git push origin feature/your-feature-name-or-bugfix/issue-number
    ```
9.  **Open a Pull Request** on GitHub:
    - Provide a descriptive title and detailed explanation of your changes.
    - Reference any related issues.

## Style Guides

- **Python**: Adhere to PEP 8 guidelines. We use `flake8` and `black` for linting and formatting.
- **Documentation**: Use Markdown for documentation files.

Thank you for contributing to Pixella!
[Read the Docs](https://obatechhub-inc.github.io/Pixella-chatbot/) for more information on setting up your development environment and developing.
