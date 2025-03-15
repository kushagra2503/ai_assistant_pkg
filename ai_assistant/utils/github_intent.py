"""
GitHub intent parser for natural language processing.
"""

import re
import logging

logger = logging.getLogger("ai_assistant")

class GitHubIntentParser:
    """
    Parse natural language requests for GitHub operations.
    
    This class identifies GitHub-related intents from user messages
    and extracts relevant parameters for executing GitHub operations.
    """
    
    def __init__(self):
        """Initialize the GitHub intent parser."""
        # Define patterns for different GitHub operations
        self.patterns = {
            "authenticate": [
                r"(?:connect|authenticate|login|sign in)(?:\s+to)?\s+(?:with\s+)?github",
                r"set up github",
                r"github authentication",
                r"github token",
                r"github credentials"
            ],
            "list_repos": [
                r"(?:list|show|get|display)(?:\s+my)?\s+(?:github\s+)?repos(?:itories)?",
                r"what(?:\s+are)?\s+my\s+github\s+repos(?:itories)?",
                r"show me my github projects",
                r"list your github repos(?:itories)?",
                r"show your github repos(?:itories)?",
                r"get your github repos(?:itories)?"
            ],
            "create_repo": [
                r"create(?:\s+a)?(?:\s+new)?\s+(?:github\s+)?repo(?:sitory)?(?:\s+called|named)?\s+[\"']?([^\"']+)[\"']?",
                r"make(?:\s+a)?(?:\s+new)?\s+(?:github\s+)?repo(?:sitory)?(?:\s+called|named)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:create|make)(?:\s+a)?(?:\s+new)?\s+(?:github\s+)?repo(?:sitory)?(?:\s+name(?:d)?\s+it(?:\s+as)?)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:hey|please)?\s+(?:create|make)(?:\s+a)?(?:\s+new)?\s+(?:github\s+)?repo(?:sitory)?(?:\s+name(?:d)?\s+it(?:\s+as)?)?\s+[\"']?([^\"']+)[\"']?"
            ],
            "list_issues": [
                r"(?:list|show|get|display)(?:\s+the)?\s+(?:github\s+)?issues(?:\s+for|from|in)?\s+(?:repo(?:sitory)?\s+)?[\"']?([^\"']+)[\"']?",
                r"what(?:\s+are)?\s+the\s+(?:github\s+)?issues(?:\s+for|from|in)?\s+(?:repo(?:sitory)?\s+)?[\"']?([^\"']+)[\"']?"
            ],
            "create_issue": [
                r"create(?:\s+a)?(?:\s+new)?\s+(?:github\s+)?issue(?:\s+in|for)?\s+(?:repo(?:sitory)?\s+)?[\"']?([^\"']+)[\"']?(?:\s+with|titled|called)?\s+[\"']?([^\"']+)[\"']?",
                r"add(?:\s+a)?(?:\s+new)?\s+(?:github\s+)?issue(?:\s+in|for)?\s+(?:repo(?:sitory)?\s+)?[\"']?([^\"']+)[\"']?(?:\s+with|titled|called)?\s+[\"']?([^\"']+)[\"']?"
            ],
            "create_file": [
                r"create(?:\s+a)?(?:\s+new)?\s+(?:github\s+)?file(?:\s+in|for)?\s+(?:repo(?:sitory)?\s+)?[\"']?([^\"']+)[\"']?(?:\s+at|called|named|path)?\s+[\"']?([^\"']+)[\"']?",
                r"add(?:\s+a)?(?:\s+new)?\s+(?:github\s+)?file(?:\s+in|for)?\s+(?:repo(?:sitory)?\s+)?[\"']?([^\"']+)[\"']?(?:\s+at|called|named|path)?\s+[\"']?([^\"']+)[\"']?"
            ],
            "delete_repo": [
                r"(?:delete|remove)(?:\s+the)?\s+(?:github\s+)?repo(?:sitory)?\s+(?:called|named)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:delete|remove)(?:\s+the)?\s+(?:github\s+)?repo(?:sitory)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:hey|please)?\s+(?:delete|remove)(?:\s+the)?\s+(?:github\s+)?repo(?:sitory)?\s+(?:called|named)?\s+[\"']?([^\"']+)[\"']?",
                r"(?:hey|please)?\s+(?:delete|remove)(?:\s+the)?\s+(?:github\s+)?repo(?:sitory)?\s+[\"']?([^\"']+)[\"']?"
            ]
        }
    
    def parse_intent(self, text):
        """
        Parse GitHub intent from natural language text.
        
        Args:
            text (str): User's natural language request
            
        Returns:
            dict: Intent information with operation and parameters, or None if no intent found
        """
        text = text.lower()
        
        # Check for GitHub-related content first
        if "github" not in text and "repo" not in text:
            return None
            
        # Debug: Log the text being parsed
        logger.info(f"Parsing GitHub intent from: '{text}'")
            
        # Try to match patterns for different operations
        for operation, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    logger.info(f"Matched GitHub intent: {operation} with pattern: {pattern}")
                    
                    # Extract parameters based on the operation
                    params = {}
                    
                    if operation == "create_repo":
                        params["name"] = match.group(1).strip()
                        
                        # Try to extract description
                        desc_match = re.search(r"description(?:\s+is|:)?\s+[\"']?([^\"']+)[\"']?", text, re.IGNORECASE)
                        if desc_match:
                            params["description"] = desc_match.group(1).strip()
                            
                        # Check if private
                        params["private"] = "private" in text
                        
                    elif operation == "list_issues":
                        params["repo"] = match.group(1).strip()
                        
                        # Try to extract state
                        if "closed" in text:
                            params["state"] = "closed"
                        elif "all" in text:
                            params["state"] = "all"
                        else:
                            params["state"] = "open"
                            
                    elif operation == "create_issue":
                        params["repo"] = match.group(1).strip()
                        params["title"] = match.group(2).strip() if len(match.groups()) > 1 else "New Issue"
                        
                        # Try to extract body
                        body_match = re.search(r"(?:with\s+description|body|content)(?:\s+is|:)?\s+[\"']?([^\"']+)[\"']?", text, re.IGNORECASE)
                        if body_match:
                            params["body"] = body_match.group(1).strip()
                            
                        # Try to extract labels
                        labels_match = re.search(r"(?:with\s+labels|labels|tags)(?:\s+are|:)?\s+[\"']?([^\"']+)[\"']?", text, re.IGNORECASE)
                        if labels_match:
                            labels_text = labels_match.group(1).strip()
                            params["labels"] = [label.strip() for label in re.split(r',|\s+and\s+', labels_text)]
                            
                    elif operation == "create_file":
                        params["repo"] = match.group(1).strip()
                        params["path"] = match.group(2).strip() if len(match.groups()) > 1 else "README.md"
                        
                        # Try to extract content
                        content_match = re.search(r"(?:with\s+content|content|containing)(?:\s+is|:)?\s+[\"']?([^\"']+)[\"']?", text, re.IGNORECASE)
                        if content_match:
                            params["content"] = content_match.group(1).strip()
                        else:
                            params["content"] = "# New File\n\nCreated via AI Assistant"
                            
                        # Try to extract commit message
                        message_match = re.search(r"(?:with\s+message|commit\s+message|message)(?:\s+is|:)?\s+[\"']?([^\"']+)[\"']?", text, re.IGNORECASE)
                        if message_match:
                            params["message"] = message_match.group(1).strip()
                        else:
                            params["message"] = "Add new file via AI Assistant"
                    
                    elif operation == "delete_repo":
                        params["repo"] = match.group(1).strip()
                    
                    return {
                        "operation": operation,
                        "params": params
                    }
                    
        # If we get here, we found GitHub-related content but no specific intent
        return {
            "operation": "general_github",
            "params": {}
        } 