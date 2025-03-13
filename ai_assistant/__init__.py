"""
AI Assistant Package
===================

A versatile AI assistant package with multi-model support and various integrations.
"""

__version__ = '0.1.0'

from .core.assistant import Assistant
from .core.conversation import ConversationHistory, PersistentConversationHistory
from .utils.screenshot import DesktopScreenshot
from .utils.speech import listen_for_speech
from .core.app import AIAssistantApp
from .integrations.calendar import GoogleCalendarIntegration

# Role-based system prompts
from .core.prompts import ROLE_PROMPTS

__all__ = [
    'Assistant',
    'ConversationHistory',
    'PersistentConversationHistory',
    'DesktopScreenshot',
    'listen_for_speech',
    'AIAssistantApp',
    'GoogleCalendarIntegration',
    'ROLE_PROMPTS'
]
