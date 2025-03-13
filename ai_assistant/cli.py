"""
Command-line interface for the AI Assistant.
"""

import asyncio
import logging
from .core.app import AIAssistantApp

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("assistant.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point for the AI Assistant CLI."""
    setup_logging()
    app = AIAssistantApp()
    asyncio.run(app.run())

if __name__ == "__main__":
    main()
