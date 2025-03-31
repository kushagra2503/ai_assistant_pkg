"""
Application intent parser for natural language processing.
"""

import re
import logging

logger = logging.getLogger("ai_assistant")

class AppIntentParser:
    """
    Parse natural language requests for application operations.
    
    This class identifies app-related intents from user messages
    and extracts relevant parameters for executing app operations.
    """
    
    def __init__(self):
        """Initialize the application intent parser."""
        # Define patterns for different app operations
        self.patterns = {
            "launch_app": [
                r"^(?:open|launch|start|run)\s+([a-zA-Z0-9\s]+)$",  # Simple "open app" pattern
                r"(?:open|launch|start|run)(?:\s+the)?\s+(?:app|application)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:open|launch|start|run)(?:\s+the)?\s+[\"']?([^\"']+)[\"']?(?:\s+app|application)?",
                r"(?:can\s+you)?\s+(?:open|launch|start|run)(?:\s+the)?\s+(?:app|application)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:can\s+you)?\s+(?:open|launch|start|run)(?:\s+the)?\s+[\"']?([^\"']+)[\"']?(?:\s+app|application)?",
                r"(?:i\s+want\s+to)?\s+(?:open|launch|start|run)(?:\s+the)?\s+(?:app|application)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:i\s+want\s+to)?\s+(?:open|launch|start|run)(?:\s+the)?\s+[\"']?([^\"']+)[\"']?(?:\s+app|application)?",
                r"(?:please)?\s+(?:open|launch|start|run)(?:\s+the)?\s+(?:app|application)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:please)?\s+(?:open|launch|start|run)(?:\s+the)?\s+[\"']?([^\"']+)[\"']?(?:\s+app|application)?"
            ],
            "list_apps": [
                r"(?:list|show|get|display)(?:\s+all)?\s+(?:installed)?\s+(?:apps|applications)",
                r"what(?:\s+are)?\s+(?:the)?\s+(?:installed)?\s+(?:apps|applications)(?:\s+on\s+my\s+(?:computer|system|device))?",
                r"show\s+me(?:\s+the)?\s+(?:installed)?\s+(?:apps|applications)(?:\s+on\s+my\s+(?:computer|system|device))?"
            ]
        }
    
    def parse_intent(self, text):
        """
        Parse application operation intent from natural language text.
        
        Args:
            text (str): User's natural language request
            
        Returns:
            dict: Intent information with operation and parameters, or None if no intent found
        """
        text = text.lower().strip()
        
        # Debug: Log the text being parsed
        logger.info(f"Parsing app intent from: '{text}'")
        
        # Special case for simple "open X" commands
        simple_open_match = re.match(r"^(?:open|launch|start|run)\s+([a-zA-Z0-9\s\.]+)$", text, re.IGNORECASE)
        if simple_open_match:
            app_name = simple_open_match.group(1).strip()
            logger.info(f"Matched simple app launch: {app_name}")
            return {
                "operation": "launch_app",
                "params": {"app_name": app_name}
            }
            
        # Check for app-related content
        app_keywords = ["app", "application", "open", "launch", "start", "run", "program"]
        
        # Skip if it's a WhatsApp related command to prevent conflicts with WhatsApp intent parser
        if "whatsapp" in text or "whats app" in text:
            return None
            
        # Check for app keywords that are standalone words, not part of other words
        has_app_keyword = False
        for keyword in app_keywords:
            # Look for the keyword as a whole word, not part of another word
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                has_app_keyword = True
                break
        
        if not has_app_keyword:
            return None
            
        # Try to match patterns for different operations
        for operation, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    logger.info(f"Matched app intent: {operation} with pattern: {pattern}")
                    
                    # Extract parameters based on the operation
                    params = {}
                    
                    if operation == "launch_app":
                        app_name = match.group(1).strip()
                        
                        # Clean up app name
                        app_name = re.sub(r'(?:the\s+)?(?:app|application)$', '', app_name).strip()
                        
                        params["app_name"] = app_name
                    
                    return {
                        "operation": operation,
                        "params": params
                    }
                    
        # If we get here, we found app-related content but no specific intent
        return {
            "operation": "general_app",
            "params": {}
        } 