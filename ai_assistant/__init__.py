"""
QuackQuery Package
=================

A versatile AI assistant package with multi-model support and various integrations.
"""

__version__ = '0.4.1'

from .core.assistant import Assistant
from .core.conversation import ConversationHistory, PersistentConversationHistory
from .utils.screenshot import DesktopScreenshot
from .utils.speech import listen_for_speech
from .utils.ocr import OCRProcessor
from .core.app import AIAssistantApp
from .integrations.github import GitHubIntegration
from .utils.github_intent import GitHubIntentParser
from .integrations.file_explorer import FileExplorer
from .utils.file_intent import FileIntentParser
from .integrations.app_launcher import AppLauncher
from .utils.app_intent import AppIntentParser

# Role-based system prompts
from .core.prompts import ROLE_PROMPTS

__all__ = [
    'Assistant',
    'ConversationHistory',
    'PersistentConversationHistory',
    'DesktopScreenshot',
    'listen_for_speech',
    'OCRProcessor',
    'AIAssistantApp',
    'GitHubIntegration',
    'GitHubIntentParser',
    'FileExplorer',
    'FileIntentParser',
    'AppLauncher',
    'AppIntentParser',
    'ROLE_PROMPTS'
]
