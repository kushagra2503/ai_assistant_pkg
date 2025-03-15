"""
File operation intent parser for natural language processing.
"""

import re
import logging
import os

# Define the logger
logger = logging.getLogger("ai_assistant")

class FileIntentParser:
    """
    Parse natural language requests for file operations.
    
    This class identifies file-related intents from user messages
    and extracts relevant parameters for executing file operations.
    """
    
    def __init__(self):
        """Initialize the file intent parser."""
        # Define patterns for different file operations
        self.patterns = {
            "list_directory": [
                r"(?:list|show|get|display)(?:\s+the)?\s+(?:files|contents|directory)(?:\s+in|of)?\s+(?:folder|directory)?\s*[\"']?([^\"']*)[\"']?",
                r"(?:list|show|get|display)(?:\s+the)?\s+(?:files|contents|directory)(?:\s+in|of)?\s+[\"']?([^\"']+)[\"']?",
                r"what(?:'s|\s+is)(?:\s+in)?\s+(?:the)?\s+(?:folder|directory)\s+[\"']?([^\"']+)[\"']?",
                r"show\s+me\s+(?:what(?:'s|\s+is)(?:\s+in)?)?\s+(?:the)?\s+(?:folder|directory)\s+[\"']?([^\"']+)[\"']?",
                r"(?:list|show|get|display)(?:\s+the)?\s+(?:current|this)(?:\s+folder|directory)?(?:\s+contents)?",
                r"what(?:'s|\s+is)(?:\s+in)?\s+(?:the)?\s+current(?:\s+folder|directory)?",
                r"show\s+me\s+(?:what(?:'s|\s+is)(?:\s+in)?)?\s+(?:the)?\s+current(?:\s+folder|directory)?"
            ],
            "create_directory": [
                r"(?:create|make|add)(?:\s+a)?\s+(?:new)?\s+(?:folder|directory)(?:\s+called|named)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:create|make|add)(?:\s+a)?\s+(?:new)?\s+(?:folder|directory)\s+[\"']?([^\"']+)[\"']?"
            ],
            "delete_item": [
                r"(?:delete|remove|trash)(?:\s+the)?\s+(?:file|folder|directory)\s+[\"']?([^\"']+)[\"']?",
                r"(?:delete|remove|trash)(?:\s+the)?\s+[\"']?([^\"']+)[\"']?"
            ],
            "move_item": [
                r"(?:move|relocate)(?:\s+the)?\s+(?:file|folder|directory)?\s+[\"']?([^\"']+)[\"']?\s+to\s+[\"']?([^\"']+)[\"']?",
                r"(?:move|relocate)(?:\s+the)?\s+[\"']?([^\"']+)[\"']?\s+to\s+[\"']?([^\"']+)[\"']?"
            ],
            "copy_item": [
                r"(?:copy|duplicate)(?:\s+the)?\s+(?:file|folder|directory)?\s+[\"']?([^\"']+)[\"']?\s+to\s+[\"']?([^\"']+)[\"']?",
                r"(?:copy|duplicate)(?:\s+the)?\s+[\"']?([^\"']+)[\"']?\s+to\s+[\"']?([^\"']+)[\"']?"
            ],
            "rename_item": [
                r"(?:rename|change\s+the\s+name\s+of)(?:\s+the)?\s+(?:file|folder|directory)?\s+[\"']?([^\"']+)[\"']?\s+to\s+[\"']?([^\"']+)[\"']?",
                r"(?:rename|change\s+the\s+name\s+of)(?:\s+the)?\s+[\"']?([^\"']+)[\"']?\s+to\s+[\"']?([^\"']+)[\"']?"
            ],
            "create_file": [
                r"(?:create|make|add)(?:\s+a)?\s+(?:new)?\s+file(?:\s+called|named)?\s+[\"']?([^\"']+)[\"']?(?:\s+with\s+content\s+[\"']?([^\"']+)[\"']?)?",
                r"(?:create|make|add)(?:\s+a)?\s+(?:new)?\s+file\s+[\"']?([^\"']+)[\"']?(?:\s+with\s+content\s+[\"']?([^\"']+)[\"']?)?"
            ],
            "read_file": [
                r"(?:read|open|show|display|get)(?:\s+the)?\s+(?:contents\s+of)?\s+(?:file)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:what(?:'s|\s+is)(?:\s+in)?)(?:\s+the)?\s+file\s+[\"']?([^\"']+)[\"']?",
                r"show\s+me\s+(?:what(?:'s|\s+is)(?:\s+in)?)?\s+(?:the)?\s+file\s+[\"']?([^\"']+)[\"']?"
            ],
            "search_files": [
                r"(?:search|find|look\s+for)(?:\s+files)?\s+(?:with\s+name)?\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+[\"']?([^\"']+)[\"']?)?(?:\s+containing\s+[\"']?([^\"']+)[\"']?)?",
                r"(?:search|find|look\s+for)(?:\s+files)?\s+containing\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+[\"']?([^\"']+)[\"']?)?"
            ],
            "change_directory": [
                r"(?:change|switch|go\s+to|navigate\s+to)(?:\s+the)?\s+(?:directory|folder)\s+[\"']?([^\"']+)[\"']?",
                r"(?:cd|chdir)\s+[\"']?([^\"']+)[\"']?"
            ],
            "zip_items": [
                r"(?:zip|compress)(?:\s+the)?\s+(?:file|folder|directory)?\s+[\"']?([^\"']+)[\"']?(?:\s+to\s+[\"']?([^\"']+)[\"']?)?",
                r"(?:create\s+a\s+zip|make\s+a\s+zip)(?:\s+of)?\s+[\"']?([^\"']+)[\"']?(?:\s+(?:named|called)\s+[\"']?([^\"']+)[\"']?)?"
            ],
            "unzip_file": [
                r"(?:unzip|extract|decompress)(?:\s+the)?\s+(?:file)?\s+[\"']?([^\"']+)[\"']?(?:\s+to\s+[\"']?([^\"']+)[\"']?)?",
                r"(?:unzip|extract|decompress)(?:\s+the)?\s+contents\s+of\s+[\"']?([^\"']+)[\"']?(?:\s+to\s+[\"']?([^\"']+)[\"']?)?"
            ]
        }
    
    def parse_intent(self, text):
        """
        Parse file operation intent from natural language text.
        
        Args:
            text (str): User's natural language request
            
        Returns:
            dict: Intent information with operation and parameters, or None if no intent found
        """
        text = text.lower()
        
        # Check for file-related content first
        file_keywords = ["file", "folder", "directory", "delete", "move", "copy", "rename", 
                         "create", "list", "search", "find", "zip", "unzip", "extract"]
                         
        has_file_keyword = any(keyword in text for keyword in file_keywords)
        
        if not has_file_keyword:
            return None
            
        # Debug: Log the text being parsed
        logger.info(f"Parsing file intent from: '{text}'")
            
        # Try to match patterns for different operations
        for operation, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    logger.info(f"Matched file intent: {operation} with pattern: {pattern}")
                    
                    # Extract parameters based on the operation
                    params = {}
                    
                    if operation == "list_directory":
                        # Check if it's for current directory
                        if "current" in match.group(0) or "this" in match.group(0):
                            params["path"] = None
                        else:
                            path = match.group(1).strip() if match.groups() else None
                            params["path"] = path if path else None
                    
                    elif operation == "create_directory":
                        params["path"] = match.group(1).strip()
                    
                    elif operation == "delete_item":
                        params["path"] = match.group(1).strip()
                        # Check if it should use trash
                        params["use_trash"] = "permanently" not in text
                    
                    elif operation == "move_item":
                        params["source"] = match.group(1).strip()
                        params["destination"] = match.group(2).strip()
                    
                    elif operation == "copy_item":
                        params["source"] = match.group(1).strip()
                        params["destination"] = match.group(2).strip()
                    
                    elif operation == "rename_item":
                        params["path"] = match.group(1).strip()
                        params["new_name"] = match.group(2).strip()
                    
                    elif operation == "create_file":
                        params["path"] = match.group(1).strip()
                        params["content"] = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else ""
                    
                    elif operation == "read_file":
                        params["path"] = match.group(1).strip()
                    
                    elif operation == "search_files":
                        if "containing" in match.group(0) and match.group(0).index("containing") < match.group(0).index(match.group(1)):
                            # This is a content search pattern
                            params["content_search"] = match.group(1).strip()
                            params["path"] = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                            params["pattern"] = "*"  # Default to all files
                        else:
                            # This is a filename pattern search
                            params["pattern"] = match.group(1).strip()
                            params["path"] = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                            params["content_search"] = match.group(3).strip() if len(match.groups()) > 2 and match.group(3) else None
                    
                    elif operation == "change_directory":
                        params["path"] = match.group(1).strip()
                    
                    elif operation == "zip_items":
                        items_text = match.group(1).strip()
                        # Split by commas or "and" to get multiple items
                        items = re.split(r',\s*|\s+and\s+', items_text)
                        params["items"] = items
                        
                        output_path = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else f"{items[0]}.zip"
                        params["output_path"] = output_path
                    
                    elif operation == "unzip_file":
                        params["zip_path"] = match.group(1).strip()
                        params["extract_path"] = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                    
                    return {
                        "operation": operation,
                        "params": params
                    }
                    
        # If we get here, we found file-related content but no specific intent
        return {
            "operation": "general_file",
            "params": {}
        } 