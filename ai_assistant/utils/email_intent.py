import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ai_assistant")

class EmailIntentParser:
    """
    Parser for natural language email commands.
    """
    
    def __init__(self):
        """Initialize the Email Intent Parser."""
        logger.info("Initializing Email Intent Parser")
        
        # Define patterns as individual variables for clarity
        self.setup_email_pattern = re.compile(r'(?:set\s*up|configure|add)\s+(?:my\s+)?email', re.IGNORECASE)
        self.send_email_pattern = re.compile(r'(?:send|write|compose)\s+(?:an\s+)?(?:email|mail|message)\s+(?:to\s+)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE)
        self.list_emails_pattern = re.compile(r'(?:list|show|check|get|view)\s+(?:my\s+)?(?:emails|mail|inbox|messages)', re.IGNORECASE)
        self.read_email_pattern = re.compile(r'(?:read|open|view|show)\s+email\s+(?:number\s+)?(\d+)', re.IGNORECASE)
        self.reply_to_email_pattern = re.compile(r'(?:reply|respond)\s+(?:to\s+)?email\s+(?:number\s+)?(\d+)', re.IGNORECASE)
        self.forward_email_pattern = re.compile(r'(?:forward)\s+email\s+(?:number\s+)?(\d+)(?:\s+to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}))?', re.IGNORECASE)
        self.delete_email_pattern = re.compile(r'(?:delete|remove)\s+email\s+(?:number\s+)?(\d+)', re.IGNORECASE)
        self.ai_compose_email_pattern = re.compile(r'(?:ai|assistant|help me)\s+(?:write|compose|draft|create)\s+(?:an\s+)?(?:email|mail|message)(?:\s+(?:to\s+)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}))?', re.IGNORECASE)
        
        # Store patterns in a dictionary for easy reference
        self.patterns = {
            'setup_email': self.setup_email_pattern,
            'send_email': self.send_email_pattern,
            'list_emails': self.list_emails_pattern,
            'read_email': self.read_email_pattern,
            'reply_to_email': self.reply_to_email_pattern,
            'forward_email': self.forward_email_pattern,
            'delete_email': self.delete_email_pattern,
            'ai_compose_email': self.ai_compose_email_pattern
        }
    
    def parse_intent(self, text):
        """
        Parse the user input to determine email-related intent.
        
        Args:
            text (str): User input text
            
        Returns:
            dict or None: Intent information if detected, None otherwise
        """
        if not text:
            return None
        
        # Normalize input for better matching
        normalized_input = text.lower().strip()
        
        # Check for AI compose email FIRST (before regular send email)
        # This is important because "ai write email" could also match the send_email pattern
        ai_compose_pattern = re.compile(r'(?:ai|assistant|help me)\s+(?:write|compose|draft|create)\s+(?:an\s+)?(?:email|mail|message)(?:\s+(?:to\s+)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}))?', re.IGNORECASE)
        match = ai_compose_pattern.search(normalized_input)
        if match:
            to_address = match.group(1) if match.groups() else None
            return {
                'operation': 'ai_compose_email',
                'to_address': to_address
            }
        
        # Check for setup email
        setup_pattern = re.compile(r'(?:set\s*up|configure|add)\s+(?:my\s+)?email', re.IGNORECASE)
        match = setup_pattern.search(normalized_input)
        if match:
            return {
                'operation': 'setup_email'
            }
        
        # Check for send email
        send_pattern = re.compile(r'(?:send|write|compose)\s+(?:an\s+)?(?:email|mail|message)\s+(?:to\s+)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE)
        match = send_pattern.search(normalized_input)
        if match:
            to_address = match.group(1) if match.groups() else None
            return {
                'operation': 'send_email',
                'to_address': to_address
            }
        
        # Check for list emails
        list_pattern = re.compile(r'(?:list|show|check|get|view)\s+(?:my\s+)?(?:emails|mail|inbox|messages)', re.IGNORECASE)
        match = list_pattern.search(normalized_input)
        if match:
            from_address = None
            from_match = re.search(r'from\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', normalized_input)
            if from_match:
                from_address = from_match.group(1)
            
            return {
                'operation': 'list_emails',
                'from_address': from_address
            }
        
        # Check for read email
        read_pattern = re.compile(r'(?:read|open|view|show)\s+email\s+(?:number\s+)?(\d+)', re.IGNORECASE)
        match = read_pattern.search(normalized_input)
        if match:
            email_id = match.group(1) if match.groups() else None
            return {
                'operation': 'read_email',
                'email_id': email_id
            }
        
        # Check for reply to email
        reply_pattern = re.compile(r'(?:reply|respond)\s+(?:to\s+)?email\s+(?:number\s+)?(\d+)', re.IGNORECASE)
        match = reply_pattern.search(normalized_input)
        if match:
            email_id = match.group(1) if match.groups() else None
            return {
                'operation': 'reply_to_email',
                'email_id': email_id
            }
        
        # Check for forward email
        forward_pattern = re.compile(r'(?:forward)\s+email\s+(?:number\s+)?(\d+)(?:\s+to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}))?', re.IGNORECASE)
        match = forward_pattern.search(normalized_input)
        if match:
            email_id = match.group(1) if match.groups() else None
            to_address = match.group(2) if len(match.groups()) > 1 else None
            return {
                'operation': 'forward_email',
                'email_id': email_id,
                'to_address': to_address
            }
        
        # Check for delete email
        delete_pattern = re.compile(r'(?:delete|remove)\s+email\s+(?:number\s+)?(\d+)', re.IGNORECASE)
        match = delete_pattern.search(normalized_input)
        if match:
            email_id = match.group(1) if match.groups() else None
            return {
                'operation': 'delete_email',
                'email_id': email_id
            }
        
        # Generic email-related query
        if any(word in normalized_input for word in ['email', 'mail', 'inbox', 'message']):
            return {
                'operation': 'generic_email'
            }
        
        return None 