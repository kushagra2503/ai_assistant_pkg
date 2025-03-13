# AI Assistant

A versatile AI assistant with multi-model support, speech recognition, and various productivity features.

## Features

- **Multi-Model Support**: Use Google's Gemini or OpenAI's GPT models
- **Speech Recognition**: Speak to your assistant
- **Desktop Screenshot Analysis**: Share your screen for visual context
- **Google Calendar Integration**: Manage your calendar events
- **Task Management**: Keep track of your to-do list
- **Role-Based Prompts**: Specialized assistance for different needs
- **Conversation History**: Maintains context between interactions

## Installation

```bash
pip install ai-assistant
```

Or install from source:

```bash
git clone https://github.com/yourusername/ai_assistant.git
cd ai_assistant
pip install -e .
```

## Usage

```bash
ai-assistant
```

### Main Menu

- **S - Speak**: Use speech recognition to talk to the assistant
- **T - Type**: Type your questions or commands
- **C - Configure**: Change settings like AI model and role
- **Q - Quit**: Exit the assistant

### Special Commands

- **/help**: Show available commands
- **/calendar list**: List upcoming events
- **/calendar add "Event Title" "Start Time"**: Add a new event

## Configuration

The assistant supports different AI models and roles:

### AI Models
- Gemini (Google AI)
- OpenAI (GPT-4, GPT-3.5)

### Assistant Roles
- General
- Tech Support
- Coding Assistant
- Business Consultant
- Research Assistant
- Creative Writer
- Personal Coach
- Data Analyst
- Sales Agent

## Requirements

- Python 3.7+
- API keys for the AI models you want to use
- Google account for Calendar integration

## License

MIT
