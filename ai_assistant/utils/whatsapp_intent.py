import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ai_assistant")

class WhatsAppIntentParser:
    """
    Parser for natural language WhatsApp commands.
    """
    
    def __init__(self):
        """Initialize the WhatsApp Intent Parser."""
        logger.info("Initializing WhatsApp Intent Parser")
        
        # Define patterns for WhatsApp operations
        self.setup_whatsapp_pattern = re.compile(r'(?:set\s*up|configure|add)\s+(?:my\s+)?whatsapp', re.IGNORECASE)
        self.send_whatsapp_pattern = re.compile(r'(?:send|write|compose)\s+(?:a\s+)?(?:whatsapp|message|whatsapp message|whatsapp msg)\s+(?:to\s+)?(.+?)(?:\s+(?:saying|with message|that says)\s+(.+))?$', re.IGNORECASE)
        self.connect_whatsapp_pattern = re.compile(r'(?:connect|login|open)\s+(?:to\s+)?(?:my\s+)?whatsapp', re.IGNORECASE)
        self.disconnect_whatsapp_pattern = re.compile(r'(?:disconnect|logout|close)\s+(?:from\s+)?(?:my\s+)?whatsapp', re.IGNORECASE)
        self.list_contacts_pattern = re.compile(r'(?:list|show|get|view)\s+(?:my\s+)?(?:whatsapp\s+)?(?:contacts|recent contacts)', re.IGNORECASE)
        self.ai_compose_whatsapp_pattern = re.compile(r'(?:ai|assistant|help me)\s+(?:write|compose|draft|create)\s+(?:a\s+)?(?:whatsapp|message|whatsapp message|whatsapp msg|msg)\s+(?:to\s+)?([+]?\d+|[a-zA-Z0-9\s]+)(?:\s+(?:about|regarding|on|for).*)?', re.IGNORECASE)
        
        # Store patterns in a dictionary for easy reference
        self.patterns = {
            'setup_whatsapp': self.setup_whatsapp_pattern,
            'send_whatsapp': self.send_whatsapp_pattern,
            'connect_whatsapp': self.connect_whatsapp_pattern,
            'disconnect_whatsapp': self.disconnect_whatsapp_pattern,
            'list_contacts': self.list_contacts_pattern,
            'ai_compose_whatsapp': self.ai_compose_whatsapp_pattern
        }
    
    def parse_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the user input to determine WhatsApp-related intent.
        
        Args:
            text (str): User input text
            
        Returns:
            dict or None: Intent information if detected, None otherwise
        """
        if not text:
            return None
            
        # Special handling for AI message composition with phone numbers
        # This should be checked FIRST to prioritize it
        if re.search(r'(?:ai|assistant|help)\s+(?:write|compose|draft|create)', text.lower()):
            # Check if there's a phone number in the text
            phone_match = re.search(r'(?:to\s+)?([+=]?\d{10,})', text)
            if phone_match:
                recipient = phone_match.group(1)
                logger.info(f"Detected intent: AI compose WhatsApp message to phone number {recipient}")
                return {
                    'action': 'ai_compose_whatsapp',
                    'recipient': recipient.strip(),
                    'instruction': text
                }
        
        # Check for setup/configure WhatsApp
        if self.patterns['setup_whatsapp'].search(text):
            logger.info("Detected intent: setup WhatsApp")
            return {
                'action': 'setup_whatsapp'
            }
        
        # More explicit pattern for sending WhatsApp messages
        explicit_send_pattern = re.compile(r'(?:send|write|compose)\s+(?:a\s+)?whatsapp\s+(?:message|msg)\s+(?:to\s+)?([^\s]+)', re.IGNORECASE)
        explicit_match = explicit_send_pattern.search(text)
        if explicit_match:
            recipient = explicit_match.group(1)
            # Try to find a message content after the recipient
            message_pattern = re.compile(r'to\s+' + re.escape(recipient) + r'\s+(?:saying|with message|that says|with|:)?\s+(.+?)$', re.IGNORECASE)
            message_match = message_pattern.search(text)
            message = message_match.group(1) if message_match else ""
            
            logger.info(f"Detected explicit intent: send WhatsApp message to {recipient}")
            return {
                'action': 'send_whatsapp',
                'recipient': recipient.strip(),
                'message': message.strip() if message else ""
            }
        
        # Check for generic send WhatsApp message pattern
        send_match = self.patterns['send_whatsapp'].search(text)
        if send_match:
            recipient = send_match.group(1)
            message = send_match.group(2) if send_match.group(2) else ""
            
            # If we have a recipient but no message, extract it from the full text
            if recipient and not message:
                # Try to extract message if it's in a different format
                message_patterns = [
                    re.compile(r'(?:saying|with message|that says)\s+(.+)$', re.IGNORECASE),
                    re.compile(r'(?:with text|with content)\s+(.+)$', re.IGNORECASE),
                    re.compile(r'(?::" |:" |:\s*")(.+?)(?:"|\n|$)', re.IGNORECASE)
                ]
                
                for pattern in message_patterns:
                    message_match = pattern.search(text)
                    if message_match:
                        message = message_match.group(1)
                        break
            
            logger.info(f"Detected intent: send WhatsApp message to {recipient}")
            return {
                'action': 'send_whatsapp',
                'recipient': recipient.strip(),
                'message': message.strip() if message else ""
            }
        
        # Check for connect to WhatsApp
        if self.patterns['connect_whatsapp'].search(text):
            logger.info("Detected intent: connect to WhatsApp")
            return {
                'action': 'connect_whatsapp'
            }
        
        # Check for disconnect from WhatsApp
        if self.patterns['disconnect_whatsapp'].search(text):
            logger.info("Detected intent: disconnect from WhatsApp")
            return {
                'action': 'disconnect_whatsapp'
            }
        
        # Check for listing WhatsApp contacts
        if self.patterns['list_contacts'].search(text):
            logger.info("Detected intent: list WhatsApp contacts")
            return {
                'action': 'list_contacts'
            }
        
        # Check for AI compose WhatsApp message
        ai_compose_match = self.patterns['ai_compose_whatsapp'].search(text)
        if ai_compose_match:
            recipient = ai_compose_match.group(1) if ai_compose_match.groups() else None
            
            if recipient:
                logger.info(f"Detected intent: AI compose WhatsApp message to {recipient}")
                return {
                    'action': 'ai_compose_whatsapp',
                    'recipient': recipient.strip(),
                    'instruction': text  # Pass the full text as instruction for AI
                }
        
        # No WhatsApp intent detected
        return None
    
    def extract_ai_message_content(self, text: str, original_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract message details if the user wants AI to help compose a message.
        
        Args:
            text (str): User's instruction for the AI
            original_intent (dict): The original detected intent
            
        Returns:
            dict: Updated intent with AI-generated message
        """
        # Extract key elements like tone, purpose, etc. from user's instruction
        tone_match = re.search(r'(?:tone|style)(?:\s+of|:|\s+is|\s+should\s+be)?\s+(\w+)', text, re.IGNORECASE)
        tone = tone_match.group(1) if tone_match else "neutral"
        
        # Extract purpose if mentioned
        purpose_match = re.search(r'(?:about|regarding|on|for)\s+(.+?)(?:\.|$)', text, re.IGNORECASE)
        purpose = purpose_match.group(1).strip() if purpose_match else ""
        
        # Extract length if specified
        length_match = re.search(r'(?:length|long|short)(?:\s+of|:|\s+is|\s+should\s+be)?\s+(\w+)', text, re.IGNORECASE)
        length = length_match.group(1) if length_match else "medium"
        
        # Extract language if specified
        lang_match = re.search(r'(?:language|in)(?:\s+of|:|\s+is|\s+should\s+be)?\s+(\w+)', text, re.IGNORECASE)
        language = lang_match.group(1) if lang_match else "English"
        
        return {
            **original_intent,
            'ai_instruction': text,  # Full instruction text
            'tone': tone,
            'purpose': purpose,
            'length': length,
            'language': language,
            'is_ai_composed': True
        }
