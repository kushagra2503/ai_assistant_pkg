# TermCrawl AI Assistant - Installation Guide

This guide provides comprehensive instructions for installing and setting up the TermCrawl AI Assistant on your system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
   - [Install from GitHub](#install-from-github)
   - [Install from Source](#install-from-source)
   - [Install for Development](#install-for-development)
3. [API Keys Setup](#api-keys-setup)
4. [Running TermCrawl AI Assistant](#running-termcrawl-ai-assistant)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Uninstallation](#uninstallation)

## Prerequisites

Before installing TermCrawl AI Assistant, ensure you have the following:

- **Python 3.7 or higher** installed on your system
- **pip** (Python package installer)
- **Git** (for installation from GitHub)
- **API keys** for at least one of the supported AI models:
  - Google Gemini API key
  - OpenAI API key

### Checking Python Version

```bash
python --version
```

Make sure the output shows Python 3.7 or higher.

## Installation Methods

### Install from GitHub

The easiest way to install TermCrawl AI Assistant is directly from GitHub:

```bash
pip install git+https://github.com/kushagra2503/ai_assistant_pkg.git
```

This will install the package globally on your system, making the `ai-assistant` command available from any terminal.

### Install from Source

If you have downloaded or cloned the source code:

1. Clone the repository (if you haven't already):
   ```bash
   git clone https://github.com/kushagra2503/ai_assistant_pkg.git
   cd ai_assistant_pkg
   ```

2. Install the package:
   ```bash
   pip install .
   ```

### Install for Development

If you plan to modify the code or contribute to the project:

```bash
git clone https://github.com/kushagra2503/ai_assistant_pkg.git
cd ai_assistant_pkg
pip install -e .
```

The `-e` flag installs the package in "editable" mode, allowing you to make changes to the code without reinstalling.

## API Keys Setup

TermCrawl AI Assistant requires API keys to function. You can use either Google Gemini or OpenAI (or both).

### Option 1: Environment Variables

Set the API keys as environment variables:

**Windows (Command Prompt)**:
```cmd
set GEMINI_API_KEY=your_gemini_api_key
set OPENAI_API_KEY=your_openai_api_key
```

**Windows (PowerShell)**:
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
$env:OPENAI_API_KEY="your_openai_api_key"
```

**Linux/macOS**:
```bash
export GEMINI_API_KEY=your_gemini_api_key
export OPENAI_API_KEY=your_openai_api_key
```

### Option 2: .env File

Create a `.env` file in your working directory:

```
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
```

### Option 3: Configure Within the Application

You can also configure the API keys within the application:

1. Run the assistant: `ai-assistant`
2. Choose option `C` for Configure settings
3. Follow the prompts to enter your API keys

## Running TermCrawl AI Assistant

After installation, you can run TermCrawl AI Assistant from any terminal:

```bash
ai-assistant
```

### Command-Line Interface

The assistant provides an interactive interface with the following options:

- **S** - Speak to the assistant (using voice input)
- **T** - Type a question (text input)
- **C** - Configure settings
- **Q** - Quit

### Using Screenshots

When typing a question, you'll be asked if you want TermCrawl to capture your screen for reference. This can be helpful when you need assistance with something visible on your screen.

## Configuration

TermCrawl AI Assistant stores its configuration in a `config.json` file in the directory where you run the command. This file contains:

- The default AI model to use
- The assistant's role/personality
- Other settings

You can modify these settings through the application's configuration menu (option `C`).

## Troubleshooting

### Common Issues

1. **Command not found: ai-assistant**
   - Ensure Python's scripts directory is in your PATH
   - Try reinstalling the package: `pip install --force-reinstall git+https://github.com/kushagra2503/ai_assistant_pkg.git`

2. **API Key errors**
   - Verify your API keys are correct
   - Check that the environment variables are properly set

3. **Missing dependencies**
   - Run: `pip install -r requirements.txt` from the source directory
   - Or reinstall the package: `pip install --force-reinstall git+https://github.com/kushagra2503/ai_assistant_pkg.git`

4. **Voice recognition issues**
   - Ensure your microphone is properly connected and has necessary permissions
   - Install additional dependencies: `pip install pyaudio`

### Getting Help

If you encounter issues not covered here, please:
- Check the [GitHub repository](https://github.com/kushagra2503/ai_assistant_pkg) for known issues
- Submit a new issue with details about your problem

## Uninstallation

To remove TermCrawl AI Assistant from your system:

```bash
pip uninstall ai-assistant
```

---

## Advanced: Using as a Library

You can also use TermCrawl AI Assistant as a library in your Python code:

```python
import asyncio
from ai_assistant import Assistant

async def main():
    # Initialize the assistant
    assistant = Assistant(
        model_choice="Gemini",  # or "OpenAI"
        api_key=None,  # Will use environment variable
        role="General"
    )
    
    # Get a response
    response = await assistant.answer_async("What is artificial intelligence?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

For more examples and advanced usage, refer to the [README.md](README.md) file.
