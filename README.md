# TermCrawl AI Assistant

A versatile AI assistant package with multi-model support and various integrations.

## Features

- Multi-model support (Google Gemini and OpenAI)
- Conversation history management
- Desktop screenshot capability
- Speech recognition
- Google Calendar integration
- Role-based system prompts for different use cases

## Quick Installation

You can install the package directly from GitHub:

```bash
pip install git+https://github.com/kushagra2503/ai_assistant_pkg.git
```

For detailed installation instructions, see the [Installation Guide](INSTALLATION.md).

## Usage

### As a Command-Line Application

After installation, you can run TermCrawl AI Assistant directly from the command line:

```bash
ai-assistant
```

### As a Library in Your Code

```python
import asyncio
from ai_assistant import Assistant, ROLE_PROMPTS

# Initialize the AI Assistant
assistant = Assistant(
    model_choice="Gemini",  # or "OpenAI"
    api_key="your-api-key",  # Optional, will use environment variable if not provided
    role="Coding Assistant"  # Optional, defaults to "General"
)

# Define an async function to get responses
async def get_response(prompt):
    response = await assistant.answer_async(prompt)
    print(f"AI Response: {response}")

# Run the async function
asyncio.run(get_response("Write a Python function to calculate the Fibonacci sequence"))
```

### Using Google Calendar Integration

```python
import asyncio
from ai_assistant import GoogleCalendarIntegration

async def manage_calendar():
    calendar = GoogleCalendarIntegration()
    
    # List upcoming events
    events = await calendar.list_upcoming_events(max_results=5)
    print(events)
    
    # Add a new event
    result = await calendar.add_event(
        summary="Team Meeting",
        start_time="tomorrow at 10am",
        end_time="tomorrow at 11am",
        description="Weekly team sync",
        location="Conference Room A"
    )
    print(result)

asyncio.run(manage_calendar())
```

## Environment Variables

The package looks for the following environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `OPENAI_API_KEY`: Your OpenAI API key

You can set these in a `.env` file in your project directory.

## Requirements

- Python 3.7+
- Required packages (automatically installed):
  - google-generativeai
  - openai
  - SpeechRecognition
  - pillow
  - opencv-python
  - python-dotenv
  - google-api-python-client
  - google-auth-httplib2
  - google-auth-oauthlib
  - python-dateutil
  - gtts

## License

MIT
