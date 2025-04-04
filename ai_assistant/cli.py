#!/usr/bin/env python
"""
Command-line interface for QuackQuery.
"""

import asyncio
import logging
import os
import sys
import traceback
from .core.app import AIAssistantApp
from .utils.tracking import track_installation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("quackquery.log"),  # Change from "assistant.log" to "quackquery.log"
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ai_assistant")  # Make sure this matches with the logger in other files

def main():
    """Main entry point for the QuackQuery CLI."""
    try:
        # Track installation (runs in background thread)
        track_installation()
        
        print("Initializing QuackQuery AI Assistant...")
        app = AIAssistantApp()
        print("Starting application...")
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\nExiting QuackQuery. Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"\nError starting QuackQuery: {str(e)}")
        print("Check quackquery.log for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
