# QuackQuery

QuackQuery is a versatile AI assistant with multiple integrations including GitHub automation, file management, and application launching capabilities.

## Features

- **Multi-model AI Support**: Seamlessly switch between Google Gemini and OpenAI models
- **Natural Language Commands**: Control your computer with simple English instructions
- **GitHub Integration**: Create repositories, manage issues, and more with voice or text
- **File Management**: Navigate, create, move, and search files using natural language
- **Application Automation**: Launch applications with simple voice commands
- **OCR Capabilities**: Extract text from images and screenshots
- **Voice Recognition**: Interact with the assistant using speech
- **Desktop Screenshots**: Capture and analyze your screen
- **Role-based Personalities**: Switch between different assistant roles for specialized help
- **Email Integration**: Send, read, reply to, and manage emails with natural language commands

## Installation

### From PyPI (Recommended)

```bash
pip install QuackQuery
```

### From Source

```bash
git clone https://github.com/kushagra2503/
cd ai_assistant
pip install -e .
```

## Quick Start

After installation, run QuackQuery from your terminal:

```bash
quackquery
```

On first run, you'll be prompted to configure your API keys.

## API Keys

QuackQuery requires at least one of the following API keys:

- **Google Gemini API key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenAI API key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

You can set these as environment variables:
```bash
# For Windows
set GEMINI_API_KEY=your_gemini_api_key
set OPENAI_API_KEY=your_openai_api_key

# For Linux/macOS
export GEMINI_API_KEY=your_gemini_api_key
export OPENAI_API_KEY=your_openai_api_key
```

Or create a `.env` file in your working directory:

## Usage

```bash
quackquery
```

## Usage Examples

### Email Management
