---
layout: default
title: What's New

---

# What's New in Pixella v1.20 (1.20.7)

Welcome to the release notes for Pixella v1.20 (1.20.7)! This version introduces several new features, improvements, and bug fixes to enhance your experience with Pixella. Below is a summary of the key changes:

## New Features

- **Enhanced Model Support**: Added support for the latest Google Generative AI models, including `gemini-2.5-pro` and `gemini-2.5-flash-lite`, providing users with more options for their AI interactions.
- **Improved Configuration Options**: Users can now set additional configuration parameters via the CLI and `.env` file, allowing for greater customization of their Pixella experience.
- **Background UI Enhancements**: The Web UI can now be run in the background with improved logging capabilities, making it easier to manage long-running sessions.

## Improvements

- **Optimized Performance**: Various performance optimizations have been made to reduce response times and improve overall efficiency.
- **Better Error Handling**: Enhanced error messages and handling mechanisms to provide clearer feedback when issues arise.
- **Updated Documentation**: The documentation has been updated to reflect the latest features and provide clearer setup instructions.

## Bug Fixes

- Fixed an issue where the CLI would not properly recognize certain environment variable settings.
- Fixed the GitHub Pages layout, configuration and build issues.
- Resolved minor bugs related to session management in both CLI and Web UI modes.
- Addressed Python version and command issues during installation on various operating systems.

## Known Issues
- Some users may experience compatibility issues with older and newer Python versions. It is recommended to use Python 3.11.
- Certain features may not function as expected on non-Unix based systems; testing is ongoing to improve cross-platform support, best platform is Mac.
- Retrieval-Augmented Generation (RAG) is Not fully working yet; users may encounter issues when attempting to use RAG features. Work is underway to resolve these problems in future releases.
- Session and memory management may have occasional inconsistencies; users are advised to monitor their sessions and report any anomalies.
- Background UI logging may not capture all events accurately; improvements are planned for subsequent updates.
- Some configuration options may not persist across sessions; users should verify settings after restarting Pixella chatbot.
- The `/import` command may have limitations with certain file types; users should refer to the documentation for supported formats.
- The CLI interactive mode may have occasional input handling issues; users are encouraged to report any problems encountered.
- Integration with certain third-party services may be unstable; users should check for compatibility before use.
- Not all models are supported due to the langchain google genai version
- there are still some minor bugs and performance issues that need to be addressed; users are encouraged to report any problems they encounter to help improve Pixella.

We appreciate your patience as we work to resolve these issues in future updates (v1.60).

## Conclusion

We recommend all users to upgrade to this latest version to take advantage of the new features and improvements. For detailed installation instructions, please refer to the [Installation Guide](installation.md).