"""
Conversation history management for the AI Assistant.
"""

import json
import os
import logging

logger = logging.getLogger("ai_assistant")

class ConversationHistory:
    """
    Manages conversation history between user and AI assistant.
    
    Attributes:
        history (list): List of conversation exchanges
        max_history (int): Maximum number of exchanges to store
    """
    
    def __init__(self, max_history=10):
        """
        Initialize conversation history.
        
        Args:
            max_history (int): Maximum number of exchanges to store
        """
        self.history = []
        self.max_history = max_history
    
    def add(self, user_input, ai_response):
        """
        Add a new exchange to the conversation history.
        
        Args:
            user_input (str): User's input
            ai_response (str): AI's response
        """
        self.history.append({"user": user_input, "assistant": ai_response})
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_context(self):
        """
        Get a formatted string of recent conversation history.
        
        Returns:
            str: Formatted conversation history
        """
        return "\n".join([f"User: {item['user']}\nAssistant: {item['assistant']}" for item in self.history[-3:]])


class PersistentConversationHistory(ConversationHistory):
    """
    Enhanced conversation history with persistence to disk.
    
    Attributes:
        history_file (str): Path to the file where history is stored
    """
    
    def __init__(self, max_history=10, history_file="conversation_history.json"):
        """
        Initialize persistent conversation history.
        
        Args:
            max_history (int): Maximum number of exchanges to store
            history_file (str): Path to the file where history is stored
        """
        super().__init__(max_history)
        self.history_file = history_file
        self.load_history()
        
    def load_history(self):
        """Load conversation history from disk."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    saved_history = json.load(f)
                    if isinstance(saved_history, list):
                        self.history = saved_history[-self.max_history:]
                        logger.info(f"Loaded {len(self.history)} conversation items from history file")
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            
    def save_history(self):
        """Save conversation history to disk."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
            
    def add(self, user_input, ai_response):
        """
        Add a new exchange to the conversation history and save to disk.
        
        Args:
            user_input (str): User's input
            ai_response (str): AI's response
        """
        super().add(user_input, ai_response)
        self.save_history()
        
    def clear(self):
        """Clear conversation history and save the empty history to disk."""
        self.history = []
        self.save_history()
        logger.info("Conversation history cleared")
