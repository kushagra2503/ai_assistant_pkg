#!/usr/bin/env python
"""
Command-line interface for QuackQuery.
"""

import asyncio
import logging
import os
import sys
from .core.app import AIAssistantApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("quackquery.log"),  # Change from "assistant.log" to "quackquery.log"
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("quackquery")  # Change from "ai_assistant" to "quackquery"

def main():
    """Main entry point for the QuackQuery CLI."""
    app = AIAssistantApp()
    asyncio.run(app.run())

if __name__ == "__main__":
    main()
